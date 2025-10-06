# ------------------------------ IMPORTS ------------------------------
import asyncio
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging

from .service import MLService

logger = logging.getLogger(__name__)

# ------------------------------ HELPER FUNCTIONS ------------------------------

def check_result(result: Dict[str, Any], operation: str) -> Dict[str, Any]:
    """Check API result and raise HTTPException if failed."""
    if not result.get("success", False):
        error_msg = result.get("error", "Unknown error")
        logger.error(f"ML {operation} failed: {error_msg}")
        raise HTTPException(status_code=400, detail=f"ML {operation} failed: {error_msg}")
    return result

# ------------------------------ PYDANTIC MODELS ------------------------------

class PredictionRequest(BaseModel):
    account_email: str
    imei: Optional[str] = None
    days_ahead: Optional[int] = 30

class ClusteringRequest(BaseModel):
    account_email: str
    imei: Optional[str] = None

class AnomalyRequest(BaseModel):
    account_email: str
    imei: Optional[str] = None

# ------------------------------ ROUTER SETUP ------------------------------
router = APIRouter(prefix="/sklearn", tags=["machine-learning"])

# ------------------------------ PREDICTIVE ANALYTICS ROUTES ------------------------------

@router.post("/predict/revenue")
async def predict_revenue(request: PredictionRequest):
    """Predict future Turo earnings using ML."""
    service = MLService()
    result = await service.predict_revenue(request.account_email, request.days_ahead)
    return check_result(result, "revenue prediction")

@router.post("/optimize/trips")
async def optimize_trips(request: ClusteringRequest):
    """Suggest optimal times and locations for trips."""
    service = MLService()
    result = await service.optimize_trips(request.account_email, request.imei)
    return check_result(result, "trip optimization")

@router.post("/predict/maintenance")
async def predict_maintenance(request: ClusteringRequest):
    """Predict vehicle maintenance needs using Bouncie data."""
    service = MLService()
    result = await service.predict_maintenance(request.account_email, request.imei)
    return check_result(result, "maintenance prediction")

# ------------------------------ CLUSTERING ROUTES ------------------------------

@router.post("/cluster/trip-patterns")
async def cluster_trip_patterns(request: ClusteringRequest):
    """Group similar trips using clustering."""
    service = MLService()
    result = await service.cluster_trip_patterns(request.account_email, request.imei)
    return check_result(result, "trip pattern clustering")

@router.post("/cluster/vehicles")
async def categorize_vehicles(request: ClusteringRequest):
    """Categorize vehicles by usage patterns."""
    service = MLService()
    result = await service.categorize_vehicles(request.account_email)
    return check_result(result, "vehicle categorization")

@router.post("/cluster/geographic-hotspots")
async def analyze_geographic_hotspots(request: ClusteringRequest):
    """Identify geographic hotspots for rentals."""
    service = MLService()
    result = await service.analyze_geographic_hotspots(request.account_email)
    return check_result(result, "geographic hotspot analysis")

# ------------------------------ ANOMALY DETECTION ROUTES ------------------------------

@router.post("/anomaly/spending")
async def detect_spending_anomalies(request: AnomalyRequest):
    """Detect unusual spending patterns using Plaid data."""
    service = MLService()
    result = await service.detect_spending_anomalies(request.account_email)
    return check_result(result, "spending anomaly detection")

@router.post("/anomaly/vehicle-issues")
async def detect_vehicle_issues(request: AnomalyRequest):
    """Detect vehicle issues using Bouncie telemetry."""
    service = MLService()
    result = await service.detect_vehicle_issues(request.account_email, request.imei)
    return check_result(result, "vehicle issue detection")

@router.post("/anomaly/performance-outliers")
async def detect_performance_outliers(request: AnomalyRequest):
    """Detect performance outliers across all metrics."""
    service = MLService()
    result = await service.detect_performance_outliers(request.account_email)
    return check_result(result, "performance outlier detection")

# ------------------------------ COMBINED ANALYTICS ROUTES ------------------------------

@router.post("/analytics/comprehensive")
async def comprehensive_analytics(request: ClusteringRequest):
    """Get comprehensive ML analytics for an account."""
    service = MLService()
    
    results = await asyncio.gather(
        service.predict_revenue(request.account_email, 30),
        service.optimize_trips(request.account_email, request.imei),
        service.cluster_trip_patterns(request.account_email, request.imei),
        service.detect_spending_anomalies(request.account_email),
        return_exceptions=True
    )
    
    return {
        "success": True,
        "data": {
            "revenue_prediction": results[0] if not isinstance(results[0], Exception) else {"error": str(results[0])},
            "trip_optimization": results[1] if not isinstance(results[1], Exception) else {"error": str(results[1])},
            "trip_clustering": results[2] if not isinstance(results[2], Exception) else {"error": str(results[2])},
            "spending_anomalies": results[3] if not isinstance(results[3], Exception) else {"error": str(results[3])}
        }
    }

@router.get("/health")
async def ml_health_check():
    """Check ML service health and dependencies."""
    try:
        import sklearn
        import numpy as np
        import pandas as pd
        
        return {
            "success": True,
            "data": {
                "status": "healthy",
                "dependencies": {
                    "sklearn": sklearn.__version__,
                    "numpy": np.__version__,
                    "pandas": pd.__version__
                },
                "models_available": [
                    "RandomForestRegressor", "IsolationForest", "KMeans", 
                    "DBSCAN", "LinearRegression", "LocalOutlierFactor"
                ]
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"ML service unhealthy: {str(e)}"
        }

# ------------------------------ END OF FILE ------------------------------
