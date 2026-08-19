from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional
from analytics.usage_analysis import UsageAnalyzer
from models.forecasting import ForecastingModel
from models.anomaly_detection import AnomalyDetectionModel
from services.recommendation_engine import RecommendationEngine
from schemas.api_schemas import RecommendationReportSchema
from backend.cache import CacheManager
from backend.database import DatabaseManager
from utils.helpers import convert_numpy_types
import logging

logger = logging.getLogger("RecommendationRoute")

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)


@router.get("/", response_model=RecommendationReportSchema)
def get_recommendations(
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
        cache_key = f"dataset_{active_dataset_id}_recommendations" if active_dataset_id else "recommendations"
        cached_data = CacheManager.get(cache_key)
        if cached_data:
            return cached_data

        # Load inputs from cache or compute them per dataset
        usage_key = f"dataset_{active_dataset_id}_usage" if active_dataset_id else "usage"
        usage = CacheManager.get(usage_key)
        if not usage:
            usage = convert_numpy_types(UsageAnalyzer(dataset_id=active_dataset_id).generate_report())
            CacheManager.set(usage_key, usage)

        forecast_key = f"dataset_{active_dataset_id}_forecast" if active_dataset_id else "forecast"
        forecast = CacheManager.get(forecast_key)
        if not forecast:
            forecast = convert_numpy_types(ForecastingModel(dataset_id=active_dataset_id).run_pipeline())
            CacheManager.set(forecast_key, forecast)

        anomaly_key = f"dataset_{active_dataset_id}_anomaly" if active_dataset_id else "anomaly"
        anomaly = CacheManager.get(anomaly_key)
        if not anomaly:
            anomaly = convert_numpy_types(AnomalyDetectionModel(dataset_id=active_dataset_id).run_pipeline())
            CacheManager.set(anomaly_key, anomaly)

        # Run engine
        engine = RecommendationEngine(usage, forecast, anomaly, dataset_id=active_dataset_id)
        report = convert_numpy_types(engine.run_pipeline())

        # Save cache
        CacheManager.set(cache_key, report)
        return report
    except Exception as e:
        logger.error(f"Error generating recommendation report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))