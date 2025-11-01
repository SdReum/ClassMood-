from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import FileResponse
from jose import jwt
from app.db import SessionLocal, MediaFile, User
import os
from pathlib import Path

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


async def get_current_user(token: str = Depends(oauth2_scheme)):
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
    db = SessionLocal()
    try:
        user_obj = db.query(User).filter(User.username == user).first()
        if not user_obj:
            raise HTTPException(status_code=404, detail="User not found")

        results = []
        for file in files:
            safe_filename = f"{user_obj.id}_{file.filename}"
            filepath = UPLOAD_DIR / safe_filename
            with open(filepath, "wb") as f:
                f.write(file.file.read())

            media = MediaFile(filename=file.filename, filepath=str(filepath), user_id=user_obj.id)
            db.add(media)
            db.commit()
            results.append({"filename": file.filename, "path": str(filepath)})
        return {"user": user, "results": results}
    finally:
        db.close()


@router.get("/files")
async def get_user_files(user: str = Depends(get_current_user)):
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
    db = SessionLocal()
    try:
        user_obj = db.query(User).filter(User.username == user).first()
        if not user_obj:
            raise HTTPException(status_code=404, detail="User not found")

        file = db.query(MediaFile).filter(MediaFile.id == file_id, MediaFile.user_id == user_obj.id).first()
        if not file:
            raise HTTPException(status_code=404, detail="File not found or access denied")

        # Удали файл с диска
        filepath = Path(file.filepath)
        if filepath.exists():
            filepath.unlink()

        # Удали запись из БД
        db.delete(file)
        db.commit()
        return {"msg": "File deleted"}
    finally:
        db.close()


@router.get("/files/{file_id}/download")
async def download_file(file_id: int, user: str = Depends(get_current_user)):
    db = SessionLocal()
    try:
        user_obj = db.query(User).filter(User.username == user).first()
        if not user_obj:
            raise HTTPException(status_code=404, detail="User not found")

        file = db.query(MediaFile).filter(MediaFile.id == file_id, MediaFile.user_id == user_obj.id).first()
        if not file:
            raise HTTPException(status_code=404, detail="File not found or access denied")

        filepath = Path(file.filepath)
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="Stored file is missing")

        return FileResponse(path=str(filepath), filename=file.filename)
    finally:
        db.close()