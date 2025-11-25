# ------------------------------ IMPORTS ------------------------------
import boto3
from botocore.exceptions import ClientError
from typing import Optional, Tuple, List
import uuid
import logging
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from core.config.settings import settings
from core.database.models.s3 import Document, DocumentCategory
from core.database.models.account import Account
from core.database.db_service import DatabaseService

# ------------------------------ CONSTANTS ------------------------------

ALLOWED_FILE_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp",
    "application/pdf",
    "application/msword",  # .doc
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/vnd.ms-excel",  # .xls
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "text/plain", "text/csv",
    "application/zip", "application/x-zip-compressed",
}

logger = logging.getLogger(__name__)

# ------------------------------ S3 SERVICE ------------------------------

class S3Service:
    """Service for S3 operations (upload, download, delete)."""
    
    def __init__(self, db: Session):
        self.db = db
        self.s3_client = self._create_s3_client()
        self.bucket_name = settings.s3.bucket_name
        self.max_file_size = settings.s3.max_file_size_mb * 1024 * 1024 
        
        if not self.bucket_name:
            raise ValueError("S3 bucket name is not configured. Please set S3_BUCKET_NAME environment variable.")
    
    def _create_s3_client(self):
        """Create and return S3 client."""
        client_config = {'region_name': settings.s3.region}
        
        if settings.s3.endpoint_url:
            client_config['endpoint_url'] = settings.s3.endpoint_url
        
        if settings.s3.access_key_id and settings.s3.secret_access_key:
            return boto3.client(
                's3',
                aws_access_key_id=settings.s3.access_key_id,
                aws_secret_access_key=settings.s3.secret_access_key,
                **client_config
            )
        else:
            return boto3.client('s3', **client_config)
    
    def _get_account(self, account_id: int) -> Account:
        """Get account by ID or user_id, raise ValueError if not found."""
        account = self.db.query(Account).filter(Account.id == account_id).first()
        
        if not account:
            account = DatabaseService.get_account_by_user_id(self.db, account_id)
        
        if not account:
            raise ValueError(f"Account {account_id} not found")
        return account
    
    def get_document(self, document_id: int, account_id: int) -> Document:
        """Get document by ID and account_id, raise ValueError if not found."""
        account = self._get_account(account_id)
        document = self.db.query(Document).filter(
            Document.id == document_id,
            Document.account_id == account.id
        ).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")
        return document
    
    def _generate_s3_key(self, account_id: int, file_name: str) -> str:
        """Generate unique S3 key for file."""
        file_ext = Path(file_name).suffix
        unique_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime("%Y/%m/%d")
        return f"documents/{account_id}/{timestamp}/{unique_id}{file_ext}"
    
    def upload_file(
        self,
        file_content: bytes,
        file_name: str,
        file_type: str,
        account_id: int,
        category: DocumentCategory,
        vehicle_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> Document:
        """Upload file to S3 and create database record."""
        
        file_size = len(file_content)
        if file_size > self.max_file_size:
            raise ValueError(f"File size ({file_size / 1024 / 1024:.2f} MB) exceeds maximum allowed size ({settings.s3.max_file_size_mb} MB)")
        
        if file_size == 0:
            raise ValueError("File is empty")
        
        if file_type and file_type.lower() not in [ft.lower() for ft in ALLOWED_FILE_TYPES]:
            raise ValueError(f"File type '{file_type}' is not allowed. Allowed types: {', '.join(sorted(ALLOWED_FILE_TYPES))}")
        
        account = self._get_account(account_id)
        
        if vehicle_id:
            from core.database.models.turo.vehicle import Vehicle
            vehicle = self.db.query(Vehicle).filter(
                Vehicle.id == vehicle_id,
                Vehicle.account_id == account.id
            ).first()
            if not vehicle:
                raise ValueError(f"Vehicle {vehicle_id} not found for account {account_id}")
        
        s3_key = self._generate_s3_key(account.id, file_name)
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=file_type
            )
            
            logger.info(f"Uploaded file to S3: {s3_key}")
            
            document = Document(
                account_id=account.id,
                vehicle_id=vehicle_id,
                file_name=file_name,
                file_type=file_type,
                file_size=file_size,
                s3_key=s3_key,
                s3_bucket=self.bucket_name,
                category=category,
                description=description
            )
            
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
            
            logger.info(f"Created document record: {document.id}")
            return document
        
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            self.db.rollback()
            raise ValueError(f"Failed to upload file to S3: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            self.db.rollback()
            raise
    
    def download_file(self, document_id: int, account_id: int) -> Tuple[bytes, str, str]:
        """Download file from S3."""
        document = self.get_document(document_id, account_id)
        
        try:
            response = self.s3_client.get_object(
                Bucket=document.s3_bucket,
                Key=document.s3_key
            )
            
            file_content = response['Body'].read()
            return file_content, document.file_name, document.file_type or 'application/octet-stream'
        
        except ClientError as e:
            logger.error(f"S3 download error: {e}")
            raise ValueError(f"Failed to download file from S3: {str(e)}")
    
    def delete_file(self, document_id: int, account_id: int) -> bool:
        """Delete file from S3 and database."""
        document = self.get_document(document_id, account_id)
        
        try:
            self.s3_client.delete_object(
                Bucket=document.s3_bucket,
                Key=document.s3_key
            )
            
            self.db.delete(document)
            self.db.commit()
            
            logger.info(f"Deleted document {document_id} from S3 and database")
            return True
        
        except ClientError as e:
            logger.error(f"S3 delete error: {e}")
            self.db.rollback()
            raise ValueError(f"Failed to delete file from S3: {str(e)}")
    
    def get_presigned_url(self, document_id: int, account_id: int, expiration: int = 3600) -> str:
        """Generate presigned URL for file access."""
        document = self.get_document(document_id, account_id)
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': document.s3_bucket,
                    'Key': document.s3_key
                },
                ExpiresIn=expiration
            )
            return url
        
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise ValueError(f"Failed to generate presigned URL: {str(e)}")
    
    def list_documents(
        self,
        account_id: int,
        vehicle_id: Optional[int] = None,
        category: Optional[DocumentCategory] = None,
        search: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Document], int]:
        """List documents with filtering and pagination."""
        account = self._get_account(account_id)
        
        query = self.db.query(Document).filter(Document.account_id == account.id)
        
        if vehicle_id is not None:
            query = query.filter(Document.vehicle_id == vehicle_id)
        
        if category:
            query = query.filter(Document.category == category)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Document.file_name.ilike(search_pattern),
                    Document.description.ilike(search_pattern)
                )
            )
        
        if start_date:
            query = query.filter(Document.created_at >= start_date)
        if end_date:
            query = query.filter(Document.created_at <= end_date)
        
        total = query.count()
        
        documents = query.order_by(desc(Document.created_at)).limit(limit).offset(offset).all()
        
        return documents, total
    
    def update_document(
        self,
        document_id: int,
        account_id: int,
        category: Optional[DocumentCategory] = None,
        vehicle_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> Document:
        """Update document metadata."""
        document = self.get_document(document_id, account_id)
        
        try:
            if category is not None:
                document.category = category
            if vehicle_id is not None:
                from core.database.models.turo.vehicle import Vehicle
                vehicle = self.db.query(Vehicle).filter(
                    Vehicle.id == vehicle_id,
                    Vehicle.account_id == document.account_id
                ).first()
                if not vehicle:
                    raise ValueError(f"Vehicle {vehicle_id} not found")
                document.vehicle_id = vehicle_id
            if description is not None:
                document.description = description
            
            self.db.commit()
            self.db.refresh(document)
            return document

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating document {document_id}: {e}")
            raise

# ------------------------------ END OF FILE ------------------------------

