# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter

from .auth import router as auth_router
from .matches import router as matches_router
from .mappings import router as mappings_router
from .live_data import router as live_data_router
from .webhooks import router as webhooks_router
from .dtc_codes import router as dtc_codes_router

# ------------------------------ COMBINE ALL ROUTERS ------------------------------

router = APIRouter()

router.include_router(auth_router)
router.include_router(matches_router)
router.include_router(mappings_router)
router.include_router(live_data_router)
router.include_router(webhooks_router)
router.include_router(dtc_codes_router)

# ------------------------------ END OF FILE ------------------------------