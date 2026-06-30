import os
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "cache")
)

class FileCache:
    """A simple persistent JSON file cache for heavy LLM responses and queries."""
    
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create cache directory: {e}")

    def _get_filepath(self, key: str) -> str:
        # Clean key for safe filename
        safe_key = "".join([c if c.isalnum() or c in "-_" else "_" for c in key])
        return os.path.join(self.cache_dir, f"{safe_key}.json")

    def get(self, key: str) -> Optional[Any]:
        """Retrieves a cached JSON-serializable item if it exists."""
        filepath = self._get_filepath(key)
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error reading cache file {filepath}: {e}")
            return None

    def set(self, key: str, value: Any) -> None:
        """Saves a JSON-serializable item to the cache."""
        filepath = self._get_filepath(key)
        try:
            # Write to a temp file first then rename to ensure atomic write
            temp_filepath = filepath + ".tmp"
            with open(temp_filepath, "w", encoding="utf-8") as f:
                json.dump(value, f, ensure_ascii=False, indent=2)
            os.replace(temp_filepath, filepath)
        except Exception as e:
            logger.error(f"Failed to write cache file {filepath}: {e}")

file_cache = FileCache()
