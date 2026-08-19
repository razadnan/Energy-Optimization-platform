import os
import shutil
import datetime
import logging
import json
from fastapi import APIRouter, HTTPException, UploadFile, File, Header, BackgroundTasks, Query
from pydantic import BaseModel
from typing import List, Optional
from backend.database import DatabaseManager
from services.preprocessing import DataPreprocessor

logger = logging.getLogger("DatasetsRoute")

router = APIRouter(
    prefix="/datasets",
    tags=["Datasets"]
)

# Response Schemas
class DatasetResponseSchema(BaseModel):
    id: int
    user_id: int
    filename: str
    status: str
    error_message: Optional[str] = None
    created_at: str


@router.post("/upload", response_model=DatasetResponseSchema)
def upload_dataset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    x_user_id: Optional[int] = Header(None),
    user_id: Optional[int] = Query(None)
):
    # Support user_id via header or query parameter
    active_user_id = x_user_id or user_id
    if not active_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-ID header or user_id query parameter.")

    # Validate file extension
    filename = file.filename
    if not filename.endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a CSV or Excel file.")

    # Create dataset entry in database
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    try:
        created_at = datetime.datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO datasets (user_id, filename, status, created_at) VALUES (?, ?, ?, ?)",
            (active_user_id, filename, "uploading", created_at)
        )
        conn.commit()
        dataset_id = cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

    # Save uploaded file to raw data directory
    raw_dir = DataPreprocessor().file_path.parent
    raw_dir.mkdir(parents=True, exist_ok=True)
    temp_file_path = raw_dir / f"dataset_{dataset_id}_{filename}"
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        # Update dataset status as failed
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE datasets SET status = 'failed', error_message = ? WHERE id = ?", (f"File save error: {str(e)}", dataset_id))
        conn.commit()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")

    # Add AI Pipeline run to background tasks
    background_tasks.add_task(run_pipeline_async, dataset_id, str(temp_file_path))

    return {
        "id": dataset_id,
        "user_id": active_user_id,
        "filename": filename,
        "status": "uploading",
        "created_at": created_at
    }


@router.get("/", response_model=List[DatasetResponseSchema])
def list_datasets(
    x_user_id: Optional[int] = Header(None),
    user_id: Optional[int] = Query(None)
):
    active_user_id = x_user_id or user_id
    if not active_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-ID header or user_id query parameter.")

    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, user_id, filename, status, error_message, created_at FROM datasets WHERE user_id = ? ORDER BY id DESC",
            (active_user_id,)
        )
        rows = cursor.fetchall()
        datasets = []
        for r in rows:
            datasets.append({
                "id": r[0],
                "user_id": r[1],
                "filename": r[2],
                "status": r[3],
                "error_message": r[4],
                "created_at": r[5]
            })
        return datasets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()


@router.get("/{dataset_id}", response_model=DatasetResponseSchema)
def get_dataset(dataset_id: int):
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, user_id, filename, status, error_message, created_at FROM datasets WHERE id = ?",
            (dataset_id,)
        )
        r = cursor.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Dataset not found.")
        return {
            "id": r[0],
            "user_id": r[1],
            "filename": r[2],
            "status": r[3],
            "error_message": r[4],
            "created_at": r[5]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()


@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: int):
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM datasets WHERE id = ?", (dataset_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Dataset not found.")
            
        cursor.execute("DELETE FROM datasets WHERE id = ?", (dataset_id,))
        conn.commit()
        return {"status": "success", "message": f"Dataset {dataset_id} deleted."}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()


def run_pipeline_async(dataset_id: int, file_path: str):
    """
    Background worker that runs the validation, cleaning, and complete AI Agent pipeline.
    """
    logger.info(f"Background pipeline execution started for dataset {dataset_id}")
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    
    try:
        # Step 1: Preprocess, validate & clean
        cursor.execute("UPDATE datasets SET status = 'cleaning' WHERE id = ?", (dataset_id,))
        conn.commit()
        
        preprocessor = DataPreprocessor()
        # This performs parsing, checks validation constraints, cleans columns, and saves to energy_data table
        preprocessor.preprocess_file(file_path, dataset_id)
        
        cursor.execute("UPDATE datasets SET status = 'processing' WHERE id = ?", (dataset_id,))
        conn.commit()

        # Step 2: Usage Analyzer
        from analytics.usage_analysis import UsageAnalyzer
        analyzer = UsageAnalyzer(dataset_id=dataset_id)
        usage_report = analyzer.generate_report()

        # Step 3: Forecasting Model
        from models.forecasting import ForecastingModel
        forecaster = ForecastingModel(dataset_id=dataset_id)
        forecast_report = forecaster.run_pipeline()

        # Step 4: Anomaly Detection Model
        from models.anomaly_detection import AnomalyDetectionModel
        detector = AnomalyDetectionModel(dataset_id=dataset_id)
        anomaly_report = detector.run_pipeline()

        # Step 5: Recommendation Engine
        from services.recommendation_engine import RecommendationEngine
        engine = RecommendationEngine(usage_report, forecast_report, anomaly_report, dataset_id=dataset_id)
        rec_report = engine.run_pipeline()

        # Step 6: Insight Agent (AI Reasoning)
        from agents.insight_agent import InsightAgent
        insight_report = InsightAgent().execute({
            "usage": usage_report,
            "forecast": forecast_report,
            "anomaly": anomaly_report,
            "recommendation": rec_report
        })

        # Step 7: Final Markdown Audit Report
        from services.report_generator import ReportGenerator
        data = {
            "usage": usage_report,
            "forecast": forecast_report,
            "anomaly": anomaly_report,
            "recommendation": rec_report,
            "insight": insight_report
        }
        generator = ReportGenerator(data)
        final_report = generator.generate_report()

        # Step 8: PDF Generator
        from services.pdf_generator import PDFGenerator
        from backend.config import config
        pdf_dir = config.OUTPUT_DIR
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = pdf_dir / f"report_{dataset_id}.pdf"
        
        PDFGenerator.generate_pdf(final_report.get("summary_markdown", ""), str(pdf_path))

        # Save AI pipeline outcomes into Reports Table
        savings_json = json.dumps(rec_report.get("savings", {}))
        co2_json = json.dumps(rec_report.get("co2", {}))
        
        cursor.execute(
            """
            INSERT OR REPLACE INTO reports (dataset_id, summary_markdown, alert_level, status, pdf_path, savings_json, co2_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                dataset_id,
                final_report.get("summary_markdown", ""),
                final_report.get("alert_level", "Normal"),
                "completed",
                str(pdf_path),
                savings_json,
                co2_json
            )
        )
        
        # Update dataset status to completed
        cursor.execute("UPDATE datasets SET status = 'completed' WHERE id = ?", (dataset_id,))
        conn.commit()
        logger.info(f"Background pipeline successfully completed for dataset {dataset_id}")
        
    except Exception as e:
        conn.rollback()
        # Set dataset status to failed and store the error message
        cursor.execute(
            "UPDATE datasets SET status = 'failed', error_message = ? WHERE id = ?",
            (str(e), dataset_id)
        )
        conn.commit()
        logger.error(f"Background pipeline failed for dataset {dataset_id}: {str(e)}", exc_info=True)
    finally:
        conn.close()
        # Clean up temporary uploaded file to keep raw folder clean
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
