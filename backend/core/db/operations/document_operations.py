# ------------------------------ IMPORTS ------------------------------
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from fastapi import HTTPException

from core.db.base import Document, DocumentType, DocumentStatus, Account, Vehicle, Trip

# ------------------------------ DOCUMENT OPERATIONS ------------------------------

class DocumentOperations:
    """Database operations for document management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_document(
        self,
        account_id: int,
        filename: str,
        original_filename: str,
        file_extension: str,
        file_size: int,
        content_type: str,
        s3_bucket: str,
        s3_key: str,
        s3_url: str,
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
        """Create a new document record."""
        try:
            document = Document(
                account_id=account_id,
                vehicle_id=vehicle_id,
                trip_id=trip_id,
                filename=filename,
                original_filename=original_filename,
                file_extension=file_extension,
                file_size=file_size,
                content_type=content_type,
                s3_bucket=s3_bucket,
                s3_key=s3_key,
                s3_url=s3_url,
                document_type=document_type,
                title=title,
                description=description,
                tags=tags or [],
                amount=amount,
                date=document_date,
                vendor=vendor,
                status=DocumentStatus.ACTIVE
            )
            
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
            
            return document
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create document record: {str(e)}"
            )
    
    def get_document_by_id(self, document_id: int, account_id: int) -> Optional[Document]:
        """Get document by ID for a specific account."""
        return self.db.query(Document).filter(
            and_(
                Document.id == document_id,
                Document.account_id == account_id,
                Document.status != DocumentStatus.DELETED
            )
        ).first()
    
    def get_document_by_s3_key(self, s3_key: str) -> Optional[Document]:
        """Get document by S3 key."""
        return self.db.query(Document).filter(
            and_(
                Document.s3_key == s3_key,
                Document.status != DocumentStatus.DELETED
            )
        ).first()
    
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
        query = self.db.query(Document).filter(
            and_(
                Document.account_id == account_id,
                Document.status != DocumentStatus.DELETED
            )
        )
        
        if document_type:
            query = query.filter(Document.document_type == document_type)
        
        if vehicle_id:
            query = query.filter(Document.vehicle_id == vehicle_id)
        
        if trip_id:
            query = query.filter(Document.trip_id == trip_id)
        
        if status:
            query = query.filter(Document.status == status)
        
        order_column = getattr(Document, order_by, Document.uploaded_at)
        if order_direction.lower() == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))
        
        return query.offset(offset).limit(limit).all()
    
    def search_documents(
        self,
        account_id: int,
        search_term: str,
        document_type: Optional[DocumentType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Document]:
        """Search documents by title, description, or filename."""
        query = self.db.query(Document).filter(
            and_(
                Document.account_id == account_id,
                Document.status != DocumentStatus.DELETED,
                or_(
                    Document.title.ilike(f"%{search_term}%"),
                    Document.description.ilike(f"%{search_term}%"),
                    Document.original_filename.ilike(f"%{search_term}%"),
                    Document.vendor.ilike(f"%{search_term}%")
                )
            )
        )
        
        if document_type:
            query = query.filter(Document.document_type == document_type)
        
        return query.offset(offset).limit(limit).all()
    
    def update_document(
        self,
        document_id: int,
        account_id: int,
        **updates
    ) -> Optional[Document]:
        """Update document fields."""
        try:
            document = self.get_document_by_id(document_id, account_id)
            if not document:
                return None
            
            allowed_fields = [
                'title', 'description', 'tags', 'amount', 'date', 'vendor',
                'vehicle_id', 'trip_id', 'document_type', 'status'
            ]
            
            for field, value in updates.items():
                if field in allowed_fields and hasattr(document, field):
                    setattr(document, field, value)
            
            document.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(document)
            
            return document
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update document: {str(e)}"
            )
    
    def delete_document(self, document_id: int, account_id: int) -> bool:
        """Soft delete document (mark as deleted)."""
        try:
            document = self.get_document_by_id(document_id, account_id)
            if not document:
                return False
            
            document.status = DocumentStatus.DELETED
            document.updated_at = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete document: {str(e)}"
            )
    
    def hard_delete_document(self, document_id: int, account_id: int) -> bool:
        """Permanently delete document from database."""
        try:
            document = self.get_document_by_id(document_id, account_id)
            if not document:
                return False
            
            self.db.delete(document)
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to permanently delete document: {str(e)}"
            )
    
    def get_documents_by_vehicle(self, vehicle_id: int, account_id: int) -> List[Document]:
        """Get all documents for a specific vehicle."""
        return self.db.query(Document).filter(
            and_(
                Document.vehicle_id == vehicle_id,
                Document.account_id == account_id,
                Document.status != DocumentStatus.DELETED
            )
        ).order_by(desc(Document.uploaded_at)).all()
    
    def get_documents_by_trip(self, trip_id: int, account_id: int) -> List[Document]:
        """Get all documents for a specific trip."""
        return self.db.query(Document).filter(
            and_(
                Document.trip_id == trip_id,
                Document.account_id == account_id,
                Document.status != DocumentStatus.DELETED
            )
        ).order_by(desc(Document.uploaded_at)).all()
    
    def get_document_stats(self, account_id: int) -> Dict[str, Any]:
        """Get document statistics for an account."""
        total_docs = self.db.query(Document).filter(
            and_(
                Document.account_id == account_id,
                Document.status != DocumentStatus.DELETED
            )
        ).count()
        
        type_counts = {}
        for doc_type in DocumentType:
            count = self.db.query(Document).filter(
                and_(
                    Document.account_id == account_id,
                    Document.document_type == doc_type,
                    Document.status != DocumentStatus.DELETED
                )
            ).count()
            type_counts[doc_type.value] = count
        
        total_size = self.db.query(Document.file_size).filter(
            and_(
                Document.account_id == account_id,
                Document.status != DocumentStatus.DELETED
            )
        ).all()
        
        total_storage = sum(size[0] for size in total_size if size[0])
        
        return {
            'total_documents': total_docs,
            'total_storage_bytes': total_storage,
            'total_storage_mb': round(total_storage / (1024 * 1024), 2),
            'by_type': type_counts
        }
    
    def update_last_accessed(self, document_id: int, account_id: int) -> bool:
        """Update last accessed timestamp."""
        try:
            document = self.get_document_by_id(document_id, account_id)
            if not document:
                return False
            
            document.last_accessed_at = datetime.utcnow()
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            return False

# ------------------------------ END OF FILE ------------------------------
