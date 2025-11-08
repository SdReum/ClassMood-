"""Database configuration and models (SQLAlchemy).

This file connects to the database, creates a session factory, and defines
simple models used by the app. If you are new to SQLAlchemy:
- "engine" is the connection to the DB.
- "SessionLocal" lets us open/close DB sessions for each request.
- "Base" is the parent class for our models.
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
import os
from dotenv import load_dotenv

# Load variables from a .env file (e.g., DATABASE_URL)
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")  # Example: postgresql://user:pass@host:5432/dbname

# Provide a beginner-friendly default: use a local SQLite DB if env is missing
if not DATABASE_URL:
    # Stores a file named app.db in the project root (where you run uvicorn)
    DATABASE_URL = "sqlite:///./app.db"

# Create a database connection "engine"
if DATABASE_URL.startswith("sqlite"):
    # SQLite needs this flag when used in multi-threaded servers
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

# Session factory: each API call should create its own session and close it
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()


class User(Base):
    """A simple user table storing username and hashed_password."""

    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)


class MediaFile(Base):
    """Stores uploaded files and links them to a user."""

    __tablename__ = "media_files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    filepath = Column(String)  # absolute or relative path on disk
    user_id = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())


def init_db():
    """Create tables if they don't exist yet.

    Called once at app startup in `app/main.py`.
    """
    Base.metadata.create_all(bind=engine)