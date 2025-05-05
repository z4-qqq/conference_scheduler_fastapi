"""
Conference Scheduling API Main Module

This is the core FastAPI application that provides endpoints for:
- User authentication and authorization
- Conference room management
- Presentation scheduling
- Conference schedule optimization

The API follows RESTful principles and uses JWT for authentication.
"""

from datetime import datetime, timedelta
from typing import List

import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import auth, crud, models, scheduler, schemas
from app.database import engine, get_db

# Load environment variables
load_dotenv()

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI application
app = FastAPI(
    title="Conference Scheduling API",
    description="API for managing conference presentations and schedules",
    version="1.0.0"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication Endpoints
@app.post("/register", response_model=schemas.User, summary="Register a new user")
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account
    
    Args:
        user: UserCreate schema containing email and password
    
    Returns:
        Newly created User object
    
    Raises:
        HTTPException: 400 if email already registered
    """
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.post("/token", response_model=schemas.Token, summary="Get access token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate and receive JWT access token
    
    Args:
        form_data: OAuth2 password form with username and password
    
    Returns:
        dict: Access token and token type
    
    Raises:
        HTTPException: 401 if authentication fails
    """
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.User, summary="Get current user info")
async def read_users_me(
    current_user: schemas.User = Depends(auth.get_current_active_user)
):
    """
    Get information about the currently authenticated user
    
    Returns:
        User object for the authenticated user
    """
    return current_user

# Room Management Endpoints
@app.post("/rooms/", response_model=schemas.Room, summary="Create a new room")
def create_room(
    room: schemas.RoomBase,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_admin_user)
):
    """
    Create a new conference room (Admin only)
    
    Args:
        room: RoomBase schema with room details
    
    Returns:
        Created Room object
    """
    return crud.create_room(db=db, room=room)

@app.get("/rooms/", response_model=List[schemas.Room], summary="List all rooms")
def read_rooms(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get paginated list of conference rooms
    
    Args:
        skip: Number of items to skip
        limit: Maximum number of items to return
    
    Returns:
        List of Room objects
    """
    rooms = crud.get_rooms(db, skip=skip, limit=limit)
    return rooms

# Presentation Management Endpoints
@app.post("/presentations/", response_model=schemas.Presentation, summary="Create a presentation")
def create_presentation(
    presentation: schemas.PresentationCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_active_user)
):
    """
    Create a new presentation (Speaker only)
    
    Args:
        presentation: Presentation details
    
    Returns:
        Created Presentation object
    """
    db_presentation = crud.create_presentation(
        db=db,
        presentation=presentation,
        speaker_id=current_user.id
    )
    return db_presentation

@app.get("/presentations/", response_model=List[schemas.Presentation], summary="List presentations")
def read_presentations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get paginated list of presentations
    
    Args:
        skip: Number of items to skip
        limit: Maximum number of items to return
    
    Returns:
        List of Presentation objects
    """
    presentations = crud.get_presentations(db, skip=skip, limit=limit)
    return presentations

@app.delete("/presentations/{presentation_id}", summary="Delete a presentation")
def delete_presentation(
    presentation_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_admin_user)
):
    """
    Delete a presentation (Admin only)
    
    Args:
        presentation_id: ID of presentation to delete
    
    Returns:
        dict: Success message
    
    Raises:
        HTTPException: 404 if presentation not found
    """
    success = crud.delete_presentation(db, presentation_id=presentation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Presentation not found")
    return {"message": "Presentation deleted successfully"}

@app.put("/presentations/{presentation_id}", response_model=schemas.Presentation, summary="Update presentation")
def update_presentation(
    presentation_id: int,
    presentation: schemas.PresentationBase,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_admin_user)
):
    """
    Update presentation details (Admin only)
    
    Args:
        presentation_id: ID of presentation to update
        presentation: Updated presentation details
    
    Returns:
        Updated Presentation object
    
    Raises:
        HTTPException: 404 if presentation not found
    """
    updated = crud.update_presentation(db, presentation_id=presentation_id, presentation=presentation)
    if not updated:
        raise HTTPException(status_code=404, detail="Presentation not found")
    return updated

# Schedule Management Endpoints
@app.put("/presentations/{presentation_id}/schedule", response_model=schemas.Presentation, summary="Schedule a presentation")
def schedule_presentation(
    presentation_id: int,
    room_id: int,
    start_time: datetime,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_admin_user)
):
    """
    Schedule a presentation in specific room and time (Admin only)
    
    Args:
        presentation_id: ID of presentation to schedule
        room_id: ID of room to schedule in
        start_time: When the presentation should start
    
    Returns:
        Scheduled Presentation object
    
    Raises:
        HTTPException: 404 if presentation not found
        HTTPException: 400 if room is already booked
    """
    presentation = crud.get_presentation(db, presentation_id=presentation_id)
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")
    
    # Check room availability
    conflicting = db.query(models.Presentation).filter(
        models.Presentation.room_id == room_id,
        models.Presentation.start_time < start_time + timedelta(minutes=presentation.duration_minutes),
        models.Presentation.end_time > start_time,
        models.Presentation.id != presentation_id
    ).first()
    if conflicting:
        raise HTTPException(status_code=400, detail="Room is already booked for the selected time")
    # Update presentation
    presentation.room_id = room_id
    presentation.start_time = start_time
    presentation.end_time = start_time + timedelta(minutes=presentation.duration_minutes)
    
    db.commit()
    db.refresh(presentation)    
    return presentation

@app.post("/schedule/optimize", summary="Optimize conference schedule")
def optimize_schedule(
    request: schemas.ScheduleRequest,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_admin_user)
):
    """
    Automatically optimize the conference schedule (Admin only)
    
    Args:
        request: Schedule optimization parameters
    
    Returns:
        dict: Optimized schedule
    
    Raises:
        HTTPException: 400 if optimization fails
    """
    try:
        result = scheduler.schedule_all_presentations(db, request.model_dump())
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/schedule/reset", response_model=schemas.Message, summary="Reset schedule")
def reset_schedule(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_admin_user)
):
    """
    Reset all scheduled presentations (Admin only)
    
    Returns:
        dict: Success message
    """
    return crud.reset_schedule(db)

# Startup event to create admin user if needed
@app.on_event("startup")
def startup_event():
    """Initialize admin user on application startup"""
    db = next(get_db())
    admin = crud.get_user_by_email(db, email="admin@example.com")
    if not admin:
        crud.create_admin_user(
            db,
            email="admin@example.com",
            password="adminpassword"  # This will now be properly hashed
        )
    db.close()

# Main entry point
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
