import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from pydantic import BaseModel
from langchain_pinecone import PineconeVectorStore
from utils import pinecone_check_index
from llm import Llm
from database import SessionLocal
from utils import get_api_keys,embeddings,pc
from models import Meeting
import json
from graph import graph
from uuid import uuid4

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

    db=SessionLocal()
    try:
        meeting=db.query(Meeting).filter(Meeting.meeting_id==item.meeting_id).first()
        keys,project=get_api_keys(item.user_id,SessionLocal())
        try:
            if keys.JIRA_API_TOKEN is not None and keys.JIRA_INSTANCE_URL is not None and keys.JIRA_USERNAME is not None:
                prompt=f"""Jira Project key: `{keys.JIRA_PROJECT}`\n
You are an AI assistant whose job is to extract *actionable* items from a meeting transcript and turn each one into a Jira task by invoking the `create_issue` tool.
*Actionable* items are first-person commitments or owner-assigned deliverables that specify a clear action (e.g., "I will update the doc," "Alice will do X by next week"). Skip any general discussion, brainstorming points without owners, or vague ideas.

For each action item:
    - Use tool `"create_issue"`

After you successfully create action items, reply exactly their json response comma separated in a json array
If you cannot create action items, reply exactly `[]`
"""
                prompt2=f"""---
**Meeting Transcript:**
\"\"\"
{item.caption}
\"\"\"
**End of Meeting Transcript**
---
"""
                config = {"configurable": {"thread_id": f"meeting_{str(uuid4())}","__api_keys":keys,"project":project,"system_message":prompt}}
                chain=graph.invoke({"messages":[prompt2]},config=config)
                if len(chain['messages']) > 1:
                    response=chain['messages'][-1]
                    if len(response.content) > 1:
                        meeting.tasks=json.loads(response.content)
                        db.commit()
                    else:
                        print("No tasks found")
            else:
                print("API_KEYS not found")
        except Exception as e:
            print("Error while making tasks from meeting: ",e)
        try:

            prompt=f"""Give summary of this meeting:
    ---
    **Meeting Transcript:**
    \"\"\"
    {item.caption}
    \"\"\"
    **End of Meeting Transcript**
    ---
    """
            response = Llm.invoke(prompt)
            if len(response.content)>1:
                meeting.summary=response.content
                db.commit()
        except Exception as e:
            print("Error while generating summary: ",e)
    except Exception as e:
        print("Something went wrong while adding meeting to DB: ",e)
    finally:
        db.close()
