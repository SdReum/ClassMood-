"""Media routes: upload files, list user's files, delete and download.

All endpoints require a valid JWT token. We decode it to get the username,
find the related user in the database, and then operate only on that user's files.
"""

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import FileResponse
from jose import jwt
from app.db import SessionLocal, MediaFile, User
import os
from pathlib import Path
from app.alg.engine import analyze_file

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
# Match auth module behavior: provide a development default when JWT_SECRET is unset.
# WARNING: Set a strong JWT_SECRET in production (.env)
SECRET_KEY = os.getenv("JWT_SECRET") or "dev-secret-change-me"
ALGORITHM = "HS256"

# Where we store uploaded files on disk (local dev). In production, consider S3.
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Extract username from the Bearer token, or raise 401 if invalid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/upload")
async def upload(
        files: list[UploadFile] = File(...),
        user: str = Depends(get_current_user)
):
    """Upload one or more files and save records in the database."""
    db = SessionLocal()
    try:
        # Verify the user exists
        user_obj = db.query(User).filter(User.username == user).first()
        if not user_obj:
            raise HTTPException(status_code=404, detail="User not found")

        results = []
        for file in files:
            # Build a simple unique filename (prefix with user ID)
            safe_filename = f"{user_obj.id}_{file.filename}"
            filepath = UPLOAD_DIR / safe_filename
            # Save content to disk
            with open(filepath, "wb") as f:
                f.write(file.file.read())

            # Create a DB record for the upload
            media = MediaFile(filename=file.filename, filepath=str(filepath), user_id=user_obj.id)
            db.add(media)
            db.commit()
            results.append({"filename": file.filename, "path": str(filepath)})
        return {"user": user, "results": results}
    finally:
        db.close()


@router.get("/files")
async def get_user_files(user: str = Depends(get_current_user)):
    """Return a list of the current user's uploaded files."""
    db = SessionLocal()
    try:
        user_obj = db.query(User).filter(User.username == user).first()
        if not user_obj:
            raise HTTPException(status_code=404, detail="User not found")

        files = db.query(MediaFile).filter(MediaFile.user_id == user_obj.id).all()
        return {
            "user": user,
            "files": [
                {"id": f.id, "filename": f.filename, "uploaded_at": f.uploaded_at}
                for f in files
            ]
        }
    finally:
        db.close()


@router.delete("/files/{file_id}")
async def delete_file(file_id: int, user: str = Depends(get_current_user)):
    """Delete a file (both from disk and DB) if it belongs to the current user."""
    db = SessionLocal()
    try:
        user_obj = db.query(User).filter(User.username == user).first()
        if not user_obj:
            raise HTTPException(status_code=404, detail="User not found")

        file = db.query(MediaFile).filter(MediaFile.id == file_id, MediaFile.user_id == user_obj.id).first()
        if not file:
            raise HTTPException(status_code=404, detail="File not found or access denied")

        # Remove from disk if present
        filepath = Path(file.filepath)
        if filepath.exists():
            filepath.unlink()

        # Remove DB row
        db.delete(file)
        db.commit()
        return {"msg": "File deleted"}
    finally:
        db.close()


@router.get("/files/{file_id}/download")
async def download_file(file_id: int, user: str = Depends(get_current_user)):
    """Send the file to the client if it belongs to the current user."""
    db = SessionLocal()
    try:
        user_obj = db.query(User).filter(User.username == user).first()
        if not user_obj:
            raise HTTPException(status_code=404, detail="User not found")

        file = db.query(MediaFile).filter(
            MediaFile.id == file_id, MediaFile.user_id == user_obj.id
        ).first()
        if not file:
            raise HTTPException(status_code=404, detail="File not found or access denied")

        filepath = Path(file.filepath)
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="Stored file is missing")

        return FileResponse(path=str(filepath), filename=file.filename)
    finally:
        db.close()

@router.get("/files/{file_id}/analyze")
async def analyze_media_file(file_id: int, user: str = Depends(get_current_user)):
    """Run the algorithm on a specific file owned by the current user.

    Returns a JSON payload like {"series": [{"t": 0.0, "value": 0.12}, ...]}
    which the frontend renders as a chart.
    """
    db = SessionLocal()
    try:
        user_obj = db.query(User).filter(User.username == user).first()
        if not user_obj:
            raise HTTPException(status_code=404, detail="User not found")

        file = db.query(MediaFile).filter(
            MediaFile.id == file_id, MediaFile.user_id == user_obj.id
        ).first()
        if not file:
            raise HTTPException(status_code=404, detail="File not found or access denied")

        filepath = Path(file.filepath)
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="Stored file is missing")

        result = analyze_file(filepath)
        return result
    finally:
        db.close()