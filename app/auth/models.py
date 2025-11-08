"""Pydantic request models for the auth module.

These models validate incoming JSON/form data structures.
"""

from pydantic import BaseModel


class UserLogin(BaseModel):
    """Login payload with username and password."""
    username: str
    password: str