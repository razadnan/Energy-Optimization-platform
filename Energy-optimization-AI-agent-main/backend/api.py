"""
=========================================================
FastAPI Backend
Energy Optimization Agent
=========================================================
"""

import sys
from pathlib import Path
root_path = str(Path(__file__).resolve().parent.parent)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import (
    usage,
    forecast,
    anomaly,
    recommendation,
    insights,
    chat,
    reports,
    auth,
    datasets,
)

app = FastAPI(
    title="Energy Optimization Agent",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from backend.database import DatabaseManager

@app.on_event("startup")
def on_startup():
    try:
        DatabaseManager.initialize_db()
    except Exception as e:
        print(f"Error during database initialization: {e}")


@app.get("/")
def home():
    return {
        "project": "Energy Optimization Agent",
        "status": "Running",
        "version": "1.0.0"
    }


# Include Routers
app.include_router(auth.router)
app.include_router(datasets.router)
app.include_router(usage.router)
app.include_router(forecast.router)
app.include_router(anomaly.router)
app.include_router(recommendation.router)
app.include_router(insights.router)
app.include_router(chat.router)
app.include_router(reports.router)