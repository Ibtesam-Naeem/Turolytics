# ------------------------------ IMPORTS ------------------------------
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from core.database import init_db
from waitlist.routes import router as waitlist_router

# ------------------------------ SETUP ------------------------------
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()

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
# Get allowed origins from environment variable (comma-separated)
# For Railway deployment, set CORS_ORIGINS to your frontend URL(s)
# Example: CORS_ORIGINS=https://your-app.railway.app,https://your-custom-domain.com
cors_origins_env = os.getenv("CORS_ORIGINS", "*")
cors_origins_env = cors_origins_env.strip()

if cors_origins_env == "*":
    # In production, require explicit origins (never default to wildcard).
    if ENVIRONMENT == "production":
        raise ValueError(
            "CORS_ORIGINS must be set in production (comma-separated list of allowed origins)."
        )
    cors_origins = ["*"]
else:
    cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
    if ENVIRONMENT == "production" and not cors_origins:
        raise ValueError(
            "CORS_ORIGINS must include at least one origin in production."
        )

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    # If using wildcard origins, do not allow credentials (browsers will reject anyway).
    allow_credentials=cors_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------ ROUTERS ------------------------------
app.include_router(waitlist_router, prefix="/api", tags=["Waitlist"])

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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=ENVIRONMENT != "production")

# ------------------------------ END OF FILE ------------------------------
