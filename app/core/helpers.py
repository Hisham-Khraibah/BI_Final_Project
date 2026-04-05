# -----------------------------------------------------------------------------
# HELPERS MODULE
# -----------------------------------------------------------------------------
"""
Shared utility functions for conversions, datetime handling, JSON I/O,
and basic data cleaning.
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any
import pandas as pd
from zoneinfo import ZoneInfo

# -----------------------------------------------------------------------------
# SAFE CONVERSIONS
# -----------------------------------------------------------------------------
def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    try:
        return float(value)
    except Exception:
        return default

def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert a value to int."""
    try:
        return int(value)
    except Exception:
        return default

# -----------------------------------------------------------------------------
# DATE / TIME HELPERS
# -----------------------------------------------------------------------------
def get_now_local(app_timezone: str = "America/Toronto") -> datetime:
    """Return current datetime in the given timezone."""
    try:
        return datetime.now(ZoneInfo(app_timezone))
    except Exception:
        return datetime.now()

def get_today_local(app_timezone: str = "America/Toronto"):
    """Return today's date in the given timezone."""
    try:
        return get_now_local(app_timezone).date()
    except Exception:
        return datetime.now().date()

def to_datetime_safe(series: pd.Series) -> pd.Series:
    """Safely convert a pandas Series to datetime."""
    try:
        return pd.to_datetime(series, errors="coerce")
    except Exception:
        return pd.Series(dtype="datetime64[ns]")

# -----------------------------------------------------------------------------
# JSON HELPERS
# -----------------------------------------------------------------------------
def safe_read_json(path: str | Path, default_value):
    """Safely read a JSON file."""
    try:
        path = Path(path)

        if not path.exists():
            return default_value

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception:
        return default_value

def safe_write_json(path: str | Path, data) -> bool:
    """Safely write a JSON file."""
    try:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return True

    except Exception:
        return False

# -----------------------------------------------------------------------------
# DATA CLEANING
# -----------------------------------------------------------------------------
def clean_amount_series(df: pd.DataFrame, column: str = "amount") -> pd.Series:
    """Return a numeric Series with non-negative values only."""
    try:
        if df.empty or column not in df.columns:
            return pd.Series(dtype=float)

        amounts = pd.to_numeric(df[column], errors="coerce").dropna()
        return amounts[amounts >= 0]

    except Exception:
        return pd.Series(dtype=float)