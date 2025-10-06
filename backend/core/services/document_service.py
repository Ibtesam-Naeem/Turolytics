# ------------------------------ IMPORTS ------------------------------
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from core.services.s3_service import s3_service
from core.db.operations.document_operations import DocumentOperations
from core.db.base import Document, DocumentType, DocumentStatus

# ------------------------------ DOCUMENT SERVICE ------------------------------

class DocumentService:
    """Service for managing documents with S3 and database integration."""
    
    def __init__(self, db: Session):
        self.db = db
        self.s3_service = s3_service
        self.document_ops = DocumentOperations(db)
    
    async def upload_document(
        self,
        file: UploadFile,
        account_id: int,
        document_type: DocumentType,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        vehicle_id: Optional[int] = None,
        trip_id: Optional[int] = None,
        amount: Optional[float] = None,
        document_date: Optional[datetime] = None,
        vendor: Optional[str] = None
    ) -> Document:
        """Upload document to S3 and create database record."""
        try:
            s3_result = await self.s3_service.upload_file(
                file=file,
                account_id=account_id,
                document_type=document_type.value,
                metadata={
                    'title': title,
                    'description': description,
                    'vehicle_id': str(vehicle_id) if vehicle_id else None,
                    'trip_id': str(trip_id) if trip_id else None,
                    'amount': str(amount) if amount else None,
                    'vendor': vendor
                }
            )
            
            document = self.document_ops.create_document(
                account_id=account_id,
                filename=s3_result['filename'],
                original_filename=s3_result['original_filename'],
                file_extension=s3_result['file_extension'],
                file_size=s3_result['file_size'],
                content_type=s3_result['content_type'],
                s3_bucket=s3_result['s3_bucket'],
                s3_key=s3_result['s3_key'],
                s3_url=s3_result['s3_url'],
                document_type=document_type,
                title=title,
                description=description,
                tags=tags,
                vehicle_id=vehicle_id,
                trip_id=trip_id,
                amount=amount,
                document_date=document_date,
                vendor=vendor
            )
            
            return document
            
        except Exception as e:
            if 's3_result' in locals():
                try:
                    await self.s3_service.delete_file(s3_result['s3_key'])
                except:
                    pass  

            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload document: {str(e)}"
            )
    
    async def download_document(self, document_id: int, account_id: int) -> Dict[str, Any]:
        """Download document from S3."""
        try:
            document = self.document_ops.get_document_by_id(document_id, account_id)
            if not document:
                raise HTTPException(
                    status_code=404,
                    detail="Document not found"
                )
            
            self.document_ops.update_last_accessed(document_id, account_id)
            
            s3_result = await self.s3_service.download_file(document.s3_key)
            
            return {
                'document': document,
                'content': s3_result['content'],
                'content_type': s3_result['content_type'],
                'content_length': s3_result['content_length']
            }
            
        except HTTPException:
            raise

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to download document: {str(e)}"
            )
    
    async def delete_document(self, document_id: int, account_id: int, permanent: bool = False) -> bool:
        """Delete document (soft delete by default)."""
        try:
            document = self.document_ops.get_document_by_id(document_id, account_id)
            if not document:
                raise HTTPException(
                    status_code=404,
                    detail="Document not found"
                )
            
            if permanent:
                await self.s3_service.delete_file(document.s3_key)
                return self.document_ops.hard_delete_document(document_id, account_id)
            else:
                return self.document_ops.delete_document(document_id, account_id)
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete document: {str(e)}"
            )
    
    def get_document(self, document_id: int, account_id: int) -> Optional[Document]:
        """Get document by ID."""
        return self.document_ops.get_document_by_id(document_id, account_id)
    
    def list_documents(
        self,
        account_id: int,
        document_type: Optional[DocumentType] = None,
        vehicle_id: Optional[int] = None,
        trip_id: Optional[int] = None,
        status: Optional[DocumentStatus] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "uploaded_at",
        order_direction: str = "desc"
    ) -> List[Document]:
        """List documents with filters."""
        return self.document_ops.list_documents(
            account_id=account_id,
            document_type=document_type,
            vehicle_id=vehicle_id,
            trip_id=trip_id,
            status=status,
            limit=limit,
            offset=offset,
            order_by=order_by,
            order_direction=order_direction
        )
    
    def search_documents(
        self,
        account_id: int,
        search_term: str,
        document_type: Optional[DocumentType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Document]:
        """Search documents."""
        return self.document_ops.search_documents(
            account_id=account_id,
            search_term=search_term,
            document_type=document_type,
            limit=limit,
            offset=offset
        )
    
    def update_document(
        self,
        document_id: int,
        account_id: int,
        **updates
    ) -> Optional[Document]:
        """Update document metadata."""
        return self.document_ops.update_document(document_id, account_id, **updates)
    
    def get_documents_by_vehicle(self, vehicle_id: int, account_id: int) -> List[Document]:
        """Get all documents for a vehicle."""
        return self.document_ops.get_documents_by_vehicle(vehicle_id, account_id)
    
    def get_documents_by_trip(self, trip_id: int, account_id: int) -> List[Document]:
        """Get all documents for a trip."""
        return self.document_ops.get_documents_by_trip(trip_id, account_id)
    
    def get_document_stats(self, account_id: int) -> Dict[str, Any]:
        """Get document statistics."""
        return self.document_ops.get_document_stats(account_id)
    
    async def generate_download_url(self, document_id: int, account_id: int, expiration: int = 3600) -> str:
        """Generate presigned URL for document download."""
        try:
            document = self.document_ops.get_document_by_id(document_id, account_id)
            if not document:
                raise HTTPException(
                    status_code=404,
                    detail="Document not found"
                )
            
            self.document_ops.update_last_accessed(document_id, account_id)
            
            url = self.s3_service._generate_presigned_url(document.s3_key, expiration)
            
            self.document_ops.update_document(document_id, account_id, s3_url=url)
            
            return url
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate download URL: {str(e)}"
            )

# ------------------------------ END OF FILE ------------------------------
