# -----------------------------------------------------------------------------
# SMART EXPENSE TRACKER - MAIN
# -----------------------------------------------------------------------------
"""
Main entry point for the Smart Expense Tracker application.
"""
from __future__ import annotations
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from app.core.config import DB_PATH, ensure_data_dir
from app.core.database import init_db
from app.tabs.add_expense import render_add_expense_tab
from app.tabs.budget_alerts import render_budget_alerts_tab
from app.tabs.dashboard import render_dashboard_tab
from app.tabs.powerbi_dashboard import render_power_bi_dashboard_tab
from app.tabs.manage import render_manage_tab
from app.tabs.export import render_export_tab

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
def configure_page() -> None:
    """Configure Streamlit page settings."""
    try:
        st.set_page_config(
            page_title="Smart Expense Tracker",
            layout="wide",
        )
    except Exception:
        pass

# -----------------------------------------------------------------------------
# STYLING
# -----------------------------------------------------------------------------
def apply_global_styles() -> None:
    """Apply global CSS styling."""
    try:
        st.markdown(
            """
            <style>
                .popup-box {
                    padding: 20px;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                    border: 1px solid #ccc;
                    margin-top: 20px;
                }

                [data-testid='stToolbar'] {
                    display: none !important;
                }

                header {
                    visibility: hidden !important;
                }

                div.stButton > button {
                    border-radius: 10px !important;
                    min-height: 42px !important;
                    padding: 0.4rem 1rem !important;
                    white-space: nowrap !important;
                    word-break: normal !important;
                    overflow-wrap: normal !important;
                }

                div.stButton > button:focus,
                div.stButton > button:focus:not(:active) {
                    outline: none !important;
                    box-shadow: none !important;
                    border-color: #cccccc !important;
                }

                div[data-testid='stMetric'] {
                    background-color: transparent;
                    padding-top: 0.15rem;
                    padding-bottom: 0.15rem;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )
    except Exception as error:
        st.error(f"Error applying page style: {error}")

# -----------------------------------------------------------------------------
# INITIALIZATION
# -----------------------------------------------------------------------------
def initialize_app() -> None:
    """Initialize required directories and database."""
    try:
        if not ensure_data_dir():
            st.error("Could not create the data directory.")
            return

        if not init_db(DB_PATH):
            st.error("Could not initialize the database.")

    except Exception as error:
        st.error(f"Error initializing application: {error}")

# -----------------------------------------------------------------------------
# HEADER
# -----------------------------------------------------------------------------
def render_app_header() -> None:
    """Render the application title."""
    try:
        st.markdown(
            """
            <h1 style='text-align: center; font-size: 56px; margin-bottom: 20px;'>
                Smart Expense Tracker
            </h1>
            """,
            unsafe_allow_html=True,
        )
    except Exception:
        st.title("Smart Expense Tracker")

# -----------------------------------------------------------------------------
# TABS
# -----------------------------------------------------------------------------
def render_app_tabs() -> None:
    """Render all application tabs."""
    try:
        tab_add, tab_budget, tab_dashboard, tab_power_bi, tab_manage, tab_export = st.tabs([
            "➕ Add Expense",
            "🚨 Budget Alerts",
            "📊 Dashboard",
            "📈 Power BI Dashboard",
            "🛠️ Manage",
            "📁 Export",
        ])

        with tab_add:
            render_add_expense_tab()

        with tab_budget:
            render_budget_alerts_tab()

        with tab_dashboard:
            render_dashboard_tab()

        with tab_power_bi:
            render_power_bi_dashboard_tab()

        with tab_manage:
            render_manage_tab()

        with tab_export:
            render_export_tab()

    except Exception as error:
        st.error(f"Error rendering tabs: {error}")

# -----------------------------------------------------------------------------
# ▶️ MAIN
# -----------------------------------------------------------------------------
def main() -> None:
    """Run the application."""
    try:
        configure_page()
        initialize_app()
        apply_global_styles()
        render_app_header()
        render_app_tabs()
    except Exception as error:
        st.error(f"Unexpected application error: {error}")

# -----------------------------------------------------------------------------
# ENTRY POINT
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()