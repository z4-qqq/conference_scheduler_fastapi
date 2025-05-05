"""
Database Configuration Module

This module handles all database connectivity and session management for the application.
It provides:

- Database engine configuration
- Session factory creation
- Base class for SQLAlchemy models
- Database session dependency for FastAPI routes

Uses SQLAlchemy for ORM and database abstraction.
"""

import os
from contextlib import contextmanager
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Load environment variables from .env file
load_dotenv()

# Database URL from environment variables
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Database engine instance
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Required for SQLite
)

# Session factory - the source of new database sessions
SessionLocal = sessionmaker(
    autocommit=False,  # Explicit commits required
    autoflush=False,   # No automatic flush
    bind=engine        # Bound to our database engine
)

# Base class for all SQLAlchemy models
Base = declarative_base()

def get_db():
    """
    Database session dependency generator for FastAPI routes.
    
    Yields:
        SessionLocal: A database session instance
    
    Ensures:
        The session is properly closed after use, even if an error occurs
    
    Usage:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            # db is your database session
            items = db.query(Item).all()
            return items
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        