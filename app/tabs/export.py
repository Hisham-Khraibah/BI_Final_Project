# -----------------------------------------------------------------------------
# EXPORT TAB
# -----------------------------------------------------------------------------
"""
Streamlit UI for exporting transaction data to CSV.
"""
from __future__ import annotations
import pandas as pd
import streamlit as st
from app.core.config import DB_PATH
from app.core.database import fetch_df
from app.core.helpers import get_now_local, safe_float

# -----------------------------------------------------------------------------
# DATA PREPARATION
# -----------------------------------------------------------------------------
def prepare_export_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare and clean the dataframe for CSV export."""
    try:
        if df.empty:
            return pd.DataFrame()

        df_export = df.sort_values(["tx_date", "id"]).reset_index(drop=True)

        if "created_at" in df_export.columns:
            created_dt = pd.to_datetime(df_export["created_at"], errors="coerce")

            df_export["created_date"] = created_dt.apply(
                lambda x: x.strftime("%Y-%m-%d") if pd.notnull(x) else ""
            )
            df_export["created_time"] = created_dt.apply(
                lambda x: x.strftime("%I:%M:%S %p") if pd.notnull(x) else ""
            )

            df_export = df_export.drop(columns=["created_at"])

        if "notes" in df_export.columns:
            df_export = df_export.drop(columns=["notes"])

        if "source" in df_export.columns:
            df_export = df_export.drop(columns=["source"])

        if "id" in df_export.columns:
            df_export = df_export.drop(columns=["id"])

        df_export.insert(0, "excel_id", df_export.index + 1)

        df_export = df_export.rename(
            columns={
                "excel_id": "ID",
                "tx_date": "Transaction Date",
                "merchant": "Vendor",
                "amount": "Amount",
                "category": "Category",
                "note": "Description",
                "created_date": "Date of creation",
                "created_time": "Time of creation",
            }
        )

        export_columns = [
            "ID",
            "Transaction Date",
            "Vendor",
            "Amount",
            "Category",
            "Description",
            "Date of creation",
            "Time of creation",
        ]

        df_export = df_export[
            [col for col in export_columns if col in df_export.columns]
        ]

        if "Transaction Date" in df_export.columns:
            tx_series = pd.to_datetime(df_export["Transaction Date"], errors="coerce")
            df_export["Transaction Date"] = tx_series.apply(
                lambda x: x.strftime("%Y-%m-%d") if pd.notnull(x) else ""
            )

        if "Amount" in df_export.columns:
            df_export["Amount"] = df_export["Amount"].map(
                lambda x: f"${safe_float(x, 0.0):,.2f}"
            )

        return df_export

    except Exception:
        return pd.DataFrame()

# -----------------------------------------------------------------------------
# MAIN RENDERER
# -----------------------------------------------------------------------------
def render_export_tab() -> None:
    """Render the Export tab UI."""
    try:
        st.subheader("CSV Export")
        st.caption("Download your transaction history as a CSV file")
        
        df = fetch_df(DB_PATH)

        if df.empty:
            st.info("No data to export.")
            return

        df_export = prepare_export_dataframe(df)

        if df_export.empty:
            st.warning("Export data could not be prepared.")
            return

        st.download_button(
            label="Download CSV",
            data=df_export.to_csv(index=False).encode("utf-8"),
            file_name=f"Expenses_{get_now_local().strftime('%Y-%m-%d')}.csv",
            mime="text/csv",
        )

    except Exception as error:
        st.error(f"Error in Export tab: {error}")