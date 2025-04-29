from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI,WebSocket,Depends,WebSocketException,status,HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel,Field
from graph import get_graph
from fastapi import BackgroundTasks, FastAPI
from meetings import Item,add_meeting_to_db
from langchain.load.dump import dumps
from database import get_db
from models import ChatToken,User,Project,ApiKey,Meeting
from tools import ApiKeys
import json
from datetime import datetime
from typing import Optional, Dict, List
import httpx
import os

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    content: str

@app.get('/')
def index():
    return {"status":"working"}

@app.websocket("/ws/{user_id}/{thread_id}")
async def websocket_endpoint(websocket: WebSocket,user_id:str, thread_id: str,db: Session = Depends(get_db)):
    token=db.query(ChatToken).filter(ChatToken.userId==user_id,ChatToken.sessionToken==thread_id).first()
    if token is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION,reason="Token invalid")
    
    keys=ApiKeys()
    user=db.query(User).filter(User.id==user_id).first()
    if user is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION,reason="User not found")
    keys.user_id=user_id
    
    project=db.query(Project).filter(Project.id==user.projectId).first()
    if project is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION,reason="Project not found")
    keys.project_id=project.id
    
    if project.githubRepo is not None:
        keys.GITHUB_REPOSITORY=project.githubRepo
    
    apikeys=db.query(ApiKey).filter(ApiKey.projectId==project.id).all()
    
    for key in apikeys:
        try:
            if key.service=='slack':
                keys.SLACK_USER_TOKEN=key.key
            elif key.service=='jira':
                keys.JIRA_API_TOKEN=key.key
                keys.JIRA_INSTANCE_URL=key.additionalData['domain']
                keys.JIRA_USERNAME=key.additionalData['email']
            elif key.service == 'calendar':
                keys.CALENDAR_TOKEN=json.loads(key.key)
        except Exception as e:
            print(e)
    config = {"configurable": {"thread_id": thread_id,"api_keys":keys,"project":project}}
    graph=get_graph(keys)
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        async for event in graph.astream({"messages": [data]}, config=config, stream_mode="messages"):
            await websocket.send_text(dumps(event, ensure_ascii=False))
        await websocket.close()
        return


class DataModel(BaseModel):
    new_state: str
    old_state: str
    created_at: datetime
    event_type: str
    event_sub_type: Optional[str] = None

class WebhookPayload(BaseModel):
    idempotency_key: str = Field(..., description="Unique key to prevent duplicate processing")
    bot_id: str
    bot_metadata: Optional[Dict] = None
    trigger: str
    data: DataModel

class TranscriptSegment(BaseModel):
    speaker_name: str
    speaker_uuid: str
    speaker_user_uuid: Optional[str]
    timestamp_ms: int
    duration_ms: int
    transcription: Optional[str]

@app.post('/attendee_webhook')
async def add_meeting_transcript(payload:WebhookPayload,background_tasks: BackgroundTasks,db: Session = Depends(get_db)):
    meeting=db.query(Meeting).filter(Meeting.bot_id==payload.bot_id).first()
    if meeting is None:
        raise HTTPException(code=status.HTTP_404_NOT_FOUND)
    meeting.bot_data={"state":payload.data.new_state}
    db.commit()
    if payload.data.new_state=='ended':
        api_key = os.environ["ATTENDEE_APIKEY"]
        if not api_key:
            raise HTTPException(500, detail="Server misconfiguration: missing ATTENDEE_APIKEY")

        url = f"https://app.attendee.dev/api/v1/bots/{payload.bot_id}/transcript"
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=10*60) as client:
            resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            raise HTTPException(resp.status_code, detail=f"Failed to fetch transcript: {resp.text}")

        transcript:List[TranscriptSegment] = resp.json()
        final_captions=""
        if len(transcript)>0:
            for chunk in transcript:
                final_captions+= f"[{chunk.speaker_name}]: {chunk.transcription}\n"
        background_tasks.add_task(add_meeting_to_db, Item(user_id=meeting.userId,meeting_id=meeting.meeting_id,caption=final_captions))
    return {"success":True}