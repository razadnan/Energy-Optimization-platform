from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional
from models.anomaly_detection import AnomalyDetectionModel
from schemas.api_schemas import AnomalyReportSchema
from backend.cache import CacheManager
from backend.database import DatabaseManager
from utils.helpers import convert_numpy_types
import logging

logger = logging.getLogger("AnomalyRoute")

router = APIRouter(
    prefix="/anomaly",
    tags=["Anomaly Detection"]
)


@router.get("/", response_model=AnomalyReportSchema)
def get_anomaly(
    x_dataset_id: Optional[int] = Header(None),
    dataset_id: Optional[int] = Query(None),
    x_user_id: Optional[int] = Header(None),
    user_id: Optional[int] = Query(None)
):
    try:
        active_dataset_id = x_dataset_id or dataset_id
        active_user_id = x_user_id or user_id

        # Resolve active dataset ID if not explicitly provided
        if not active_dataset_id:
            active_dataset_id = DatabaseManager.get_active_dataset_id(active_user_id)

        # Check cache for this dataset ID
        cache_key = f"dataset_{active_dataset_id}_anomaly" if active_dataset_id else "anomaly"
        cached_data = CacheManager.get(cache_key, max_age_seconds=43200)
        if cached_data:
            return cached_data

        # Compute
        model = AnomalyDetectionModel(dataset_id=active_dataset_id)
        report = convert_numpy_types(model.run_pipeline())
        
        # Save cache
        CacheManager.set(cache_key, report)
        return report
    except Exception as e:
        logger.error(f"Error generating anomaly report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))