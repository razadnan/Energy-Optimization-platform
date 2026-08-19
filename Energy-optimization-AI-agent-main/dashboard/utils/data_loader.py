import requests
import streamlit as st
from analytics.usage_analysis import UsageAnalyzer
from models.forecasting import ForecastingModel
from models.anomaly_detection import AnomalyDetectionModel
from services.recommendation_engine import RecommendationEngine
from services.report_generator import ReportGenerator
from agents.insight_agent import InsightAgent
from services.chat_service import ChatService
from backend.cache import CacheManager
from dashboard.utils.helpers import convert_numpy_types

API_BASE_URL = "http://127.0.0.1:8000"


def get_auth_headers():
    """Build authorization and tenant context headers from session state."""
    headers = {}
    if "user" in st.session_state and st.session_state["user"]:
        headers["X-User-ID"] = str(st.session_state["user"]["id"])
    if "active_dataset_id" in st.session_state and st.session_state["active_dataset_id"]:
        headers["X-Dataset-ID"] = str(st.session_state["active_dataset_id"])
    return headers


@st.cache_data(ttl=3600)
def load_usage_data(dataset_id: int = None):
    headers = get_auth_headers()
    # Explicitly append dataset_id as query parameter if passed
    params = {"dataset_id": dataset_id} if dataset_id else {}
    try:
        response = requests.get(f"{API_BASE_URL}/usage", headers=headers, params=params, timeout=3)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    
    # Fallback to direct calculation
    cache_key = f"dataset_{dataset_id}_usage" if dataset_id else "usage"
    cached = CacheManager.get(cache_key)
    if cached:
        return cached
    try:
        analyzer = UsageAnalyzer(dataset_id=dataset_id)
        report = convert_numpy_types(analyzer.generate_report())
        CacheManager.set(cache_key, report)
        return report
    except Exception:
        return None


@st.cache_data(ttl=3600)
def load_forecast_data(dataset_id: int = None):
    headers = get_auth_headers()
    params = {"dataset_id": dataset_id} if dataset_id else {}
    try:
        response = requests.get(f"{API_BASE_URL}/forecast", headers=headers, params=params, timeout=3)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    
    # Fallback to direct calculation
    cache_key = f"dataset_{dataset_id}_forecast" if dataset_id else "forecast"
    cached = CacheManager.get(cache_key)
    if cached:
        return cached
    try:
        model = ForecastingModel(dataset_id=dataset_id)
        report = convert_numpy_types(model.run_pipeline())
        CacheManager.set(cache_key, report)
        return report
    except Exception:
        return None


@st.cache_data(ttl=3600)
def load_anomaly_data(dataset_id: int = None):
    headers = get_auth_headers()
    params = {"dataset_id": dataset_id} if dataset_id else {}
    try:
        response = requests.get(f"{API_BASE_URL}/anomaly", headers=headers, params=params, timeout=3)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    
    # Fallback to direct calculation
    cache_key = f"dataset_{dataset_id}_anomaly" if dataset_id else "anomaly"
    cached = CacheManager.get(cache_key)
    if cached:
        return cached
    try:
        model = AnomalyDetectionModel(dataset_id=dataset_id)
        report = convert_numpy_types(model.run_pipeline())
        CacheManager.set(cache_key, report)
        return report
    except Exception:
        return None


@st.cache_data(ttl=3600)
def load_recommendation_data(dataset_id: int = None):
    headers = get_auth_headers()
    params = {"dataset_id": dataset_id} if dataset_id else {}
    try:
        response = requests.get(f"{API_BASE_URL}/recommendations", headers=headers, params=params, timeout=3)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    
    # Fallback to direct calculation
    cache_key = f"dataset_{dataset_id}_recommendations" if dataset_id else "recommendations"
    cached = CacheManager.get(cache_key)
    if cached:
        return cached
    try:
        usage = load_usage_data(dataset_id=dataset_id)
        forecast = load_forecast_data(dataset_id=dataset_id)
        anomaly = load_anomaly_data(dataset_id=dataset_id)
        if not usage or not forecast or not anomaly:
            return None
        engine = RecommendationEngine(usage, forecast, anomaly, dataset_id=dataset_id)
        report = convert_numpy_types(engine.run_pipeline())
        CacheManager.set(cache_key, report)
        return report
    except Exception:
        return None


@st.cache_data(ttl=3600)
def load_insight_data(dataset_id: int = None):
    headers = get_auth_headers()
    params = {"dataset_id": dataset_id} if dataset_id else {}
    try:
        response = requests.get(f"{API_BASE_URL}/insights", headers=headers, params=params, timeout=3)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass

    # Fallback to direct calculation
    cache_key = f"dataset_{dataset_id}_insight" if dataset_id else "insight"
    cached = CacheManager.get(cache_key)
    if cached:
        return cached
    try:
        usage = load_usage_data(dataset_id=dataset_id)
        forecast = load_forecast_data(dataset_id=dataset_id)
        anomaly = load_anomaly_data(dataset_id=dataset_id)
        recommendation = load_recommendation_data(dataset_id=dataset_id)
        if not usage or not forecast or not anomaly or not recommendation:
            return None
        data = {
            "usage": usage,
            "forecast": forecast,
            "anomaly": anomaly,
            "recommendation": recommendation
        }
        report = InsightAgent().execute(data)
        CacheManager.set(cache_key, report)
        return report
    except Exception:
        return None


@st.cache_data(ttl=3600)
def load_reports_data(dataset_id: int = None):
    headers = get_auth_headers()
    params = {"dataset_id": dataset_id} if dataset_id else {}
    try:
        response = requests.get(f"{API_BASE_URL}/reports", headers=headers, params=params, timeout=3)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    
    # Fallback to direct calculation
    cache_key = f"dataset_{dataset_id}_report" if dataset_id else "report"
    cached = CacheManager.get(cache_key)
    if cached:
        return cached
    try:
        usage = load_usage_data(dataset_id=dataset_id)
        forecast = load_forecast_data(dataset_id=dataset_id)
        anomaly = load_anomaly_data(dataset_id=dataset_id)
        recommendation = load_recommendation_data(dataset_id=dataset_id)
        insight = load_insight_data(dataset_id=dataset_id)
        if not usage or not forecast or not anomaly or not recommendation or not insight:
            return None
        data = {
            "usage": usage,
            "forecast": forecast,
            "anomaly": anomaly,
            "recommendation": recommendation,
            "insight": insight
        }
        generator = ReportGenerator(data)
        report = convert_numpy_types(generator.generate_report())
        CacheManager.set(cache_key, report)
        return report
    except Exception:
        return None


def send_chat_message(message: str, history: list, dataset_id: int = None) -> dict:
    headers = get_auth_headers()
    params = {"dataset_id": dataset_id} if dataset_id else {}
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat/",
            json={"message": message, "history": history},
            headers=headers,
            params=params,
            timeout=15,
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass

    # Fallback to direct in-process call
    reports = {
        "usage": load_usage_data(dataset_id=dataset_id),
        "forecast": load_forecast_data(dataset_id=dataset_id),
        "anomaly": load_anomaly_data(dataset_id=dataset_id),
        "recommendation": load_recommendation_data(dataset_id=dataset_id),
        "insight": load_insight_data(dataset_id=dataset_id),
    }
    return ChatService().answer(message, history, reports)


def check_active_dataset_status():
    """Checks the status of the active dataset. If not completed, renders warning/error and stops page execution."""
    active_id = st.session_state.get("active_dataset_id")
    if not active_id:
        return
    
    from backend.database import DatabaseManager
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT status, error_message, filename FROM datasets WHERE id = ?", (active_id,))
        row = cursor.fetchone()
        if row:
            status, err, filename = row
            if status in ["uploading", "cleaning", "processing"]:
                st.warning(f"⏳ The dataset `{filename}` is currently being processed by the AI pipeline (Status: **{status}**).")
                st.info("The dashboard will unlock once processing is complete. Please wait...")
                if st.button("🔄 Refresh Status", use_container_width=True):
                    st.rerun()
                st.stop()
            elif status == "failed":
                st.error(f"❌ The AI pipeline failed to process the dataset `{filename}`.")
                if err:
                    st.error(f"**Error Details:** {err}")
                st.info("Please upload a new valid dataset on the **Input Data** page.")
                st.stop()
    except Exception as e:
        st.error(f"Error checking dataset status: {e}")
    finally:
        conn.close()
