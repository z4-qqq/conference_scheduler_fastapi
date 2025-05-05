"""
Pydantic Schemas Module

Defines all data models (schemas) used for API request/response validation.
These schemas ensure type safety and data validation throughout the application.

Includes schemas for:
- User authentication and management
- Conference room management
- Presentation scheduling
- API responses and messages
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """
    Base user schema containing common user fields.
    
    Attributes:
        email: Valid email address (validated via EmailStr)
    """
    email: EmailStr

class UserCreate(UserBase):
    """
    Schema for user creation (registration).
    Extends UserBase with password field.
    
    Attributes:
        password: Plain text password (will be hashed)
    """
    password: str

class User(UserBase):
    """
    Complete user schema returned by API.
    Includes all user attributes except password.
    
    Attributes:
        id: Unique user ID
        is_active: Account activation status
        is_admin: Administrator privileges flag
    """
    id: int
    is_active: bool
    is_admin: bool

    class Config:
        from_attributes = True  # Enable ORM mode

class Token(BaseModel):
    """
    Authentication token response schema.
    
    Attributes:
        access_token: JWT token string
        token_type: Token type (e.g., 'bearer')
    """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """
    Data contained within JWT token payload.
    
    Attributes:
        email: User email (optional)
    """
    email: Optional[str] = None

class RoomBase(BaseModel):
    """
    Base room schema containing essential room fields.
    
    Attributes:
        name: Unique room name/identifier
        capacity: Maximum occupancy
    """
    name: str
    capacity: int

class Room(RoomBase):
    """
    Complete room schema including ID.
    Returned by room-related API endpoints.
    
    Attributes:
        id: Unique room ID
    """
    id: int

    class Config:
        from_attributes = True  # Enable ORM mode

class PresentationBase(BaseModel):
    """
    Base presentation schema with core presentation fields.
    
    Attributes:
        title: Presentation title
        description: Detailed description
        start_time: Scheduled start time
        end_time: Scheduled end time
        speaker_id: Presenting user ID
        room_id: Scheduled room ID
    """
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    speaker_id: int
    room_id: int

class PresentationCreate(BaseModel):
    """
    Schema for creating new presentations.
    Contains only user-provided fields.
    
    Attributes:
        title: Presentation title
        description: Detailed description
        duration_minutes: Length in minutes
    """
    title: str
    description: str
    duration_minutes: int

class Presentation(PresentationBase):
    """
    Complete presentation schema including ID and optional fields.
    Returned by presentation-related API endpoints.
    
    Attributes:
        id: Unique presentation ID
        speaker_id: Presenting user ID
        room_id: Scheduled room ID (optional)
        start_time: Scheduled start time (optional)
        end_time: Scheduled end time (optional)
    """
    id: int
    speaker_id: int
    room_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    class Config:
        from_attributes = True  # Enable ORM mode

class ScheduleRequest(BaseModel):
    """
    Request schema for schedule optimization.
    
    Attributes:
        conference_days: Number of conference days (default: 1)
        day_start_time: Daily start time in HH:MM format (default: '09:00')
        day_end_time: Daily end time in HH:MM format (default: '18:00')
        break_duration: Break duration in minutes (default: 15)
    """
    conference_days: int = 1
    day_start_time: str = "09:00"
    day_end_time: str = "18:00"
    break_duration: int = 15

class ScheduleOptimizationRequest(BaseModel):
    """
    Request schema for presentation filtering during optimization.
    
    Attributes:
        min_duration: Minimum presentation duration in minutes
        max_duration: Maximum presentation duration in minutes
        preferred_topics: Optional list of preferred topics/keywords
    """
    min_duration: int
    max_duration: int
    preferred_topics: Optional[List[str]] = None

class Message(BaseModel):
    """
    Generic message response schema.
    
    Attributes:
        message: Response message content
    """
    message: str
