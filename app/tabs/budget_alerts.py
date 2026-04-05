# -----------------------------------------------------------------------------
# BUDGET ALERTS TAB
# -----------------------------------------------------------------------------
"""
Streamlit UI for budget settings, KPI monitoring, alerts, and category views.
"""
from __future__ import annotations
import pandas as pd
import streamlit as st
from app.core.budget_logic import (
    build_budget_alerts,
    build_category_budget_overview,
    calculate_kpis,
    get_budget_popup_messages,
    get_current_month_df,
    load_budget_settings,
    save_budget_settings,
)
from app.core.categories import get_all_categories
from app.core.config import BUDGET_PATH, CUSTOM_CAT_PATH, DB_PATH
from app.core.database import fetch_df
from app.core.helpers import get_now_local, safe_float
from app.ui.components import (
    render_budget_popup_inline,
    render_budget_progress,
    render_clean_pie_chart,
)

# -----------------------------------------------------------------------------
# SESSION STATE
# -----------------------------------------------------------------------------
def init_budget_alerts_state() -> None:
    """Initialize session state values used by the Budget Alerts tab."""
    if "shown_budget_popups" not in st.session_state:
        st.session_state["shown_budget_popups"] = []

    if "budget_saved_message" not in st.session_state:
        st.session_state["budget_saved_message"] = ""

    if "active_budget_popup" not in st.session_state:
        st.session_state["active_budget_popup"] = None

# -----------------------------------------------------------------------------
# MAIN RENDERER
# -----------------------------------------------------------------------------
def render_budget_alerts_tab() -> None:
    """Render the Budget Alerts tab UI."""
    try:
        init_budget_alerts_state()

        st.subheader("Budget Alerts")

        df = fetch_df(DB_PATH)
        saved_budget_settings = load_budget_settings(BUDGET_PATH)
        all_categories = [
            category
            for category in get_all_categories(CUSTOM_CAT_PATH)
            if category != ""
        ]

        if not df.empty:
            df["tx_date"] = pd.to_datetime(df["tx_date"], errors="coerce")
            df = df.dropna(subset=["tx_date"])

        if st.session_state["budget_saved_message"]:
            st.success(st.session_state["budget_saved_message"])
            st.session_state["budget_saved_message"] = ""

        st.markdown("### Set Monthly Budget")

        monthly_budget_input = st.number_input(
            "Overall Monthly Budget",
            min_value=0.0,
            value=safe_float(saved_budget_settings.get("monthly_budget", 0.0), 0.0),
            step=10.0,
            format="%.2f",
            key="overall_monthly_budget",
        )

        updated_category_budgets = {}

        with st.expander("Set Category Budgets", expanded=False):
            current_category_budgets = saved_budget_settings.get("category_budgets", {})

            for category in all_categories:
                updated_category_budgets[category] = st.number_input(
                    f"{category} Budget",
                    min_value=0.0,
                    value=float(current_category_budgets.get(category, 0.0)),
                    step=10.0,
                    format="%.2f",
                    key=f"budget_{category}",
                )

        col_save1, col_save2 = st.columns(2)

        with col_save1:
            if st.button("Save Budget Settings", use_container_width=True):
                cleaned_budgets = {
                    key: float(value)
                    for key, value in updated_category_budgets.items()
                    if float(value) > 0
                }

                if save_budget_settings(
                    BUDGET_PATH,
                    float(monthly_budget_input),
                    cleaned_budgets,
                ):
                    st.session_state["shown_budget_popups"] = []
                    st.session_state["active_budget_popup"] = None
                    st.session_state["budget_saved_message"] = (
                        "Budget settings saved successfully."
                    )
                    st.rerun()
                else:
                    st.error("Could not save budget settings.")

        with col_save2:
            if st.button("Clear All Budgets", use_container_width=True):
                if save_budget_settings(BUDGET_PATH, 0.0, {}):
                    st.session_state["shown_budget_popups"] = []
                    st.session_state["active_budget_popup"] = None
                    st.session_state["budget_saved_message"] = (
                        "All budget settings were cleared."
                    )
                    st.rerun()
                else:
                    st.error("Could not clear budget settings.")

        effective_budget_settings = {
            "monthly_budget": float(monthly_budget_input),
            "category_budgets": {
                key: float(value)
                for key, value in updated_category_budgets.items()
                if float(value) > 0
            },
        }

        st.markdown("---")
        st.markdown("### Current Month Budget Status")

        popup_messages = get_budget_popup_messages(df, effective_budget_settings)

        if popup_messages:
            first_popup = popup_messages[0]
            popup_key = f"{first_popup['title']}|{first_popup['message']}"

            if popup_key not in st.session_state["shown_budget_popups"]:
                st.session_state["shown_budget_popups"].append(popup_key)
                st.session_state["active_budget_popup"] = first_popup

        render_budget_popup_inline()

        current_month_name = get_now_local().strftime("%B %Y")
        st.markdown(f"**Budget period:** {current_month_name}")

        current_month_df = get_current_month_df(df)

        if current_month_df.empty:
            st.info("No expenses recorded for the current month yet.")
            return

        kpis = calculate_kpis(df, effective_budget_settings)

        total_spent = kpis["total_spending"]
        overall_budget = kpis["monthly_budget"]
        remaining = kpis["remaining_budget"]
        usage_percent = kpis["usage_percent"]
        transaction_count = kpis["transaction_count"]
        average_spend = kpis["average_spend"]

        st.markdown("### KPI Monitoring")

        col1, col2, col3, col4, col5, col6 = st.columns(6)

        with col1:
            st.metric("Total Spending", f"${total_spent:,.2f}")

        with col2:
            st.metric("Monthly Budget", f"${overall_budget:,.2f}")

        with col3:
            st.metric("Remaining Budget", f"${remaining:,.2f}")

        with col4:
            st.metric("Usage Ratio", f"{usage_percent:.2f}%")

        with col5:
            st.metric("Transactions", f"{transaction_count}")

        with col6:
            st.metric("Average Spend", f"${average_spend:,.2f}")

        if overall_budget > 0:
            if usage_percent > 100:
                st.error(f"Budget usage is at {usage_percent:.2f}% - Over Budget")
            elif usage_percent >= 80:
                st.warning(f"Budget usage is at {usage_percent:.2f}% - Warning Zone")
            else:
                st.success(f"Budget usage is at {usage_percent:.2f}% - On Track")
        else:
            st.info("Set a monthly budget to track usage ratio.")

        st.markdown("### Overall Budget Progress")
        render_budget_progress("Overall Monthly Budget", total_spent, overall_budget)

        with st.expander("Alerts", expanded=False):
            alerts = build_budget_alerts(df, effective_budget_settings)

            if alerts:
                for alert in alerts:
                    if alert["type"] == "error":
                        st.error(f"{alert['title']} - {alert['message']}")
                    elif alert["type"] == "warning":
                        st.warning(f"{alert['title']} - {alert['message']}")
                    else:
                        st.success(f"{alert['title']} - {alert['message']}")
            else:
                st.info("No alerts available.")

        with st.expander("Category Budget Progress", expanded=False):
            category_spend = current_month_df.groupby(
                "category",
                as_index=False,
            )["amount"].sum()

            if not category_spend.empty:
                for _, row in category_spend.iterrows():
                    category = str(row["category"])
                    spent = float(row["amount"])
                    budget = float(
                        effective_budget_settings.get("category_budgets", {}).get(
                            category,
                            0.0,
                        )
                    )
                    render_budget_progress(category, spent, budget)
            else:
                st.info("No category spending data available.")

        with st.expander("Category Budget Overview", expanded=False):
            overview_df = build_category_budget_overview(df, effective_budget_settings)

            if not overview_df.empty:
                display_df = overview_df.copy()

                display_df["Spent"] = display_df["Spent"].map(
                    lambda x: f"${x:,.2f}"
                )
                display_df["Budget"] = display_df["Budget"].map(
                    lambda x: f"${x:,.2f}"
                )

                if "Remaining" in display_df.columns:
                    display_df["Remaining"] = display_df["Remaining"].apply(
                        lambda x: f"${x:,.2f}" if pd.notnull(x) else "-"
                    )

                if "Usage %" in display_df.columns:
                    display_df["Usage %"] = display_df["Usage %"].apply(
                        lambda x: f"{x:.2f}%" if pd.notnull(x) else "-"
                    )

                st.dataframe(display_df, hide_index=True)
            else:
                st.info("No category spending data available.")

        with st.expander("Pie Chart - Current Month Category Spending", expanded=False):
            pie_df = current_month_df.groupby("category", as_index=False)["amount"].sum()
            render_clean_pie_chart(pie_df)

    except Exception as error:
        st.error(f"Error in Budget Alerts tab: {error}")