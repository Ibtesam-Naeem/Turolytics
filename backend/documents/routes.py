# ------------------------------ IMPORTS ------------------------------
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from core.db.database import get_db
from core.services.document_service import DocumentService
from core.db.base import DocumentType, DocumentStatus
from core.utils.doc_helpers import parse_tags, parse_date, parse_enum, to_response, safe_route

# ------------------------------ ROUTER SETUP ------------------------------
router = APIRouter(prefix="/documents", tags=["documents"])

# ------------------------------ PYDANTIC MODELS ------------------------------
from pydantic import BaseModel

class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_extension: str
    file_size: int
    content_type: Optional[str]
    document_type: str
    title: Optional[str]
    description: Optional[str]
    tags: Optional[List[str]]
    vehicle_id: Optional[int]
    trip_id: Optional[int]
    amount: Optional[float]
    date: Optional[datetime]
    vendor: Optional[str]
    status: str
    uploaded_at: datetime
    last_accessed_at: Optional[datetime]
    s3_url: Optional[str]

class DocumentStatsResponse(BaseModel):
    total_documents: int
    total_storage_bytes: int
    total_storage_mb: float
    by_type: dict

class DocumentUploadRequest(BaseModel):
    document_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    vehicle_id: Optional[int] = None
    trip_id: Optional[int] = None
    amount: Optional[float] = None
    document_date: Optional[datetime] = None
    vendor: Optional[str] = None

# ------------------------------ ROUTES ------------------------------

@router.post("/upload", response_model=DocumentResponse)
@safe_route
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # JSON string
    vehicle_id: Optional[int] = Form(None),
    trip_id: Optional[int] = Form(None),
    amount: Optional[float] = Form(None),
    document_date: Optional[str] = Form(None),  # ISO string
    vendor: Optional[str] = Form(None),
    account_id: int = Query(..., description="Account ID"),
    db: Session = Depends(get_db)
):
    """Upload a document to S3 and create database record."""
    doc_service = DocumentService(db)
    document = await doc_service.upload_document(
        file=file,
        account_id=account_id,
        document_type=parse_enum(DocumentType, document_type),
        title=title,
        description=description,
        tags=parse_tags(tags),
        vehicle_id=vehicle_id,
        trip_id=trip_id,
        amount=amount,
        document_date=parse_date(document_date),
        vendor=vendor
    )
    return to_response(document)

@router.get("/{document_id}", response_model=DocumentResponse)
@safe_route
async def get_document(
    document_id: int,
    account_id: int = Query(..., description="Account ID"),
    db: Session = Depends(get_db)
):
    """Get document metadata by ID."""
    doc_service = DocumentService(db)
    document = doc_service.get_document(document_id, account_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return to_response(document)

@router.get("/{document_id}/download")
@safe_route
async def download_document(
    document_id: int,
    account_id: int = Query(..., description="Account ID"),
    db: Session = Depends(get_db)
):
    """Download document file."""
    doc_service = DocumentService(db)
    result = await doc_service.download_document(document_id, account_id)
    
    return StreamingResponse(
        io.BytesIO(result['content']),
        media_type=result['content_type'],
        headers={
            "Content-Disposition": f"attachment; filename={result['document'].original_filename}"
        }
    )

@router.get("/{document_id}/url")
@safe_route
async def get_download_url(
    document_id: int,
    account_id: int = Query(..., description="Account ID"),
    expiration: int = Query(3600, description="URL expiration in seconds"),
    db: Session = Depends(get_db)
):
    """Get presigned download URL for document."""
    doc_service = DocumentService(db)
    url = await doc_service.generate_download_url(document_id, account_id, expiration)
    
    return {"download_url": url, "expires_in_seconds": expiration}

@router.get("/", response_model=List[DocumentResponse])
@safe_route
async def list_documents(
    account_id: int = Query(..., description="Account ID"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    vehicle_id: Optional[int] = Query(None, description="Filter by vehicle ID"),
    trip_id: Optional[int] = Query(None, description="Filter by trip ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Number of documents to return"),
    offset: int = Query(0, description="Number of documents to skip"),
    order_by: str = Query("uploaded_at", description="Field to order by"),
    order_direction: str = Query("desc", description="Order direction (asc/desc)"),
    db: Session = Depends(get_db)
):
    """List documents with optional filters."""
    doc_service = DocumentService(db)
    documents = doc_service.list_documents(
        account_id=account_id,
        document_type=parse_enum(DocumentType, document_type),
        vehicle_id=vehicle_id,
        trip_id=trip_id,
        status=parse_enum(DocumentStatus, status),
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_direction=order_direction
    )
    
    return [to_response(doc) for doc in documents]

@router.get("/search", response_model=List[DocumentResponse])
@safe_route
async def search_documents(
    q: str = Query(..., description="Search term"),
    account_id: int = Query(..., description="Account ID"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    limit: int = Query(50, description="Number of documents to return"),
    offset: int = Query(0, description="Number of documents to skip"),
    db: Session = Depends(get_db)
):
    """Search documents by title, description, filename, or vendor."""
    doc_service = DocumentService(db)
    documents = doc_service.search_documents(
        account_id=account_id,
        search_term=q,
        document_type=parse_enum(DocumentType, document_type),
        limit=limit,
        offset=offset
    )
    
    return [to_response(doc) for doc in documents]

@router.put("/{document_id}", response_model=DocumentResponse)
@safe_route
async def update_document(
    document_id: int,
    account_id: int = Query(..., description="Account ID"),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # JSON string
    vehicle_id: Optional[int] = Form(None),
    trip_id: Optional[int] = Form(None),
    amount: Optional[float] = Form(None),
    document_date: Optional[str] = Form(None),  # ISO string
    vendor: Optional[str] = Form(None),
    document_type: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Update document metadata."""
    # Prepare updates
    updates = {}
    if title is not None:
        updates['title'] = title
    if description is not None:
        updates['description'] = description
    if tags is not None:
        updates['tags'] = parse_tags(tags)
    if vehicle_id is not None:
        updates['vehicle_id'] = vehicle_id
    if trip_id is not None:
        updates['trip_id'] = trip_id
    if amount is not None:
        updates['amount'] = amount
    if document_date is not None:
        updates['date'] = parse_date(document_date)
    if vendor is not None:
        updates['vendor'] = vendor
    if document_type is not None:
        updates['document_type'] = parse_enum(DocumentType, document_type)
    if status is not None:
        updates['status'] = parse_enum(DocumentStatus, status)
    
    doc_service = DocumentService(db)
    document = doc_service.update_document(document_id, account_id, **updates)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return to_response(document)

@router.delete("/{document_id}")
@safe_route
async def delete_document(
    document_id: int,
    account_id: int = Query(..., description="Account ID"),
    permanent: bool = Query(False, description="Permanently delete (removes from S3)"),
    db: Session = Depends(get_db)
):
    """Delete document (soft delete by default)."""
    doc_service = DocumentService(db)
    success = await doc_service.delete_document(document_id, account_id, permanent)
    
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"message": "Document deleted successfully"}

@router.get("/stats", response_model=DocumentStatsResponse)
@safe_route
async def get_document_stats(
    account_id: int = Query(..., description="Account ID"),
    db: Session = Depends(get_db)
):
    """Get document statistics for account."""
    doc_service = DocumentService(db)
    stats = doc_service.get_document_stats(account_id)
    
    return DocumentStatsResponse(**stats)

@router.get("/vehicle/{vehicle_id}", response_model=List[DocumentResponse])
@safe_route
async def get_vehicle_documents(
    vehicle_id: int,
    account_id: int = Query(..., description="Account ID"),
    db: Session = Depends(get_db)
):
    """Get all documents for a specific vehicle."""
    doc_service = DocumentService(db)
    documents = doc_service.get_documents_by_vehicle(vehicle_id, account_id)
    
    return [to_response(doc) for doc in documents]

@router.get("/trip/{trip_id}", response_model=List[DocumentResponse])
@safe_route
async def get_trip_documents(
    trip_id: int,
    account_id: int = Query(..., description="Account ID"),
    db: Session = Depends(get_db)
):
    """Get all documents for a specific trip."""
    doc_service = DocumentService(db)
    documents = doc_service.get_documents_by_trip(trip_id, account_id)
    
    return [to_response(doc) for doc in documents]

# ------------------------------ END OF FILE ------------------------------
