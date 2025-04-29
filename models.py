from sqlalchemy import Column, String,JSON,ARRAY,DateTime
from sqlalchemy.ext.declarative import declarative_base
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
    tasks=Column(ARRAY(JSON),default=[])