from __future__ import annotations

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from typing import List, Optional, Tuple, Dict
from langchain_core.utils import guard_import
import time
from sqlalchemy.orm import Session
from models import User,Project,ApiKey
from models import ApiKeys
from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings

import json

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

pc = Pinecone(api_key=os.environ['PINECONE_API_KEY'])

def import_google() -> Tuple[Request, Credentials]:
    """Import google libraries.

    Returns:
        Tuple[Request, Credentials]: Request and Credentials classes.
    """
    return (
        guard_import(
            module_name="google.auth.transport.requests",
            pip_name="google-auth",
        ).Request,
        guard_import(
            module_name="google.oauth2.credentials", pip_name="google-auth"
        ).Credentials,
    )

DEFAULT_SCOPES = ["https://www.googleapis.com/auth/calendar"]

def get_google_credentials(
    token: Dict[str,str],
    scopes: Optional[List[str]] = None,
) -> Credentials:
    """Get credentials."""
    # From https://developers.google.com/calendar/api/quickstart/python
    Request, Credentials = import_google()
    creds = None
    scopes = scopes or DEFAULT_SCOPES
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    token.update({'client_secret':os.environ['GOOGLE_CLIENT_SECRET'],'client_id':os.environ['GOOGLE_CLIENT_ID'],'scopes':scopes,"universe_domain": "googleapis.com","token_uri": "https://oauth2.googleapis.com/token"})
    creds = Credentials.from_authorized_user_info(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # type: ignore[call-arg]
    return creds

from pinecone import Pinecone, ServerlessSpec

def pinecone_check_index(pc:Pinecone):
    index_name = os.environ['PINECONE_VECTOR_NAME']

    existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]
    if index_name not in existing_indexes:
        pc.create_index(
            name=index_name,
            dimension=3072,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        while not pc.describe_index(index_name).status["ready"]:
            time.sleep(1)

from fastapi import WebSocketException,status

def get_api_keys(user_id:str,db:Session):
    keys=ApiKeys()
    user=db.query(User).filter(User.id==user_id).first()
    if user is None:
        raise WebSocketException(status.WS_1008_POLICY_VIOLATION,"User not found")
    keys.user_id=user_id
    
    project=db.query(Project).filter(Project.id==user.projectId).first()
    if project is None:
        raise WebSocketException(status.WS_1008_POLICY_VIOLATION,"Project not found")
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
                keys.JIRA_PROJECT=key.additionalData['projectKey']
            elif key.service == 'calendar':
                keys.CALENDAR_TOKEN=json.loads(key.key)
        except Exception as e:
            print(e)
    return (keys,project)