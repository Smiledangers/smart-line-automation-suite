"""
File upload endpoints for handling images, audio, documents.
"""
import logging
import os
import uuid
import aiofiles
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/files", tags=["files"])

# Upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Allowed extensions by type
ALLOWED_IMAGES = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_AUDIO = {".mp3", ".m4a", ".ogg", ".wav", ".webm"}
ALLOWED_DOCS = {".pdf", ".doc", ".docx", ".txt", ".csv", ".xlsx", ".xls"}


def get_file_type(filename: str) -> str:
    """Determine file type from extension."""
    ext = Path(filename).suffix.lower()
    
    if ext in ALLOWED_IMAGES:
        return "image"
    elif ext in ALLOWED_AUDIO:
        return "audio"
    elif ext in ALLOWED_DOCS:
        return "document"
    else:
        return "unknown"


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
    conversation_id: Optional[int] = Form(None),
):
    """
    Upload a file (image, audio, or document).
    
    Returns file URL for sending via messaging platforms.
    """
    # Validate file size (max 10MB)
    file_size = 0
    contents = await file.read(10 * 1024 * 1024)  # Read first 10MB
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")
    await file.seek(0)
    
    # Validate file type
    file_type = get_file_type(file.filename)
    
    if file_type == "unknown":
        raise HTTPException(
            status_code=400,
            detail="File type not allowed. Allowed: jpg, png, gif, webp, mp3, wav, pdf, txt, csv"
        )
    
    # Generate unique filename
    ext = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{ext}"
    
    # Create user subdirectory if user_id provided
    if user_id:
        user_dir = UPLOAD_DIR / str(user_id)
        user_dir.mkdir(exist_ok=True)
        file_path = user_dir / unique_filename
    else:
        file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    try:
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)
        
        logger.info(f"File uploaded: {file.filename} -> {file_path}")
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file")
    
    # Return file URL (configure BASE_URL in production)
    base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
    file_url = f"{base_url}/api/v1/files/{file_path.name}"
    
    return {
        "status": "success",
        "filename": unique_filename,
        "original_filename": file.filename,
        "file_type": file_type,
        "file_url": file_url,
        "size": len(content),
    }


@router.get("/{filename}")
async def get_file(
    filename: str,
    request: Request,
):
    """Download a file."""
    # Security: prevent directory traversal
    filename = filename.replace("..", "")
    
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=filename,
    )


@router.delete("/{filename}")
async def delete_file(
    filename: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete an uploaded file."""
    # Security: prevent directory traversal
    filename = filename.replace("..", "")
    
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        file_path.unlink()
        logger.info(f"File deleted: {filename}")
        return {"status": "success", "message": "File deleted"}
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete file")


@router.get("/list")
async def list_files(
    user_id: Optional[str] = None,
):
    """List uploaded files."""
    if user_id:
        user_dir = UPLOAD_DIR / str(user_id)
        if user_dir.exists():
            files = list(user_dir.iterdir())
        else:
            files = []
    else:
        files = list(UPLOAD_DIR.iterdir())
    
    return {
        "files": [
            {
                "filename": f.name,
                "size": f.stat().st_size,
                "created": f.stat().st_ctime,
            }
            for f in files if f.is_file()
        ],
        "total": len(files),
    }


@router.get("/health")
async def files_health():
    """Files service health check."""
    return {
        "status": "healthy",
        "service": "files",
        "storage": str(UPLOAD_DIR),
        "allowed_types": {
            "images": list(ALLOWED_IMAGES),
            "audio": list(ALLOWED_AUDIO),
            "documents": list(ALLOWED_DOCS),
        },
    }