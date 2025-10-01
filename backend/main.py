# ------------------------------ IMPORTS ------------------------------
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime

# Import core components
from core.config.settings import settings

# Import domain routers
from turo.routes import router as turo_router
from plaid.routes import router as plaid_router
# from bouncie.routes import router as bouncie_router  # TODO: Implement when ready

# ------------------------------ LOGGING ------------------------------
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ------------------------------ LIFECYCLE MANAGEMENT ------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("🚀 Starting Turolytics API...")
    yield
    logger.info("🛑 Shutting down Turolytics API...")

# ------------------------------ FASTAPI APP ------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    description="Turo fleet analytics and data scraping API - Portfolio Project",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    debug=settings.DEBUG
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# ------------------------------ HEALTH ENDPOINTS ------------------------------
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Turolytics API - Portfolio Project",
        "version": settings.APP_VERSION,
        "description": "Turo fleet analytics and data scraping API",
        "features": [
            "Automated Turo data scraping",
            "Real-time vehicle tracking", 
            "Financial analytics",
            "Customer review analysis"
        ],
        "integrations": {
            "enabled": settings.get_enabled_integrations()
        },
        "endpoints": {
            "health": "/health",
            "turo": "/api/turo/*",
            "plaid": "/api/plaid/*",
            "bouncie": "/api/bouncie/*"  # TODO: Implement when ready
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        from core.db import get_db
        from sqlalchemy import text
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        database_status = "connected"
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        database_status = "disconnected"
    
    return {
        "status": "healthy",
        "service": "Turolytics API",
        "database": database_status,
        "timestamp": datetime.utcnow().isoformat()
    }

# ------------------------------ INCLUDE ROUTERS ------------------------------
# Include domain routers
app.include_router(turo_router, prefix="/api")
app.include_router(plaid_router, prefix="/api")
# app.include_router(bouncie_router, prefix="/api")  # TODO: Implement when ready

# ------------------------------ MAIN EXECUTION ------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
