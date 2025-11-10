"""Authentication routes: login, registration, and current user.

This module issues JWT access tokens and verifies them. The front-end stores
the token in localStorage and sends it as `Authorization: Bearer <token>`.
"""

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel

from jose import jwt
from datetime import datetime, timedelta
from app.db import SessionLocal, User
from app.auth.utils import verify_password
import os

router = APIRouter()

# JWT configuration
# For development, fall back to a simple default if JWT_SECRET is not set.
# WARNING: Always set a strong JWT_SECRET in production (.env)
SECRET_KEY = os.getenv("JWT_SECRET") or "H7p-BLIlm61RDYnNuWrLr9OukKNjHPpJMRASp4hhZ3E"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def create_access_token(data: dict):
    """Create a short-lived JWT token with an expiration claim (exp)."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Exchange username/password for an access token.

    The `OAuth2PasswordRequestForm` expects form data: username, password.
    """
    db = SessionLocal()
    try:
        # Find user and verify password
        user = db.query(User).filter(User.username == form_data.username).first()
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Invalid credentials")

        # If valid, return a JWT access token
        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}
    finally:
        db.close()


class UserCreate(BaseModel):
    """Payload for registering a new user."""
    username: str
    password: str


@router.post("/register")
def register(user: UserCreate):
    """Create a new user with a securely hashed password."""
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == user.username).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already registered")

        # Hash the password with bcrypt before saving
        hashed = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_user = User(username=user.username, hashed_password=hashed)
        db.add(new_user)
        db.commit()
        return {"msg": "User created"}
    finally:
        db.close()


@router.get("/me")
def read_me(token: str = Depends(oauth2_scheme)):
    """Return the username embedded in the provided Bearer token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": username}
    except Exception:
        # Any error decoding the token results in 401
        raise HTTPException(status_code=401, detail="Invalid token")