# ------------------------------ IMPORTS ------------------------------
from datetime import datetime
from fastapi import HTTPException
import json
from core.db.base import DocumentType, DocumentStatus

# ------------------------------ HELPER FUNCTIONS ------------------------------

def parse_tags(raw: str | None):
    """Parse JSON tags string into list."""
    if not raw: 
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid tags format (must be JSON array)")

def parse_date(raw: str | None):
    """Parse ISO date string into datetime."""
    if not raw: 
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(400, "Invalid document_date (use ISO format)")

def parse_enum(enum_cls, value: str | None):
    """Parse string into enum value."""
    if not value: 
        return None
    try:
        return enum_cls(value)
    except ValueError:
        raise HTTPException(400, f"Invalid {enum_cls.__name__}: {value}")

def to_response(doc):
    """Map SQLAlchemy model → Pydantic response."""
    from documents.routes import DocumentResponse
    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        original_filename=doc.original_filename,
        file_extension=doc.file_extension,
        file_size=doc.file_size,
        content_type=doc.content_type,
        document_type=doc.document_type.value,
        title=doc.title,
        description=doc.description,
        tags=doc.tags,
        vehicle_id=doc.vehicle_id,
        trip_id=doc.trip_id,
        amount=float(doc.amount) if doc.amount else None,
        date=doc.date,
        vendor=doc.vendor,
        status=doc.status.value,
        uploaded_at=doc.uploaded_at,
        last_accessed_at=doc.last_accessed_at,
        s3_url=doc.s3_url,
    )

# ------------------------------ DECORATORS ------------------------------

def safe_route(fn):
    """Decorator to handle common error patterns."""
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, f"Server error: {e}")
    return wrapper

# ------------------------------ END OF FILE ------------------------------
