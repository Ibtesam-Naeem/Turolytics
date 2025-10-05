# ------------------------------ IMPORTS ------------------------------
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from turo.routes import router as turo_router
from bouncie.routes import router as bouncie_router
from plaid.routes import router as plaid_router
from core.db.database import create_tables, test_connection

# ------------------------------ LOGGING ------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------------ DATABASE INITIALIZATION ------------------------------
def initialize_database():
    """Initialize database tables on startup."""
    try:
        logger.info("Initializing database...")
        create_tables()
        test_connection()
        logger.info("Database initialized successfully!")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

initialize_database()

# ------------------------------ FASTAPI APP ------------------------------
app = FastAPI(
    title="Turolytics API",
    description="Backend API for Turolytics",
    version="1.0.0"
)

# ------------------------------ CORS MIDDLEWARE ------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------ ROUTERS ------------------------------
app.include_router(turo_router, prefix="/api")
app.include_router(bouncie_router, prefix="/api")
app.include_router(plaid_router, prefix="/api")

# ------------------------------ HEALTH ENDPOINT ------------------------------
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Turolytics API", "status": "running"}

@app.get("/health")
async def health():
    """Health check with database status."""
    try:
        test_connection()
        return {
            "status": "healthy",
            "database": "connected",
            "tables": "initialized"
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

# ------------------------------ MAIN ------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ------------------------------ END OF FILE ------------------------------