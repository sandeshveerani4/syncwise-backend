from dotenv import load_dotenv
from fastapi import FastAPI,WebSocket,Depends,WebSocketException,status,HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from graph import get_graph
from fastapi import BackgroundTasks, FastAPI
from meetings import Item,add_meeting_to_db
from langchain.load.dump import dumps
from database import get_db
from models import ChatToken,User,Project,ApiKey
from tools import ApiKeys
import json
load_dotenv()

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

@app.post('/meetings')
async def add_meeting_transcript(item:Item, background_tasks: BackgroundTasks,db: Session = Depends(get_db)):
    """ token=db.query(ChatToken).filter(ChatToken.userId==item.user_id,ChatToken.sessionToken==item.token).first()
    if token is None:
        raise HTTPException(code=status.HTTP_401_UNAUTHORIZED) """
    background_tasks.add_task(add_meeting_to_db, item)
    return {"done":True}