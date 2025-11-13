# ------------------------------ IMPORTS ------------------------------
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging

from core.database import init_db
from core.config.settings import settings
from turo.routes import router as turo_router
from bouncie.routes import router as bouncie_router

# ------------------------------ SETUP ------------------------------
load_dotenv()
logger = logging.getLogger("turolytics")

# ------------------------------ LIFESPAN ------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully\n")
   
    except Exception as e:
        logger.error(f"Database initialization failed: {e}\n")
    yield

# ------------------------------ APP ------------------------------
app = FastAPI(
    title="Turolytics API",
    description="Backend API for Turolytics",
    version="1.0.0",
    lifespan=lifespan,
)

# ------------------------------ CORS ------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------ ROUTERS ------------------------------
app.include_router(turo_router, prefix="/api/turo", tags=["Turo"])
app.include_router(bouncie_router, prefix="/api/bouncie", tags=["Bouncie"])

# ------------------------------ HEALTH ENDPOINTS ------------------------------
@app.get("/", tags=["Health"])
async def root():
    return {"message": "Turolytics API", "status": "running"}

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}

# ------------------------------ MAIN ------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# ------------------------------ END OF FILE ------------------------------
