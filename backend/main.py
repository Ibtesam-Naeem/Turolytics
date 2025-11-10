# ------------------------------ IMPORTS ------------------------------
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging

load_dotenv()

from turo.routes import router as turo_router
from core.config.settings import settings
from core.database import init_db

# ------------------------------ LOGGING ------------------------------
logger = logging.getLogger(__name__)

# ------------------------------ LIFESPAN EVENTS ------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")
    
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    yield

# ------------------------------ FASTAPI APP ------------------------------
app = FastAPI(
    title="Turolytics API",
    description="Backend API for Turolytics",
    version="1.0.0",
    lifespan=lifespan
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

# ------------------------------ HEALTH ENDPOINT ------------------------------
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Turolytics API", "status": "running"}

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy"
    }

# ------------------------------ MAIN ------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ------------------------------ END OF FILE ------------------------------