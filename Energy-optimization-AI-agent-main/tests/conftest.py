"""
Shared pytest fixtures for the Energy Optimization Agent test suite.

Model fitting (Prophet / Isolation Forest) is expensive, so session-scoped
fixtures compute each report once per test run and reuse the on-disk
CacheManager so repeated `pytest` invocations stay fast too.
"""

import sys
from pathlib import Path
root_path = str(Path(__file__).resolve().parent.parent)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

import pytest

from analytics.usage_analysis import UsageAnalyzer
from models.forecasting import ForecastingModel
from models.anomaly_detection import AnomalyDetectionModel
from services.recommendation_engine import RecommendationEngine
from agents.insight_agent import InsightAgent
from services.report_generator import ReportGenerator
from backend.cache import CacheManager
from utils.helpers import convert_numpy_types


@pytest.fixture(scope="session")
def usage_report():
    cached = CacheManager.get("usage")
    if cached:
        return cached
    report = convert_numpy_types(UsageAnalyzer().generate_report())
    CacheManager.set("usage", report)
    return report


@pytest.fixture(scope="session")
def forecast_report():
    cached = CacheManager.get("forecast", max_age_seconds=43200)
    if cached:
        return cached
    report = convert_numpy_types(ForecastingModel().run_pipeline())
    CacheManager.set("forecast", report)
    return report


@pytest.fixture(scope="session")
def anomaly_report():
    cached = CacheManager.get("anomaly", max_age_seconds=43200)
    if cached:
        return cached
    report = convert_numpy_types(AnomalyDetectionModel().run_pipeline())
    CacheManager.set("anomaly", report)
    return report


@pytest.fixture(scope="session")
def recommendation_report(usage_report, forecast_report, anomaly_report):
    cached = CacheManager.get("recommendations")
    if cached:
        return cached
    engine = RecommendationEngine(usage_report, forecast_report, anomaly_report)
    report = convert_numpy_types(engine.run_pipeline())
    CacheManager.set("recommendations", report)
    return report


@pytest.fixture(scope="session")
def insight_report(usage_report, forecast_report, anomaly_report, recommendation_report):
    cached = CacheManager.get("insight")
    if cached:
        return cached
    report = InsightAgent().execute({
        "usage": usage_report,
        "forecast": forecast_report,
        "anomaly": anomaly_report,
        "recommendation": recommendation_report,
    })
    CacheManager.set("insight", report)
    return report


@pytest.fixture(scope="session")
def reporting_report(usage_report, forecast_report, anomaly_report, recommendation_report, insight_report):
    cached = CacheManager.get("report")
    if cached:
        return cached
    generator = ReportGenerator({
        "usage": usage_report,
        "forecast": forecast_report,
        "anomaly": anomaly_report,
        "recommendation": recommendation_report,
        "insight": insight_report,
    })
    report = convert_numpy_types(generator.generate_report())
    CacheManager.set("report", report)
    return report
