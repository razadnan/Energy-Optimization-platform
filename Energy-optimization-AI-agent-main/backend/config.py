"""
Project Configuration
Energy Optimization Agent
"""

import sys
from pathlib import Path
root_path = str(Path(__file__).resolve().parent.parent)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

import os

DEVELOPER_MODE = (
    os.getenv(
        "DEVELOPER_MODE",
        "False"
    ).lower()
    ==
    "true"
)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv is optional - env vars can still be set directly
    pass


class Config:
    """Central configuration class."""

    # =====================================================
    # PROJECT ROOT
    # =====================================================
    BASE_DIR = Path(__file__).resolve().parent.parent

    # =====================================================
    # DATA DIRECTORIES
    # =====================================================
    DATA_DIR = BASE_DIR / "data"
    RAW_DATA_DIR = DATA_DIR / "raw"
    PROCESSED_DATA_DIR = DATA_DIR / "processed"
    DATABASE_PATH = DATA_DIR / "energy_agent.db"

    # =====================================================
    # OUTPUT DIRECTORIES
    # =====================================================
    OUTPUT_DIR = DATA_DIR / "outputs"
    LOG_DIR = DATA_DIR / "logs"

    def __init__(self):
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)

    # =====================================================
    # MODEL DIRECTORY
    # =====================================================
    MODEL_DIR = BASE_DIR / "models"

    # =====================================================
    # APPLICATION SETTINGS
    # =====================================================
    APP_NAME = "Energy Optimization Agent"
    VERSION = "1.0.0"

    # =====================================================
    # FORECAST SETTINGS
    # =====================================================
    FORECAST_HORIZON = 24

    # =====================================================
    # ANOMALY DETECTION
    # =====================================================
    ANOMALY_THRESHOLD = 0.85

    # =====================================================
    # SAVINGS CALCULATION
    # =====================================================
    # =====================================================
    # LLM / INSIGHT AGENT SETTINGS
    # =====================================================
    INSIGHT_MAX_TOKENS = 1024

    @property
    def ELECTRICITY_RATE(self) -> float:
        try:
            from dotenv import load_dotenv
            load_dotenv(self.BASE_DIR / ".env", override=False)
        except Exception:
            pass
        try:
            return float(os.environ.get("ELECTRICITY_RATE", 8.0))
        except ValueError:
            return 8.0

    @ELECTRICITY_RATE.setter
    def ELECTRICITY_RATE(self, value):
        os.environ["ELECTRICITY_RATE"] = str(value)

    @property
    def CO2_PER_KWH(self) -> float:
        try:
            from dotenv import load_dotenv
            load_dotenv(self.BASE_DIR / ".env", override=False)
        except Exception:
            pass
        try:
            return float(os.environ.get("CO2_PER_KWH", 0.82))
        except ValueError:
            return 0.82

    @CO2_PER_KWH.setter
    def CO2_PER_KWH(self, value):
        os.environ["CO2_PER_KWH"] = str(value)

    @property
    def ANTHROPIC_API_KEY(self):
        try:
            from dotenv import load_dotenv
            load_dotenv(self.BASE_DIR / ".env", override=False)
        except Exception:
            pass
        return os.environ.get("ANTHROPIC_API_KEY")

    @ANTHROPIC_API_KEY.setter
    def ANTHROPIC_API_KEY(self, value):
        os.environ["ANTHROPIC_API_KEY"] = str(value) if value else ""

    @property
    def GEMINI_API_KEY(self):
        try:
            from dotenv import load_dotenv
            load_dotenv(self.BASE_DIR / ".env", override=False)
        except Exception:
            pass
        return os.environ.get("GEMINI_API_KEY")

    @GEMINI_API_KEY.setter
    def GEMINI_API_KEY(self, value):
        os.environ["GEMINI_API_KEY"] = str(value) if value else ""

    @property
    def INSIGHT_MODEL(self):
        try:
            from dotenv import load_dotenv
            load_dotenv(self.BASE_DIR / ".env", override=False)
        except Exception:
            pass
        default_model = "gemini-3.1-flash-lite" if os.environ.get("GEMINI_API_KEY") else "claude-sonnet-4-6"
        return os.environ.get("INSIGHT_MODEL", default_model)

    @INSIGHT_MODEL.setter
    def INSIGHT_MODEL(self, value):
        default_model = "gemini-3.1-flash-lite" if os.environ.get("GEMINI_API_KEY") else "claude-sonnet-4-6"
        os.environ["INSIGHT_MODEL"] = str(value) if value else default_model


config = Config()