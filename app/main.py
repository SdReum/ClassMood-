"""Main FastAPI application.

This file wires everything together:
- Creates the FastAPI app instance
- Initializes the database on startup
- Serves basic HTML pages from `app/static/`
- Includes routers from the `auth` and `media` modules
- Exposes a simple `/meta/boot` endpoint to detect server restarts from the client
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from app.db import init_db
from app.auth.routes import router as auth_router
from app.media.routes import router as media_router
from uuid import uuid4

# Create the FastAPI app
app = FastAPI()


@app.on_event("startup")
def on_startup():
    """Called once when the server starts.

    We create DB tables if they are missing.
    """
    init_db()


# Unique boot identifier to detect server restarts from the client (front-end uses it)
BOOT_ID = str(uuid4())

# Serve files under /static (e.g., JS, CSS, HTML assets)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# The following routes just return HTML pages from the static folder.
@app.get("/")
async def read_root():
    """Return the main HTML page."""
    return FileResponse(os.path.join("app", "static", "index.html"))


@app.get("/auth")
async def read_auth():
    """Return the auth HTML page."""
    return FileResponse(os.path.join("app", "static", "index.html"))


@app.get("/upload")
async def read_upload():
    """Return the upload HTML page."""
    return FileResponse(os.path.join("app", "static", "upload.html"))


@app.get("/profile")
async def read_profile():
    """Return the profile HTML page."""
    return FileResponse(os.path.join("app", "static", "profile.html"))


@app.get("/algorithm")
async def read_algorithm():
    """Return the algorithm HTML page."""
    return FileResponse(os.path.join("app", "static", "algorithm.html"))


@app.get("/meta/boot")
async def get_boot_id():
    """Return the current boot ID so the client can detect restarts."""
    return {"boot_id": BOOT_ID}


# Register sub-routers that contain the actual API logic
app.include_router(auth_router, prefix="/auth")
app.include_router(media_router, prefix="/media")