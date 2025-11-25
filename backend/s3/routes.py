# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, UploadFile, File, Query, Depends, HTTPException, Path, Form
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime
import logging
from io import BytesIO

from .service import S3Service
from .schemas import DocumentOut, DocumentUpdateRequest
from turo.schemas import APIResponse
from core.database import get_db
from core.database.models.s3 import DocumentCategory
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
async def upload_document(
    account_id: int = Form(..., description="Account ID"),
    category: DocumentCategory = Form(..., description="Document category"),
    vehicle_id: Optional[int] = Form(None, description="Vehicle ID (optional, use null for general)"),
    description: Optional[str] = Form(None, description="Optional description"),
    file: UploadFile = File(..., description="File to upload"),
    service: S3Service = Depends(get_s3_service)
) -> APIResponse:
    """Upload a document to S3."""
    try:
        file_content = await file.read()
        
        document = service.upload_file(
            file_content=file_content,
            file_name=file.filename or "unnamed",
            file_type=file.content_type or "application/octet-stream",
            account_id=account_id,
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
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")

@router.get("/list", response_model=APIResponse)
async def list_documents(
    account_id: int = Query(..., description="Account ID"),
    vehicle_id: Optional[int] = Query(None, description="Filter by vehicle ID (use null for general/non-vehicle documents)"),
    category: Optional[DocumentCategory] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in file name or description"),
    start_date: Optional[datetime] = Query(None, description="Filter documents created on or after this date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Filter documents created on or before this date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    service: S3Service = Depends(get_s3_service)
) -> APIResponse:
    """List documents with filtering and pagination."""
    try:
        documents, total = service.list_documents(
            account_id=account_id,
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
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@router.get("/{document_id}", response_model=APIResponse)
async def get_document(
    document_id: int = Path(..., description="Document ID"),
    account_id: int = Query(..., description="Account ID"),
    service: S3Service = Depends(get_s3_service)
) -> APIResponse:
    """Get document metadata by ID."""
    try:
        document = service.get_document(document_id, account_id)
        return APIResponse(
            success=True,
            data={"document": DocumentOut.model_validate(document, from_attributes=True)}
        )
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Error getting document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")

@router.get("/{document_id}/download")
async def download_document(
    document_id: int = Path(..., description="Document ID"),
    account_id: int = Query(..., description="Account ID"),
    service: S3Service = Depends(get_s3_service)
) -> StreamingResponse:
    """Download a document file."""
    try:
        file_content, file_name, file_type = service.download_file(document_id, account_id)
        
        file_stream = BytesIO(file_content)
        
        return StreamingResponse(
            file_stream,
            media_type=file_type,
            headers={
                "Content-Disposition": f'attachment; filename="{file_name}"'
            }
        )
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Error downloading document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download document: {str(e)}")

@router.get("/{document_id}/url", response_model=APIResponse)
async def get_document_url(
    document_id: int = Path(..., description="Document ID"),
    account_id: int = Query(..., description="Account ID"),
    expiration: int = Query(3600, ge=60, le=604800, description="URL expiration time in seconds (60-604800)"),
    service: S3Service = Depends(get_s3_service)
) -> APIResponse:
    """Get presigned URL for document access."""
    try:
        url = service.get_presigned_url(document_id, account_id, expiration)
        
        return APIResponse(
            success=True,
            data={
                "url": url,
                "expiration_seconds": expiration
            }
        )
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Error generating document URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate document URL: {str(e)}")

@router.put("/{document_id}", response_model=APIResponse)
async def update_document(
    document_id: int = Path(..., description="Document ID"),
    account_id: int = Query(..., description="Account ID"),
    request: DocumentUpdateRequest = ...,
    service: S3Service = Depends(get_s3_service)
) -> APIResponse:
    """Update document metadata."""
    try:
        document = service.update_document(
            document_id=document_id,
            account_id=account_id,
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
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Error updating document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update document: {str(e)}")

@router.delete("/{document_id}", response_model=APIResponse)
async def delete_document(
    document_id: int = Path(..., description="Document ID"),
    account_id: int = Query(..., description="Account ID"),
    service: S3Service = Depends(get_s3_service)
) -> APIResponse:
    """Delete a document from S3 and database."""
    try:
        service.delete_file(document_id, account_id)
        
        return APIResponse(
            success=True,
            data={"message": f"Document {document_id} deleted successfully"}
        )
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

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

