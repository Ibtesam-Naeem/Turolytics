#!/usr/bin/env python3
"""
Turolytics Backend API
Main FastAPI application entry point.
"""

# ------------------------------ IMPORTS ------------------------------
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from turo.routes import router as turo_router
from bouncie.routes import router as bouncie_router

# ------------------------------ LOGGING ------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# ------------------------------ HEALTH ENDPOINT ------------------------------
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Turolytics API", "status": "running"}

@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)