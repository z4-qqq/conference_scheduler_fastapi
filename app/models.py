"""
Database Models Module

Defines all SQLAlchemy ORM models for the conference scheduling system.
Includes models for:

- Users (with authentication fields)
- Conference rooms
- Presentations
- Relationships between these entities

All models inherit from SQLAlchemy's Base class.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """
    User model representing conference participants and administrators.
    
    Attributes:
        id: Primary key
        email: Unique email address (used for authentication)
        hashed_password: Password hash (not plain text)
        is_active: Whether the account is active
        is_admin: Whether the user has admin privileges
        presentations: Relationship to presentations given by this user
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    presentations = relationship("Presentation", back_populates="speaker")

class Room(Base):
    """
    Conference room model representing physical/virtual spaces for presentations.
    
    Attributes:
        id: Primary key
        name: Unique name/identifier for the room
        capacity: Maximum number of attendees
        presentations: Relationship to presentations scheduled in this room
    """
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    capacity = Column(Integer)

    presentations = relationship("Presentation", back_populates="room")

class Presentation(Base):
    """
    Presentation model representing conference talks/sessions.
    
    Attributes:
        id: Primary key
        title: Presentation title
        description: Detailed description
        duration_minutes: Length in minutes
        start_time: Scheduled start time (nullable)
        end_time: Scheduled end time (nullable)
        speaker_id: ForeignKey to presenting User
        room_id: ForeignKey to scheduled Room (nullable)
        speaker: Relationship to User model
        room: Relationship to Room model
    """
    __tablename__ = "presentations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    duration_minutes = Column(Integer)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    speaker_id = Column(Integer, ForeignKey("users.id"))
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)

    speaker = relationship("User", back_populates="presentations")
    room = relationship("Room", back_populates="presentations")
