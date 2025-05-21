from sqlalchemy import Column, String,JSON,ARRAY,DateTime,Boolean,ForeignKey,Integer
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime,timezone
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import Optional,Dict
from pydantic import BaseModel,Field

Base  = declarative_base()

class User(Base):
    __tablename__ = "User"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    emailVerified = Column(DateTime, nullable=True)
    image = Column(String, nullable=True)
    onboarded = Column(Boolean, nullable=False, default=False)
    createdAt = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    updatedAt = Column(
        DateTime,
        nullable=False,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )

    # relations
    projectId = Column(String, ForeignKey("Project.id"), nullable=True)

    chattoken = relationship(
        "ChatToken", back_populates="user", cascade="all, delete-orphan"
    )
    meetings = relationship(
        "Meeting", back_populates="user", cascade="all, delete-orphan"
    )


class ChatToken(Base):
    __tablename__ = "ChatToken"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sessionToken = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    userId = Column(String, ForeignKey("User.id", ondelete="CASCADE"), nullable=False)

    # relations
    user = relationship("User", back_populates="chattoken")


class Project(Base):
    __tablename__ = "Project"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    userId = Column(String, ForeignKey("User.id"), nullable=False)
    githubInstallationId = Column(Integer, nullable=True)
    githubRepo = Column(String, nullable=True)
    additionalData = Column(JSON, nullable=True)
    createdAt = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    updatedAt = Column(
        DateTime,
        nullable=False,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )

    apiKeys = relationship(
        "ApiKey", back_populates="project", cascade="all, delete-orphan"
    )
    meetings = relationship(
        "Meeting", back_populates="project", cascade="all, delete-orphan"
    )


class ApiKey(Base):
    __tablename__ = "ApiKey"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String, nullable=False)
    service = Column(String, nullable=False)
    additionalData = Column(JSON, nullable=True)
    projectId = Column(
        String, ForeignKey("Project.id", ondelete="SET NULL"), nullable=True
    )
    createdAt = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    updatedAt = Column(
        DateTime,
        nullable=False,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )

    # relations
    project = relationship("Project", back_populates="apiKeys")


class Meeting(Base):
    __tablename__ = "Meeting"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=True)
    userId = Column(String, ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    projectId = Column(
        String, ForeignKey("Project.id", ondelete="CASCADE"), nullable=False
    )
    meeting_id = Column(String, nullable=False)
    tasks = Column(JSON, nullable=False, default=dict)
    attendees = Column(JSON, nullable=False, default=list)
    creation_date = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    end_date = Column(DateTime, nullable=True)
    bot_id = Column(String, nullable=True)
    bot_data = Column(JSON, nullable=False, default=dict)
    summary=Column(String,nullable=True)
    # relations
    user = relationship("User", back_populates="meetings")
    project = relationship("Project", back_populates="meetings")

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