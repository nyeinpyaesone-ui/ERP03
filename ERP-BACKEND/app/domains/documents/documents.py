from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import shutil
import uuid

from app.database import get_db
from app.domains.documents.documents import Document
from app.auth import get_current_user
from app.config import settings
from app.services.activity_log import log_activity
from app.services.security_utils import validate_file_upload

router = APIRouter()

UPLOAD_DIR = settings.UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    title: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Upload and persist a validated document for the authenticated user.
    
    Parameters:
        file (UploadFile): The file to validate and upload.
        entity_type (Optional[str]): The type of entity associated with the document.
        entity_id (Optional[int]): The identifier of the associated entity.
        title (Optional[str]): The document title; defaults to the uploaded filename.
    
    Returns:
        Document: The newly created document record.
    
    Raises:
        HTTPException: With status code 400 if no file is provided or validation fails.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Read file content for validation
    file_content = await file.read()
    
    # Validate file using security utilities
    is_valid, error_msg, safe_filename = validate_file_upload(file_content, file.filename)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Generate unique safe filename
    unique_name = f"{uuid.uuid4()}_{safe_filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    # Write validated file
    with open(file_path, "wb") as buffer:
        buffer.write(file_content)

    # Get MIME type from validation (we know it's valid at this point)
    import mimetypes
    mime_type, _ = mimetypes.guess_type(file.filename)
    
    doc = Document(
        title=title or file.filename,
        filename=safe_filename,  # Store sanitized filename
        file_path=file_path,
        file_size=len(file_content),
        mime_type=mime_type,
        entity_type=entity_type,
        entity_id=entity_id,
        uploaded_by=current_user.id
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    log_activity(db, user_id=current_user.id, action="document_uploaded", entity_type="document", entity_id=doc.id)
    return doc

@router.get("/documents")
def list_documents(
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Document)
    if entity_type:
        query = query.filter(Document.entity_type == entity_type)
    if entity_id:
        query = query.filter(Document.entity_id == entity_id)
    return query.order_by(Document.created_at.desc()).all()

@router.get("/documents/{doc_id}")
def get_document(doc_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.delete("/documents/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    db.delete(doc)
    db.commit()
    return {"message": "Document deleted"}

