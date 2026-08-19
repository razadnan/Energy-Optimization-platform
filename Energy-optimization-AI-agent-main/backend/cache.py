import json
from pathlib import Path
import time
from backend.config import config
from utils.helpers import convert_numpy_types
from services.logger import setup_logger

logger = setup_logger("CacheManager")

class CacheManager:
    """
    Manages loading and saving cached pipeline outputs to avoid recalculating
    expensive machine learning fits on every request.
    """

    CACHE_DIR = config.OUTPUT_DIR / "cache"

    @classmethod
    def initialize(cls):
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get(cls, key: str, max_age_seconds: int = 86400) -> dict:
        """
        Retrieves cached data if it exists and is not expired.
        """
        cls.initialize()
        cache_file = cls.CACHE_DIR / f"{key}.json"
        
        if not cache_file.exists():
            return None
            
        file_age = time.time() - cache_file.stat().st_mtime
        if file_age > max_age_seconds:
            logger.info(f"Cache for {key} is expired ({file_age:.1f}s old).")
            return None
            
        try:
            with open(cache_file, "r") as f:
                data = json.load(f)
                logger.info(f"Loaded {key} from cache.")
                return data
        except Exception as e:
            logger.error(f"Error reading cache file for {key}: {e}")
            return None

    @classmethod
    def set(cls, key: str, data: dict):
        """
        Saves data to the cache.
        """
        cls.initialize()
        cache_file = cls.CACHE_DIR / f"{key}.json"
        try:
            # Cast numpy types to ensure serializability
            clean_data = convert_numpy_types(data)
            with open(cache_file, "w") as f:
                json.dump(clean_data, f, indent=4)
            logger.info(f"Saved cache for {key}.")
        except Exception as e:
            logger.error(f"Error writing cache file for {key}: {e}")
