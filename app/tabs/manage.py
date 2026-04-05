# -----------------------------------------------------------------------------
# 🛠️ MANAGE TAB
# -----------------------------------------------------------------------------
"""
Streamlit UI for viewing, editing, and deleting saved transactions.
"""
from __future__ import annotations
import pandas as pd
import streamlit as st
from app.core.categories import get_all_categories
from app.core.config import APP_TIMEZONE, CUSTOM_CAT_PATH, DB_PATH
from app.core.database import delete_expense, fetch_df, update_expense
from app.core.helpers import get_today_local, safe_float
from app.ui.components import render_date_input

# -----------------------------------------------------------------------------
# DATA PREPARATION
# -----------------------------------------------------------------------------
def prepare_manage_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare the dataframe for display in the Manage tab."""
    try:
        if df.empty:
            return pd.DataFrame()

        df_manage = df.copy()

        if "created_at" in df_manage.columns:
            created_dt = pd.to_datetime(df_manage["created_at"], errors="coerce")

            df_manage["created_date"] = created_dt.apply(
                lambda x: x.strftime("%Y-%m-%d") if pd.notnull(x) else ""
            )
            df_manage["created_time"] = created_dt.apply(
                lambda x: x.strftime("%I:%M:%S %p") if pd.notnull(x) else ""
            )

            df_manage = df_manage.drop(columns=["created_at"])

        if "notes" in df_manage.columns:
            df_manage = df_manage.drop(columns=["notes"])

        if "source" in df_manage.columns:
            df_manage = df_manage.drop(columns=["source"])

        if "tx_date" in df_manage.columns:
            tx_series = pd.to_datetime(df_manage["tx_date"], errors="coerce")
            df_manage["tx_date"] = tx_series.apply(
                lambda x: x.strftime("%Y-%m-%d") if pd.notnull(x) else ""
            )

        if "amount" in df_manage.columns:
            df_manage["amount"] = df_manage["amount"].map(
                lambda x: f"${safe_float(x, 0.0):,.2f}"
            )

        df_manage = df_manage.rename(
            columns={
                "id": "ID",
                "tx_date": "Transaction Date",
                "merchant": "Vendor",
                "amount": "Amount",
                "category": "Category",
                "note": "Description",
                "created_date": "Date of creation",
                "created_time": "Time of creation",
            }
        )

        display_columns = [
            "ID",
            "Transaction Date",
            "Vendor",
            "Amount",
            "Category",
            "Description",
            "Date of creation",
            "Time of creation",
        ]

        existing_columns = [col for col in display_columns if col in df_manage.columns]
        df_manage = df_manage[existing_columns]

        return df_manage

    except Exception:
        return pd.DataFrame()

# -----------------------------------------------------------------------------
# MAIN RENDERER
# -----------------------------------------------------------------------------
def render_manage_tab() -> None:
    """Render the Manage tab UI."""
    try:
        st.subheader("Edit or Delete")
        st.info("Select a row in the table below to edit or delete.")

        df = fetch_df(DB_PATH)

        if df.empty:
            st.info("No records to manage.")
            return

        df_display = prepare_manage_dataframe(df)

        if df_display.empty:
            st.info("No records to manage.")
            return

        event = st.dataframe(
            df_display,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
        )

        selected_rows = event.selection.rows

        if not selected_rows:
            return

        selected_idx = selected_rows[0]
        selected_row = df.iloc[selected_idx]
        row_id = int(selected_row["id"])

        st.markdown(f"**Selected row ID:** {row_id}")

        action = st.radio(
            "Action",
            ["Edit", "Delete"],
            horizontal=True,
            key=f"manage_action_{row_id}",
        )

        if action == "Edit":
            col1, col2, col3 = st.columns(3)

            with col1:
                edit_date = render_date_input(
                    label="Transaction Date",
                    value=min(
                        pd.to_datetime(selected_row["tx_date"]).date(),
                        get_today_local(APP_TIMEZONE),
                    ),
                    max_value=get_today_local(APP_TIMEZONE),
                    key=f"edit_date_{row_id}",
                    app_timezone=APP_TIMEZONE,
                )

            with col2:
                edit_merchant = st.text_input(
                    "Vendor",
                    value=str(selected_row["merchant"]),
                    key=f"edit_merchant_{row_id}",
                )

            with col3:
                edit_amount = st.number_input(
                    "Amount",
                    value=float(selected_row["amount"]),
                    min_value=0.0,
                    step=0.01,
                    key=f"edit_amount_{row_id}",
                )

            all_categories = get_all_categories(CUSTOM_CAT_PATH)

            try:
                edit_category_index = all_categories.index(selected_row["category"])
            except ValueError:
                edit_category_index = 0

            edit_category = st.selectbox(
                "Category",
                all_categories,
                index=edit_category_index,
                key=f"edit_cat_{row_id}",
            )

            edit_note = st.text_input(
                "Description",
                value=str(selected_row.get("note", "")),
                key=f"edit_note_{row_id}",
            )

            if st.button("Save Changes", key=f"edit_btn_{row_id}"):
                if update_expense(
                    db_path=DB_PATH,
                    row_id=row_id,
                    tx_date=edit_date.isoformat(),
                    merchant=edit_merchant,
                    amount=edit_amount,
                    category=edit_category,
                    note=edit_note,
                ):
                    st.success("Updated successfully")
                    st.rerun()
                else:
                    st.error("Could not update the selected row.")

        elif action == "Delete":
            if st.button("Confirm Delete", key=f"delete_btn_{row_id}"):
                if delete_expense(DB_PATH, row_id):
                    st.success("Deleted successfully")
                    st.rerun()
                else:
                    st.error("Could not delete the selected row.")

    except Exception as error:
        st.error(f"Error in Manage tab: {error}")