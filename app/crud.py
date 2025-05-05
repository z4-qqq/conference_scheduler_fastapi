"""
Database CRUD Operations Module

This module contains all database operations for the conference scheduling system.
It provides Create, Read, Update and Delete (CRUD) functionality for:
- Users (including admin users)
- Conference rooms
- Presentations
- Schedule management

All functions are database-agnostic and work through SQLAlchemy sessions.
"""

from datetime import datetime
from typing import Dict, List, Optional, Union

from sqlalchemy.orm import Session

import app.models as models
import app.schemas as schemas
from app.security_utils import get_password_hash

# User Operations

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """
    Retrieves a single user by ID
    
    Args:
        db: Database session
        user_id: ID of the user to retrieve
    
    Returns:
        User object if found, None otherwise
    """
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """
    Retrieves a single user by email address
    
    Args:
        db: Database session
        email: Email address of the user to retrieve
    
    Returns:
        User object if found, None otherwise
    """
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    """
    Retrieves a list of users with pagination
    
    Args:
        db: Database session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
    
    Returns:
        List of User objects
    """
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """
    Create a new user with properly hashed password
    
    Args:
        db: Database session
        user: UserCreate schema with email and password
    
    Returns:
        The created User object
    """
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_admin_user(db: Session, email: str, password: str) -> models.User:
    """
    Create a new admin user with properly hashed password
    
    Args:
        db: Database session
        email: Admin email address
        password: Admin password
    
    Returns:
        The created admin User object
    """
    hashed_password = get_password_hash(password)
    db_user = models.User(
        email=email,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Room Operations

def get_rooms(db: Session, skip: int = 0, limit: int = 100) -> List[models.Room]:
    """
    Retrieves a list of conference rooms with pagination
    
    Args:
        db: Database session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
    
    Returns:
        List of Room objects
    """
    return db.query(models.Room).offset(skip).limit(limit).all()

def create_room(db: Session, room: schemas.RoomBase) -> models.Room:
    """
    Creates a new conference room
    
    Args:
        db: Database session
        room: RoomBase schema with room details
    
    Returns:
        The created Room object
    """
    db_room = models.Room(**room.model_dump())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

# Presentation Operations

def get_presentations(db: Session, skip: int = 0, limit: int = 100) -> List[models.Presentation]:
    """
    Retrieves a list of presentations with pagination
    
    Args:
        db: Database session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
    
    Returns:
        List of Presentation objects
    """
    return db.query(models.Presentation).offset(skip).limit(limit).all()

def get_presentation(db: Session, presentation_id: int) -> Optional[models.Presentation]:
    """
    Retrieves a single presentation by ID
    
    Args:
        db: Database session
        presentation_id: ID of the presentation to retrieve
    
    Returns:
        Presentation object if found, None otherwise
    """
    return db.query(models.Presentation).filter(models.Presentation.id == presentation_id).first()

def create_presentation(
    db: Session, 
    presentation: schemas.PresentationCreate, 
    speaker_id: int
) -> models.Presentation:
    """
    Creates a new presentation with basic information
    
    Args:
        db: Database session
        presentation: PresentationCreate schema with title, description and duration
        speaker_id: ID of the speaker/user creating the presentation
    
    Returns:
        The created Presentation object (without scheduled time/room)
    """
    db_presentation = models.Presentation(
        title=presentation.title,
        description=presentation.description,
        duration_minutes=presentation.duration_minutes,
        speaker_id=speaker_id,
        room_id=None,
        start_time=None,
        end_time=None
    )
    db.add(db_presentation)
    db.commit()
    db.refresh(db_presentation)
    return db_presentation

def update_presentation(
    db: Session, 
    presentation_id: int, 
    presentation: schemas.PresentationBase
) -> Optional[models.Presentation]:
    """
    Updates an existing presentation
    
    Args:
        db: Database session
        presentation_id: ID of the presentation to update
        presentation: PresentationBase schema with updated fields
    
    Returns:
        Updated Presentation object if found, None otherwise
    """
    db_presentation = db.query(models.Presentation).filter(models.Presentation.id == presentation_id).first()
    if db_presentation:
        for key, value in presentation.model_dump().items():
            setattr(db_presentation, key, value)
        db.commit()
        db.refresh(db_presentation)
        return db_presentation
    return None

def delete_presentation(db: Session, presentation_id: int) -> bool:
    """
    Deletes a presentation
    
    Args:
        db: Database session
        presentation_id: ID of the presentation to delete
    
    Returns:
        True if presentation was deleted, False if not found
    """
    presentation = db.query(models.Presentation).filter(models.Presentation.id == presentation_id).first()
    if presentation:
        db.delete(presentation)
        db.commit()
        return True
    return False

# Schedule Management

def reset_schedule(db: Session) -> Dict[str, str]:
    """
    Resets the conference schedule by clearing room assignments and time slots
    
    Args:
        db: Database session
    
    Returns:
        Dictionary with a message confirming the reset
    """
    db.query(models.Presentation).update({
        models.Presentation.room_id: None,
        models.Presentation.start_time: None,
        models.Presentation.end_time: None
    })
    db.commit()
    return {"message": "Schedule has been reset"}
