"""Path utilities for Edgar-AI."""

from pathlib import Path
from edgar.config import settings


def get_data_dir() -> Path:
    """Get the data directory path."""
    path = Path(settings.data_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_cache_dir() -> Path:
    """Get the cache directory path."""
    path = get_data_dir() / "cache"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_logs_dir() -> Path:
    """Get the logs directory path."""
    path = get_data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path