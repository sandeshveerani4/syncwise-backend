from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI,WebSocket,Depends,WebSocketException,status,HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from graph import graph,generate_system
from fastapi import BackgroundTasks, FastAPI
from meetings import Item,add_meeting_to_db
from langchain.load.dump import dumps
from database import get_db
from models import ChatToken,Meeting,TranscriptSegment,WebhookPayload
from typing import List
import httpx
import os
from utils import get_api_keys

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
def index():
    return {"status":"working"}

@app.websocket("/ws/{user_id}/{thread_id}")
async def websocket_endpoint(websocket: WebSocket,user_id:str, thread_id: str,db: Session = Depends(get_db)):
    token=db.query(ChatToken).filter(ChatToken.userId==user_id,ChatToken.sessionToken==thread_id).first()
    if token is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION,reason="Token invalid")
    
    keys,project=get_api_keys(user_id,db)
    
    config = {"configurable": {"thread_id": thread_id,"__api_keys":keys,"project":project,"system_message":generate_system(keys,project)}}
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        async for event in graph.astream({"messages": [data]}, config=config, stream_mode="messages"):
            await websocket.send_text(dumps(event, ensure_ascii=False))
        await websocket.close()
        return

@app.post('/attendee_webhook')
async def add_meeting_transcript(payload:WebhookPayload,background_tasks: BackgroundTasks,db: Session = Depends(get_db)):
    meeting=db.query(Meeting).filter(Meeting.bot_id==payload.bot_id).first()
    if meeting is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
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
                if chunk['transcription']['transcript']:
                    final_captions+= f"[{chunk['speaker_name']}]: {chunk['transcription']['transcript']}\n"
        background_tasks.add_task(add_meeting_to_db, Item(user_id=meeting.userId,meeting_id=meeting.meeting_id,caption=final_captions))
    return {"success":True}