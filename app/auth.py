"""
Authentication and Authorization Module

This module provides JWT token handling and user authentication/authorization 
functionality for the conference scheduling API. It includes:

- JWT token creation and verification
- User authentication with password verification
- Authorization checks for active users and admin users
- Dependency injections for protected routes

Uses OAuth2 password bearer flow for token authentication.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db
from app.security_utils import pwd_context

# Load environment variables
load_dotenv()

# Configuration from environment
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a JWT access token
    
    Args:
        data: Dictionary containing the token payload (typically includes user identity)
        expires_delta: Optional timedelta for token expiration. Defaults to 15 minutes.
    
    Returns:
        str: Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> schemas.User:
    """
    Dependency that gets current authenticated user from JWT token
    
    Args:
        token: JWT token from Authorization header
        db: Database session
    
    Returns:
        schemas.User: Authenticated user object
    
    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
        
    user = crud.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
        
    return user

async def get_current_active_user(
    current_user: schemas.User = Depends(get_current_user)
) -> schemas.User:
    """
    Dependency that checks if current user is active
    
    Args:
        current_user: Authenticated user from get_current_user
    
    Returns:
        schemas.User: Active user object
    
    Raises:
        HTTPException: 400 if user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(
    current_user: schemas.User = Depends(get_current_user)
) -> schemas.User:
    """
    Dependency that checks if current user is admin
    
    Args:
        current_user: Authenticated user from get_current_user
    
    Returns:
        schemas.User: Admin user object
    
    Raises:
        HTTPException: 403 if user is not admin
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

def authenticate_user(db: Session, username: str, password: str) -> schemas.User | bool:
    """
    Authenticate user with email and password
    
    Args:
        db: Database session
        username: User's email address
        password: Plain text password
    
    Returns:
        User object if authentication succeeds, False otherwise
    """
    user = crud.get_user_by_email(db, email=username)
    if not user:
        return False
        
    if not verify_password(password, user.hashed_password):
        return False
        
    return user

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hashed version
    
    Args:
        plain_password: Input password to verify
        hashed_password: Stored password hash to compare against
    
    Returns:
        bool: True if passwords match, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)
