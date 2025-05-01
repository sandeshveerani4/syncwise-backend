import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

from models import Base, User, Project, ChatToken, ApiKey, Meeting

@pytest.fixture(scope="function")
def session():
    # In-memory SQLite for fast, isolated tests
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    yield db
    db.close()

def test_user_project_meeting_relationship(session):
    # Create a user
    user = User(email="a@example.com", password="pw")
    session.add(user)
    session.commit()
    assert user.id is not None

    # Create a project and link it
    proj = Project(name="Proj1", userId=user.id)
    session.add(proj)
    session.commit()

    user.projectId = proj.id
    session.commit()
    session.refresh(user)

    assert user.projectId == proj.id
    assert proj.id is not None

    # Create a meeting under that user/project
    meet = Meeting(
        name="Kickoff",
        userId=user.id,
        projectId=proj.id,
        meeting_id="m1",
        creation_date=datetime.now(timezone.utc),
    )
    session.add(meet)
    session.commit()
    session.refresh(proj)

    assert proj.meetings[0].id == meet.id
    assert meet.user.id == user.id

def test_chattoken_relationship(session):
    # Seed a user
    user = User(email="b@example.com", password="pw")
    session.add(user)
    session.commit()

    # Create a chat token
    ct = ChatToken(userId=user.id)
    session.add(ct)
    session.commit()
    session.refresh(user)

    # Relationship works both ways
    assert user.chattoken[0].id == ct.id
    assert ct.user.id == user.id

def test_apikey_relationship(session):
    # Seed a user and project
    user = User(email="c@example.com", password="pw")
    session.add(user)
    session.commit()

    proj = Project(name="Proj2", userId=user.id)
    session.add(proj)
    session.commit()

    # Create an API key for that project
    key = ApiKey(key="xyz", service="svc", projectId=proj.id)
    session.add(key)
    session.commit()
    session.refresh(proj)

    assert proj.apiKeys[0].id == key.id
    assert key.project.id == proj.id

def test_meeting_defaults_and_json_fields(session):
    # Seed user & project
    user = User(email="d@example.com", password="pw")
    session.add(user); session.commit()
    proj = Project(name="Proj3", userId=user.id)
    session.add(proj); session.commit()

    # Create meeting without supplying tasks/attendees
    meet = Meeting(
        name="Review",
        userId=user.id,
        projectId=proj.id,
        meeting_id="m2",
        creation_date=datetime.now(timezone.utc),
    )
    session.add(meet)
    session.commit()
    session.refresh(meet)

    # JSON defaults
    assert meet.tasks == {}
    assert meet.attendees == []

    # Timestamp fields are set
    assert isinstance(meet.creation_date, datetime)
    assert meet.end_date is None
