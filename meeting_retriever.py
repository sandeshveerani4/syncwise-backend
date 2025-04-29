from meetings import pc,embeddings
from utils import pinecone_check_index
import os
from typing import Optional
from database import SessionLocal
from models import Meeting
import dateparser
from datetime import datetime, timedelta
import json
from pydantic import BaseModel
from langchain.tools import tool

def format_meeting_list(meetings: list[Meeting]) -> str:
    if not meetings:
        return "No meetings found."
    entries = []
    for m in meetings:
        created = m.creation_date.strftime("%Y-%m-%d %H:%M") if m.creation_date else "N/A"
        ended   = m.end_date.strftime(   "%Y-%m-%d %H:%M") if m.end_date      else "N/A"
        # build one bullet per meeting, with sub-bullets
        entries.append(
            {'id':m.id,'name':m.name,'meeting_link':m.meeting_id,'created':created,'ended':ended,'attendees':m.attendees}
        )
    return json.dumps(entries)

def list_user_meetings(user_id:str,project_id:str) -> list[Meeting]:
    return (
        SessionLocal()
        .query(Meeting)
        .filter(Meeting.userId == user_id,Meeting.projectId==project_id)
        .order_by(Meeting.creation_date.asc())
        .all()
    )

class RetrieveOrListMeetingsInput(BaseModel):
    query: str
    meeting_id: Optional[str] = None

def _retrieve_or_list_meetings(
    user_id:str,
    project_id:str
):
    @tool(
        description=(
            "If you give me a `query` and a `meeting_id`, I'll return transcript snippets.  "
            "If you only give me a `query`, I'll look for an attendee name or date and "
            "list matching meetings (showing Meeting ID, Link, Created, Ended, Attendees)."
        ),
        args_schema=RetrieveOrListMeetingsInput,
    )
    def retrieve_or_list_meetings(query: str, meeting_id: Optional[str] = None)-> str:
        pinecone_check_index(pc)
        index = pc.Index(os.environ['PINECONE_VECTOR_NAME'])
        print("Query",query)
        # 1) If they gave us a meeting_id, do the Pinecone transcript lookup:
        if meeting_id:
            print("Meeting ID",meeting_id)
            q_emb = embeddings.embed_query(query)
            res = index.query(
                vector=q_emb,
                top_k=5,
                include_metadata=True,
                filter={ "meeting_id": { "$eq": meeting_id } }
            )
            print(res)
            if not res["matches"]:
                return f"No transcript found for meeting `{meeting_id}`."
            return [m["metadata"]["text"] for m in res["matches"]]
        
        # 2) No meeting_id → we’ll query the meetings table for metadata

        meetings = list_user_meetings(user_id,project_id)
        if not meetings:
            return "You don't have any meetings scheduled."

        # 2a) look for an attendee name in the query
        lowered = query.lower()
        all_attendees = {att for m in meetings for att in m.attendees}
        for att in all_attendees:
            if att.lower() in lowered:
                filtered = [m for m in meetings if att in m.attendees]
                return format_meeting_list(filtered)

        # 2b) look for a date in the query (using dateparser)
        dt = dateparser.parse(query, settings={"PREFER_DATES_FROM": "future"})
        if dt:
            start = datetime(dt.year, dt.month, dt.day)
            end   = start + timedelta(days=1)
            filtered = [
                m for m in meetings
                if (start <= m.creation_date < end) or (start <= m.end_date < end)
            ]
            return format_meeting_list(filtered)

        # 2c) fallback: list all meetings
        return format_meeting_list(meetings)
    return retrieve_or_list_meetings