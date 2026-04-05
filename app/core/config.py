# -----------------------------------------------------------------------------
# CONFIG MODULE
# -----------------------------------------------------------------------------
"""
Central application configuration for timezone, directories, and file paths.
"""
from __future__ import annotations
from pathlib import Path

# -----------------------------------------------------------------------------
# APP SETTINGS
# -----------------------------------------------------------------------------
APP_TIMEZONE = "America/Toronto"

# -----------------------------------------------------------------------------
# DIRECTORIES
# -----------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = PROJECT_ROOT / "app"
DATA_DIR = PROJECT_ROOT / "data"

# -----------------------------------------------------------------------------
# FILE PATHS
# -----------------------------------------------------------------------------
CSV_PATH = DATA_DIR / "Expenses.csv"
DB_PATH = DATA_DIR / "Expenses.db"
BUDGET_PATH = DATA_DIR / "budget_settings.json"
CUSTOM_CAT_PATH = DATA_DIR / "custom_categories.json"
CUSTOM_KEYWORD_PATH = DATA_DIR / "custom_keywords.json"

# -----------------------------------------------------------------------------
# INITIALIZATION
# -----------------------------------------------------------------------------
def ensure_data_dir() -> bool:
    """Create the data directory if it does not already exist."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False

# -----------------------------------------------------------------------------
# STRING PATH HELPERS
# -----------------------------------------------------------------------------
def get_csv_path() -> str:
    return str(CSV_PATH)

def get_db_path() -> str:
    return str(DB_PATH)

def get_budget_path() -> str:
    return str(BUDGET_PATH)

def get_custom_cat_path() -> str:
    return str(CUSTOM_CAT_PATH)

def get_custom_keyword_path() -> str:
    return str(CUSTOM_KEYWORD_PATH)