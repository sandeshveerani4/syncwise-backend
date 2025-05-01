import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from pydantic import BaseModel
from langchain_pinecone import PineconeVectorStore
from utils import pinecone_check_index
from llm import Llm
from langchain_community.agent_toolkits.jira.toolkit import JiraToolkit
from langchain_community.utilities.jira import JiraAPIWrapper
from database import SessionLocal
from utils import get_api_keys,embeddings,pc
from langchain.agents import initialize_agent, AgentType
from models import Meeting
import json

class Item(BaseModel):
    user_id: str
    meeting_id: str
    caption: str

def add_meeting_to_db(item:Item):
    pinecone_check_index(pc)
    index = pc.Index(os.environ['PINECONE_VECTOR_NAME'])
    
    vector_store = PineconeVectorStore(index=index, embedding=embeddings)

    doc = Document(page_content=item.caption,
        metadata={
            "user_id":item.user_id,
            "meeting_id":item.meeting_id,
            "source": "meeting"
        }
    )
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=200,
    length_function=len,)
    new_chunks = text_splitter.split_documents([doc])
    vector_store.add_documents(new_chunks)
    try:
        keys,project=get_api_keys(item.user_id,SessionLocal())
        if keys.JIRA_API_TOKEN is not None and keys.JIRA_INSTANCE_URL is not None and keys.JIRA_USERNAME is not None:
            jira = JiraAPIWrapper(jira_api_token=keys.JIRA_API_TOKEN,jira_username=keys.JIRA_USERNAME,jira_cloud=True,jira_instance_url=keys.JIRA_INSTANCE_URL)
            toolkit = JiraToolkit.from_jira_api_wrapper(jira)
            jira_tools = toolkit.get_tools()
            prompt=f"""You are an AI assistant whose job is to extract *actionable* items from a meeting transcript
and turn each one into a Jira task by invoking the `create_issue` tool.

For each action item:
- Use tool `"create_issue"`

If you can successfully create action items, reply exactly their json response comma separated in a json array
If you find **no** action items, reply exactly `No tasks found.`

---  
**Meeting Transcript:**  
\"\"\"  
{item.caption}
\"\"\"  
"""
            agent = initialize_agent(jira_tools,Llm,agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION)
            
            response=agent.run(prompt)
            db=SessionLocal()
            meeting=db.query(Meeting).filter(Meeting.meeting_id==item.meeting_id).first()
            meeting.tasks=json.loads(response)
            db.commit()
            db.close()
        else:
            print("API_KEYS not found")
    except Exception as e:
        print("Error while making tasks from meeting: ",e)