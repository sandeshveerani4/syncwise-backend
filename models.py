from sqlalchemy import Column, String,JSON,ARRAY,DateTime
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import Optional,Dict

Base  = declarative_base()

class ChatToken(Base):
    __tablename__ = 'ChatToken'
    id  = Column(String, primary_key=True, index=True)
    sessionToken = Column(String)
    userId = Column(String)

class User(Base):
    __tablename__ = 'User'
    id  = Column(String, primary_key=True, index=True)
    projectId=Column(String)

class Project(Base):
    __tablename__ = 'Project'
    id  = Column(String, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    userId = Column(String)
    githubRepo = Column(String,nullable=True)

class ApiKey(Base):
    __tablename__ = 'ApiKey'
    id  = Column(String, primary_key=True, index=True)
    key = Column(String)
    service = Column(String)
    additionalData = Column(JSON)
    projectId=Column(String)

class Meeting(Base):
    __tablename__ = 'Meeting'
    id  = Column(String, primary_key=True, index=True)
    name = Column(String,nullable=True)
    userId = Column(String)
    projectId = Column(String)
    meeting_id = Column(String)
    attendees = Column(ARRAY(String),default=[])
    creation_date=Column(DateTime)
    end_date=Column(DateTime,nullable=True)
    bot_id=Column(String,nullable=True)
    bot_data=Column(JSON)
    tasks=Column(JSON)

class ApiKeys(BaseModel):
    user_id:str=None
    project_id:str=None
    JIRA_PROJECT:Optional[str]=None
    JIRA_API_TOKEN: Optional[str]=None
    JIRA_USERNAME:Optional[str]=None
    JIRA_INSTANCE_URL:Optional[str]=None
    GITHUB_REPOSITORY:Optional[str]=None
    SLACK_USER_TOKEN:Optional[str]=None
    CALENDAR_TOKEN:Dict[str,str]=None