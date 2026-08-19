import os
from fastapi import APIRouter, HTTPException, Header, Query
from fastapi.responses import FileResponse
from typing import Optional
from services.report_generator import ReportGenerator
from schemas.api_schemas import ReportingResponseSchema
from backend.cache import CacheManager
from backend.database import DatabaseManager
from analytics.usage_analysis import UsageAnalyzer
from models.forecasting import ForecastingModel
from models.anomaly_detection import AnomalyDetectionModel
from services.recommendation_engine import RecommendationEngine
from agents.insight_agent import InsightAgent
from utils.helpers import convert_numpy_types
from services.pdf_generator import PDFGenerator
import logging

logger = logging.getLogger("ReportsRoute")

router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)


@router.get("/", response_model=ReportingResponseSchema)
def get_reports(
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
        cache_key = f"dataset_{active_dataset_id}_report" if active_dataset_id else "report"
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

        recommendation_key = f"dataset_{active_dataset_id}_recommendations" if active_dataset_id else "recommendations"
        recommendation = CacheManager.get(recommendation_key)
        if not recommendation:
            engine = RecommendationEngine(usage, forecast, anomaly, dataset_id=active_dataset_id)
            recommendation = convert_numpy_types(engine.run_pipeline())
            CacheManager.set(recommendation_key, recommendation)

        insight_key = f"dataset_{active_dataset_id}_insight" if active_dataset_id else "insight"
        insight = CacheManager.get(insight_key)
        if not insight:
            insight = InsightAgent().execute({
                "usage": usage,
                "forecast": forecast,
                "anomaly": anomaly,
                "recommendation": recommendation
            })
            CacheManager.set(insight_key, insight)

        # Generate report
        data = {
            "usage": usage,
            "forecast": forecast,
            "anomaly": anomaly,
            "recommendation": recommendation,
            "insight": insight
        }

        generator = ReportGenerator(data)
        report = convert_numpy_types(generator.generate_report())

        # Save cache
        CacheManager.set(cache_key, report)
        
        # Save to reports database table as well for persistence
        if active_dataset_id:
            import json
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            try:
                savings_json = json.dumps(recommendation.get("savings", {}))
                co2_json = json.dumps(recommendation.get("co2", {}))
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO reports (dataset_id, summary_markdown, alert_level, status, savings_json, co2_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        active_dataset_id,
                        report.get("summary_markdown", ""),
                        report.get("alert_level", "Normal"),
                        "completed",
                        savings_json,
                        co2_json
                    )
                )
                conn.commit()
            except Exception as e:
                logger.error(f"Failed to save report to database: {e}")
            finally:
                conn.close()

        return report
    except Exception as e:
        logger.error(f"Error generating intelligence report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download")
def download_pdf_report(
    x_dataset_id: Optional[int] = Header(None),
    dataset_id: Optional[int] = Query(None),
    x_user_id: Optional[int] = Header(None),
    user_id: Optional[int] = Query(None)
):
    active_dataset_id = x_dataset_id or dataset_id
    active_user_id = x_user_id or user_id

    if not active_dataset_id:
        active_dataset_id = DatabaseManager.get_active_dataset_id(active_user_id)

    pdf_path = None
    
    # Try fetching path from DB
    if active_dataset_id:
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT pdf_path FROM reports WHERE dataset_id = ?", (active_dataset_id,))
            row = cursor.fetchone()
            pdf_path = row[0] if row else None
        except Exception as e:
            logger.error(f"Error querying PDF path: {e}")
        finally:
            conn.close()
            
    # Generate on-the-fly if path not found or doesn't exist
    if not pdf_path or not os.path.exists(pdf_path):
        # Generate markdown content
        report_md = ""
        if active_dataset_id:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT summary_markdown FROM reports WHERE dataset_id = ?", (active_dataset_id,))
                row = cursor.fetchone()
                report_md = row[0] if row else ""
            except Exception as e:
                logger.error(f"Error querying report MD: {e}")
            finally:
                conn.close()
                
        if not report_md:
            # Generate default reports content
            rep = get_reports(x_dataset_id=active_dataset_id)
            report_md = rep.get("summary_markdown", "")
            
        from backend.config import config
        pdf_dir = config.OUTPUT_DIR
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_id = active_dataset_id if active_dataset_id else "default"
        pdf_path = str(pdf_dir / f"report_{pdf_id}.pdf")
        
        PDFGenerator.generate_pdf(report_md, pdf_path)
        
        if active_dataset_id:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE reports SET pdf_path = ? WHERE dataset_id = ?", (pdf_path, active_dataset_id))
                conn.commit()
            except Exception as e:
                logger.error(f"Error updating pdf path: {e}")
            finally:
                conn.close()
                
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"energy_audit_report_{active_dataset_id or 'default'}.pdf")
