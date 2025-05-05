"""
Test Suite for Conference Scheduling API

Covers all major endpoints and functionality including:
- User authentication and registration
- Room management
- Presentation management
- Schedule optimization
- Authorization checks
"""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Presentation, Room, User
from app.schemas import UserCreate
from app.security_utils import pwd_context

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test database tables
Base.metadata.create_all(bind=engine)

# Dependency override
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Test data
TEST_USER = UserCreate(email="test@example.com", password="testpassword")
ADMIN_USER = UserCreate(email="admin@example.com", password="adminpassword")

# Fixtures
@pytest.fixture(scope="function")
def test_db():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Create admin user
    admin = User(
        email=ADMIN_USER.email,
        hashed_password=pwd_context.hash(ADMIN_USER.password),
    is_admin=True
)
    db.add(admin)
    db.commit()
    
    yield db
    
    # Cleanup
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def auth_headers(test_db):
    # Register test user
    client.post("/register", json=TEST_USER.model_dump())
    
    # Get access token
    response = client.post(
        "/token",
        data={"username": TEST_USER.email, "password": TEST_USER.password}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers(test_db):
    # Get admin access token
    response = client.post(
        "/token",
        data={"username": ADMIN_USER.email, "password": ADMIN_USER.password}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# Helper functions
def create_test_room(db, name="Test Room", capacity=50):
    room = Room(name=name, capacity=capacity)
    db.add(room)
    db.commit()
    return room

def create_test_presentation(db, title="Test Talk", duration=30, speaker_id=1):
    pres = Presentation(
        title=title,
        description="Test description",
        duration_minutes=duration,
        speaker_id=speaker_id
    )
    db.add(pres)
    db.commit()
    return pres

# Authentication tests
def test_register_user(test_db):
    response = client.post(
        "/register",
        json={"email": "new@example.com", "password": "newpassword"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "new@example.com"
    assert "id" in response.json()

def test_login_for_access_token(test_db):
    response = client.post(
        "/token",
        data={"username": ADMIN_USER.email, "password": ADMIN_USER.password}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

# Room management tests
def test_create_room(admin_headers):
    room_data = {"name": "Main Hall", "capacity": 100}
    response = client.post("/rooms/", json=room_data, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Main Hall"
    assert response.json()["capacity"] == 100
    assert "id" in response.json()

def test_get_rooms(test_db, admin_headers):
    # Create test room
    create_test_room(test_db)
    
    response = client.get("/rooms/", headers=admin_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Test Room"

# Presentation management tests
def test_create_presentation(auth_headers):
    pres_data = {
        "title": "New Presentation",
        "description": "About new stuff",
        "duration_minutes": 45
    }
    response = client.post("/presentations/", json=pres_data, headers=auth_headers)
    print(response.json())
    assert response.status_code == 200
    assert response.json()["title"] == "New Presentation"
    assert response.json()["speaker_id"] == 2  # First user is id 2

def test_schedule_presentation(test_db, admin_headers):
    # Create test room and presentation
    room = create_test_room(test_db)
    pres = create_test_presentation(test_db)
    
    start_time = datetime.now() + timedelta(days=1)
    response = client.put(
        f"/presentations/{pres.id}/schedule",
        params={
            "room_id": room.id,
            "start_time": start_time.isoformat()
        },
        headers=admin_headers
    )
    assert response.status_code == 200
    assert response.json()["room_id"] == room.id
    assert response.json()["start_time"] == start_time.isoformat()

# Schedule optimization tests
def test_optimize_schedule(test_db, admin_headers):
    # Create test data
    create_test_room(test_db)
    create_test_presentation(test_db)
    
    request_data = {
        "conference_days": 1,
        "day_start_time": "09:00",
        "day_end_time": "18:00",
        "break_duration": 15
    }
    response = client.post(
        "/schedule/optimize",
        json=request_data,
        headers=admin_headers
    )
    assert response.status_code == 200
    assert len(response.json()) == 1  # One room should have presentations

# Authorization tests
def test_non_admin_cannot_create_room(auth_headers):
    response = client.post(
        "/rooms/",
        json={"name": "Unauthorized", "capacity": 10},
        headers=auth_headers
    )
    assert response.status_code == 403
    assert "Not enough permissions" in response.json()["detail"]

def test_reset_schedule_admin_only(auth_headers):
    response = client.post("/schedule/reset", headers=auth_headers)
    assert response.status_code == 403
    assert "Not enough permissions" in response.json()["detail"]

# Edge cases
def test_schedule_conflict(test_db, admin_headers):
    room = create_test_room(test_db)
    start_time = datetime.now() + timedelta(days=1)
    
    # Create first presentation and schedule it
    pres1 = create_test_presentation(test_db, title="Talk 1")
    client.put(
        f"/presentations/{pres1.id}/schedule",
        params={
            "room_id": room.id,
            "start_time": start_time.isoformat()
        },
        headers=admin_headers
    )
    
    # Try to schedule overlapping presentation
    pres2 = create_test_presentation(test_db, title="Talk 2")
    response = client.put(
        f"/presentations/{pres2.id}/schedule",
        params={
            "room_id": room.id,
            "start_time": start_time.isoformat()
        },
        headers=admin_headers
    )
    assert response.status_code == 400
    assert "already booked" in response.json()["detail"]
