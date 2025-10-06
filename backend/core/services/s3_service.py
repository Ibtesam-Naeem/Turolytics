# ------------------------------ IMPORTS ------------------------------
import boto3
import uuid
import mimetypes
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, BinaryIO
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import HTTPException, UploadFile
import logging

from core.config.settings import settings

# ------------------------------ LOGGING ------------------------------
logger = logging.getLogger(__name__)

# ------------------------------ S3 SERVICE ------------------------------

class S3Service:
    """Service for handling S3 operations."""
    
    def __init__(self):
        """Initialize S3 service with configuration."""
        self.config = settings.s3
        self.s3_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize S3 client with credentials."""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.config.access_key_id,
                aws_secret_access_key=self.config.secret_access_key,
                region_name=self.config.region
            )
            logger.info("S3 client initialized successfully")
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise HTTPException(
                status_code=500,
                detail="AWS credentials not configured"
            )
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize S3 service"
            )
    
    def _validate_file(self, file: UploadFile) -> Dict[str, Any]:
        """Validate uploaded file."""
        if hasattr(file, 'size') and file.size > self.config.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {self.config.max_file_size} bytes"
            )
        
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Filename is required"
            )
        
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in self.config.get_allowed_extensions_list():
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(self.config.get_allowed_extensions_list())}"
            )
        
        content_type, _ = mimetypes.guess_type(file.filename)
        if not content_type:
            content_type = 'application/octet-stream'
        
        return {
            'extension': file_extension,
            'content_type': content_type
        }
    
    def _generate_s3_key(self, account_id: int, document_type: str, filename: str) -> str:
        """Generate unique S3 key for file."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"documents/{account_id}/{document_type}/{timestamp}_{unique_id}_{filename}"
    
    async def upload_file(
        self,
        file: UploadFile,
        account_id: int,
        document_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Upload file to S3 and return file information."""
        try:
            file_info = self._validate_file(file)
            
            s3_key = self._generate_s3_key(account_id, document_type, file.filename)
            
            s3_metadata = {
                'account_id': str(account_id),
                'document_type': document_type,
                'original_filename': file.filename,
                'uploaded_at': datetime.utcnow().isoformat()
            }
            
            if metadata:
                s3_metadata.update(metadata)
            
            file_content = await file.read()
            file_size = len(file_content)
            
            self.s3_client.put_object(
                Bucket=self.config.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=file_info['content_type'],
                Metadata=s3_metadata
            )
            
            s3_url = self._generate_presigned_url(s3_key)
            
            logger.info(f"File uploaded successfully: {s3_key}")
            
            return {
                'filename': file.filename,
                'original_filename': file.filename,
                'file_extension': file_info['extension'],
                'file_size': file_size,
                'content_type': file_info['content_type'],
                's3_bucket': self.config.bucket_name,
                's3_key': s3_key,
                's3_url': s3_url
            }
            
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload file to S3: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred during file upload"
            )
    
    def _generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        """Generate presigned URL for file access."""
        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.config.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return ""
    
    async def download_file(self, s3_key: str) -> Dict[str, Any]:
        """Download file from S3."""
        try:
            response = self.s3_client.get_object(
                Bucket=self.config.bucket_name,
                Key=s3_key
            )
            
            return {
                'content': response['Body'].read(),
                'content_type': response.get('ContentType', 'application/octet-stream'),
                'content_length': response.get('ContentLength', 0),
                'last_modified': response.get('LastModified'),
                'metadata': response.get('Metadata', {})
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise HTTPException(
                    status_code=404,
                    detail="File not found"
                )
            logger.error(f"S3 download error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to download file from S3: {str(e)}"
            )
    
    async def delete_file(self, s3_key: str) -> bool:
        """Delete file from S3."""
        try:
            self.s3_client.delete_object(
                Bucket=self.config.bucket_name,
                Key=s3_key
            )
            logger.info(f"File deleted successfully: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"S3 delete error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete file from S3: {str(e)}"
            )
    
    async def list_files(self, account_id: int, prefix: str = "documents/") -> List[Dict[str, Any]]:
        """List files for an account."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.config.bucket_name,
                Prefix=f"{prefix}{account_id}/"
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'url': self._generate_presigned_url(obj['Key'])
                })
            
            return files
            
        except ClientError as e:
            logger.error(f"S3 list error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list files from S3: {str(e)}"
            )
    
    async def get_file_metadata(self, s3_key: str) -> Dict[str, Any]:
        """Get file metadata from S3."""
        try:
            response = self.s3_client.head_object(
                Bucket=self.config.bucket_name,
                Key=s3_key
            )
            
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'metadata': response.get('Metadata', {}),
                'etag': response.get('ETag')
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise HTTPException(
                    status_code=404,
                    detail="File not found"
                )
            logger.error(f"S3 metadata error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get file metadata from S3: {str(e)}"
            )
    
    def test_connection(self) -> bool:
        """Test S3 connection."""
        try:
            self.s3_client.head_bucket(Bucket=self.config.bucket_name)
            return True
        except ClientError as e:
            logger.error(f"S3 connection test failed: {e}")
            return False

# ------------------------------ GLOBAL INSTANCE ------------------------------
s3_service = S3Service()

# ------------------------------ END OF FILE ------------------------------
