import requests
import asyncio
import websockets
import json
from database import SessionLocal
from models import User,ChatToken,Project
import pytest
# Change these if your server is on a different host/port
HTTP_BASE = "http://localhost:8000"
WS_BASE   = "ws://localhost:8000"

def test_health():
    """Call GET / and expect {"status":"working"}."""
    resp = requests.get(f"{HTTP_BASE}/")
    assert resp.status_code == 200, f"Health returned {resp.status_code}"
    data = resp.json()
    assert data.get("status") == "working", f"Unexpected payload: {data}"
    print("✔ Health check passed")

@pytest.mark.asyncio
async def test_websocket_chat(msg="Hello"):
    """
    Open WS to /ws/{user_id}/{thread_id}, send a JSON message,
    and print the AI response.
    """
    db=SessionLocal()

    user = db.query(User).filter(User.email=='test@test.com').first()
    
    if user is None:
        user=User(name="test user",email='test@test.com',password='testpass')
        db.add(user)
        db.commit()
    
    if user.projectId is None:
        project=Project(name="Test Project",userId=user.id)
        db.add(project)
        db.commit()
        user.projectId=project.id
        db.commit()
    
    user_id = user.id

    # Create a new chat token for the chat
    
    ct=ChatToken(userId=user_id)
    db.add(ct)
    db.commit()
    thread_id = ct.sessionToken
    uri = f"{WS_BASE}/ws/{user_id}/{thread_id}"

    print(f"→ Connecting to {uri}")
    async with websockets.connect(uri) as ws:
        await ws.send(msg)
        print("→ Sent:", msg)
        print("***Output***")
        async for raw in ws:
            data = json.loads(raw)
            assert "content" in data[0]['kwargs']
            assert "langgraph_node" in data[1]
            if data[1]['langgraph_node']=='agent':
                print(data[0]['kwargs']['content'], end="")
        print("***Output End***")

@pytest.mark.asyncio
async def test_websocket_no_chattoken():
    db = SessionLocal()
    # Create user + project, but do NOT create ChatToken
    user = db.query(User).filter_by(email='test+noct@example.com').first()
    if not user:
        user = User(name="NoToken", email='test+noct@example.com', password='pw')
        db.add(user); db.commit()
    if not user.projectId:
        proj = Project(name="NoTokenProj", userId=user.id)
        db.add(proj); db.commit()
        user.projectId = proj.id; db.commit()

    invalid_session = "nonexistent-token"
    uri = f"{WS_BASE}/ws/{user.id}/{invalid_session}"

    print(f"→ Connecting to {uri} (no chat token case)")
    try:
        async with websockets.connect(uri):
            pass
        assert False, "Connection should have been rejected"
    except Exception as e:
        print("✔ No-ChatToken connection correctly failed:", type(e).__name__)

@pytest.mark.asyncio
async def test_websocket_invalid_chattoken():
    # Similar to above: wrong user/session combo
    # Use a user ID that doesn’t exist
    fake_user = "00000000-0000-0000-0000-000000000000"
    fake_token = "invalid-token"
    uri = f"{WS_BASE}/ws/{fake_user}/{fake_token}"

    print(f"→ Connecting to {uri} (invalid chat token case)")
    try:
        async with websockets.connect(uri):
            pass
        assert False, "Connection should have been rejected"
    except Exception as e:
        print("✔ Invalid-ChatToken connection correctly failed:", type(e).__name__)

@pytest.mark.asyncio
async def test_websocket_no_project():
    db = SessionLocal()
    # Create a user but do NOT set projectId
    user = db.query(User).filter_by(email='test+noproject@example.com').first()
    if not user:
        user = User(name="NoProj", email='test+noproject@example.com', password='pw')
        db.add(user); db.commit()
    user.projectId = None
    db.commit()

    # Create a valid ChatToken
    token = ChatToken(userId=user.id)
    db.add(token)
    db.commit()
    uri = f"{WS_BASE}/ws/{user.id}/{token.sessionToken}"

    print(f"→ Connecting to {uri} (no projectId case)")
    try:
        async with websockets.connect(uri):
            pass
        assert False, "Connection should have been rejected due to missing project"
    except Exception as e:
        print("✔ No-Project connection correctly failed:", type(e).__name__)

if __name__ == "__main__":
    print("\nRunning integration tests against live server…\n")
    test_health()
    asyncio.run(test_websocket_chat())
    asyncio.run(test_websocket_no_chattoken())
    asyncio.run(test_websocket_invalid_chattoken())
    asyncio.run(test_websocket_no_project())
    print("\n✅ All integration tests passed!\n")
