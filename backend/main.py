# ------------------------------ IMPORTS ------------------------------
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
import logging
import os
from typing import Optional

from core.database import init_db, get_db
from turo.routes import router as turo_router
from bouncie.routes import router as bouncie_router
from bouncie.service import BouncieService
from bouncie.auto_match import handle_bouncie_auto_processing
from s3.routes import router as s3_router
from sqlalchemy.orm import Session

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
app.include_router(s3_router, prefix="/api/documents", tags=["Documents"])

# ------------------------------ HELPER FUNCTIONS ------------------------------

def _build_redirect_url(error: Optional[str] = None, success: bool = False) -> str:
    """Build frontend redirect URL with query parameters."""
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8080")
    if success:
        return f"{frontend_url}/settings?bouncie_success=true"
    return f"{frontend_url}/settings?bouncie_error={error or 'unknown_error'}"

# ------------------------------ BOUNCIE OAUTH CALLBACK ------------------------------
@app.get("/auth/bouncie/callback", tags=["Bouncie"])
async def bouncie_oauth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Handle OAuth callback from Bouncie.
    Bouncie redirects here after user authorization.
    Exchanges code for tokens, saves to database, redirects to frontend.
    """
    if error:
        logger.error(f"Bouncie OAuth error: {error}")
        return RedirectResponse(url=_build_redirect_url(error=error))
    
    if not code:
        logger.error("Bouncie callback received without authorization code")
        return RedirectResponse(url=_build_redirect_url(error="no_code"))
    
    try:
        account_id = int(state) if state else None
    except (ValueError, TypeError):
        logger.warning(f"Invalid state parameter: {state}")
        account_id = None
    
    if not account_id:
        logger.error("Bouncie callback received without valid account_id in state")
        return RedirectResponse(url=_build_redirect_url(error="no_account"))
    
    try:
        service = BouncieService(db=db, account_id=account_id)
        result = await service.exchange_code_for_token(code)
        
        if result.get("success"):
            logger.info(f"Successfully saved Bouncie tokens for account {account_id}")
            await handle_bouncie_auto_processing(db, account_id)
            return RedirectResponse(url=_build_redirect_url(success=True))
        
        error_msg = result.get("error", "unknown_error")
        logger.error(f"Failed to exchange Bouncie token for account {account_id}: {error_msg}")
        return RedirectResponse(url=_build_redirect_url(error=error_msg))
    
    except Exception as e:
        logger.exception(f"Exception in Bouncie callback handler: {e}")
        return RedirectResponse(url=_build_redirect_url(error="server_error"))

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
