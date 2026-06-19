import os
import uuid
import shutil
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_async_db
from app.db.models import User, Document
from app.api.dependencies import get_current_user
from app.models.document import DocumentResponse

router = APIRouter()

UPLOAD_DIR = "data/documents"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    # Check file size using FastAPI's built-in UploadFile.size
    if file.size is not None and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds the 5MB limit."
        )

    # Generate a unique filename to prevent collisions
    file_extension = ""
    if file.filename and "." in file.filename:
        file_extension = f".{file.filename.split('.')[-1]}"
    
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Save the file to the local filesystem
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    # Create the Document record in the DB
    document = Document(
        document_id=str(uuid.uuid4()),
        user_id=current_user.user_id,
        file_name=file.filename or "unknown_document",
        storage_path=file_path,
        uploaded_at=datetime.now(timezone.utc)
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    return document

@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Document).where(Document.user_id == current_user.user_id).order_by(Document.uploaded_at.desc())
    result = await db.execute(stmt)
    documents = result.scalars().all()
    
    return documents

@router.get("/{document_id}/download", response_class=FileResponse)
async def download_document(
    document_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Document).where(
        (Document.document_id == document_id) & 
        (Document.user_id == current_user.user_id)
    )
    result = await db.execute(stmt)
    document = result.scalars().first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )
        
    if not os.path.exists(document.storage_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server."
        )
        
    return FileResponse(
        path=document.storage_path,
        filename=document.file_name,
        media_type="application/octet-stream"
    )

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Document).where(
        (Document.document_id == document_id) & 
        (Document.user_id == current_user.user_id)
    )
    result = await db.execute(stmt)
    document = result.scalars().first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )
        
    # Remove from filesystem
    if os.path.exists(document.storage_path):
        try:
            os.remove(document.storage_path)
        except Exception as e:
            # We can log the error, but we still want to delete the DB record
            print(f"Failed to delete file {document.storage_path}: {e}")
            
    # Delete from database
    await db.delete(document)
    await db.commit()

