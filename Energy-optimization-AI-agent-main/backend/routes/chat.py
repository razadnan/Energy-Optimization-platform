from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional
from analytics.usage_analysis import UsageAnalyzer
from models.forecasting import ForecastingModel
from models.anomaly_detection import AnomalyDetectionModel
from services.recommendation_engine import RecommendationEngine
from agents.insight_agent import InsightAgent
from services.chat_service import ChatService
from schemas.api_schemas import ChatRequestSchema, ChatResponseSchema
from backend.cache import CacheManager
from backend.database import DatabaseManager
from utils.helpers import convert_numpy_types
import logging

logger = logging.getLogger("ChatRoute")

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

_chat_service = ChatService()


def _load_all_reports(dataset_id: Optional[int]) -> dict:
    """
    Reuses whatever's already cached for the specific dataset.
    """
    usage_key = f"dataset_{dataset_id}_usage" if dataset_id else "usage"
    usage = CacheManager.get(usage_key)
    if not usage:
        usage = convert_numpy_types(UsageAnalyzer(dataset_id=dataset_id).generate_report())
        CacheManager.set(usage_key, usage)

    forecast_key = f"dataset_{dataset_id}_forecast" if dataset_id else "forecast"
    forecast = CacheManager.get(forecast_key)
    if not forecast:
        forecast = convert_numpy_types(ForecastingModel(dataset_id=dataset_id).run_pipeline())
        CacheManager.set(forecast_key, forecast)

    anomaly_key = f"dataset_{dataset_id}_anomaly" if dataset_id else "anomaly"
    anomaly = CacheManager.get(anomaly_key)
    if not anomaly:
        anomaly = convert_numpy_types(AnomalyDetectionModel(dataset_id=dataset_id).run_pipeline())
        CacheManager.set(anomaly_key, anomaly)

    recommendation_key = f"dataset_{dataset_id}_recommendations" if dataset_id else "recommendations"
    recommendation = CacheManager.get(recommendation_key)
    if not recommendation:
        engine = RecommendationEngine(usage, forecast, anomaly, dataset_id=dataset_id)
        recommendation = convert_numpy_types(engine.run_pipeline())
        CacheManager.set(recommendation_key, recommendation)

    insight_key = f"dataset_{dataset_id}_insight" if dataset_id else "insight"
    insight = CacheManager.get(insight_key)
    if not insight:
        insight = InsightAgent().execute({
            "usage": usage,
            "forecast": forecast,
            "anomaly": anomaly,
            "recommendation": recommendation,
        })
        CacheManager.set(insight_key, insight)

    return {
        "usage": usage,
        "forecast": forecast,
        "anomaly": anomaly,
        "recommendation": recommendation,
        "insight": insight,
    }


@router.post("/", response_model=ChatResponseSchema)
def post_chat(
    request: ChatRequestSchema,
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

        reports = _load_all_reports(active_dataset_id)
        history = [turn.model_dump() for turn in request.history]

        result = _chat_service.answer(request.message, history, reports)
        return result
    except Exception as e:
        logger.error(f"Error handling chat message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
