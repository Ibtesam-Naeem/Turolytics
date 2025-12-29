# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, UploadFile, File, Query, Depends, HTTPException, Path, Form
from fastapi.responses import StreamingResponse
from typing import Optional, Union
from datetime import datetime
import logging
from io import BytesIO

from .service import S3Service
from .schemas import DocumentOut, DocumentUpdateRequest
from turo.schemas import APIResponse
from core.database import get_db
from core.database.models.s3 import DocumentCategory
from core.database.models.account import Account
from core.security.auth import get_current_active_user
from core.utils.route_helpers import handle_route_errors
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ------------------------------ ROUTER SETUP ------------------------------
router = APIRouter(tags=["Documents"])

# ------------------------------ DEPENDENCY INJECTION ------------------------------

def get_s3_service(db: Session = Depends(get_db)) -> S3Service:
    """Dependency to get S3Service instance."""
    return S3Service(db)

# ------------------------------ DOCUMENT ENDPOINTS ------------------------------

@router.post("/upload", response_model=APIResponse)
@handle_route_errors("uploading document")
async def upload_document(
    category: DocumentCategory = Form(..., description="Document category"),
    vehicle_id: Optional[int] = Form(None, description="Vehicle ID (optional, use null for general)"),
    description: Optional[str] = Form(None, description="Optional description"),
    file: UploadFile = File(..., description="File to upload"),
    current_user: Account = Depends(get_current_active_user),
    service: S3Service = Depends(get_s3_service)
) -> APIResponse:
    """Upload a document to S3."""
    file_content = await file.read()
    
    document = service.upload_file(
        file_content=file_content,
        file_name=file.filename or "unnamed",
        file_type=file.content_type or "application/octet-stream",
        account=current_user,
        category=category,
        vehicle_id=vehicle_id,
        description=description
    )
    
    return APIResponse(
        success=True,
        data={
            "document": DocumentOut.model_validate(document, from_attributes=True),
            "message": "File uploaded successfully"
        }
    )

@router.get("/list", response_model=APIResponse)
@handle_route_errors("listing documents")
async def list_documents(
    vehicle_id: Optional[int] = Query(None, description="Filter by vehicle ID (use null for general/non-vehicle documents)"),
    category: Optional[DocumentCategory] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in file name or description"),
    start_date: Optional[datetime] = Query(None, description="Filter documents created on or after this date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Filter documents created on or before this date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: Account = Depends(get_current_active_user),
    service: S3Service = Depends(get_s3_service)
) -> APIResponse:
    """List documents with filtering and pagination."""
    documents, total = service.list_documents(
        account=current_user,
        vehicle_id=vehicle_id,
        category=category,
        search=search,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    
    return APIResponse(
        success=True,
        data={
            "documents": [DocumentOut.model_validate(d, from_attributes=True) for d in documents],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    )

@router.get("/{document_id}", response_model=None)
@handle_route_errors("getting document")
async def get_document(
    document_id: int = Path(..., description="Document ID"),
    action: Optional[str] = Query(None, description="Action: 'download' to download file, 'url' to get presigned URL, or omit for metadata"),
    expiration: int = Query(3600, ge=60, le=604800, description="URL expiration time in seconds (60-604800) - only used with action=url"),
    current_user: Account = Depends(get_current_active_user),
    service: S3Service = Depends(get_s3_service)
) -> Union[APIResponse, StreamingResponse]:
    """Get document metadata, download file, or get presigned URL."""
    if action == "download":
        file_content, file_name, file_type = service.download_file(document_id, current_user)
        file_stream = BytesIO(file_content)
        return StreamingResponse(
            file_stream,
            media_type=file_type,
            headers={
                "Content-Disposition": f'attachment; filename="{file_name}"'
            }
        )
    elif action == "url":
        url = service.get_presigned_url(document_id, current_user, expiration)
        return APIResponse(
            success=True,
            data={
                "url": url,
                "expiration_seconds": expiration
            }
        )
    else:
        document = service.get_document(document_id, current_user)
        return APIResponse(
            success=True,
            data={"document": DocumentOut.model_validate(document, from_attributes=True)}
        )

@router.put("/{document_id}", response_model=APIResponse)
@handle_route_errors("updating document")
async def update_document(
    document_id: int = Path(..., description="Document ID"),
    request: DocumentUpdateRequest = ...,
    current_user: Account = Depends(get_current_active_user),
    service: S3Service = Depends(get_s3_service)
) -> APIResponse:
    """Update document metadata."""
    document = service.update_document(
        document_id=document_id,
        account=current_user,
        category=request.category,
        vehicle_id=request.vehicle_id,
        description=request.description
    )
    
    return APIResponse(
        success=True,
        data={
            "document": DocumentOut.model_validate(document, from_attributes=True),
            "message": "Document updated successfully"
        }
    )

@router.delete("/{document_id}", response_model=APIResponse)
@handle_route_errors("deleting document")
async def delete_document(
    document_id: int = Path(..., description="Document ID"),
    current_user: Account = Depends(get_current_active_user),
    service: S3Service = Depends(get_s3_service)
) -> APIResponse:
    """Delete a document from S3 and database."""
    service.delete_file(document_id, current_user)
    
    return APIResponse(
        success=True,
        data={"message": f"Document {document_id} deleted successfully"}
    )

@router.get("/categories/list", response_model=APIResponse)
async def list_categories() -> APIResponse:
    """Get list of available document categories."""
    categories = [
        {"value": cat.value, "label": cat.value.replace("_", " ").title()}
        for cat in DocumentCategory
    ]
    
    return APIResponse(
        success=True,
        data={"categories": categories}
    )

# ------------------------------ END OF FILE ------------------------------

