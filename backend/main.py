# ------------------------------ IMPORTS ------------------------------
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from dotenv import load_dotenv

load_dotenv()

from turo.routes import router as turo_router

# ------------------------------ LOGGING ------------------------------
logging.basicConfig(level=logging.INFO)

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