# -----------------------------------------------------------------------------
# DASHBOARD TAB
# -----------------------------------------------------------------------------
"""
Streamlit UI for dashboard filtering, KPI monitoring, trends,
forecasting, and category analysis.
"""
from __future__ import annotations
from functools import reduce
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from matplotlib.ticker import FuncFormatter
from app.core.analytics import (
    calculate_category_totals_with_reduce,
    get_top_category_summary,
    overall_monthly,
    prepare_monthly_forecast_data,
    weekly_summary,
)
from app.core.budget_logic import calculate_kpis, load_budget_settings
from app.core.config import BUDGET_PATH, DB_PATH
from app.core.database import fetch_df
from app.core.helpers import safe_float

# -----------------------------------------------------------------------------
# MAIN RENDERER
# -----------------------------------------------------------------------------
def render_dashboard_tab() -> None:
    """Render the Dashboard tab UI."""
    try:
        st.subheader("Visualizations and Insights")

        df = fetch_df(DB_PATH)

        if not df.empty:
            df["tx_date"] = pd.to_datetime(df["tx_date"], errors="coerce")
            df = df.dropna(subset=["tx_date"])

        if df.empty:
            st.warning("No data available.")
            return

        years = sorted(df["tx_date"].dt.year.unique(), reverse=True)
        selected_year = st.selectbox(
            "Select Year",
            years,
            key="dashboard_selected_year",
        )

        df_filtered = df[df["tx_date"].dt.year == selected_year].copy()

        if df_filtered.empty:
            st.warning("No data for the selected year.")
            return

        budget_settings = load_budget_settings(BUDGET_PATH)
        dashboard_kpis = calculate_kpis(df, budget_settings)

        st.markdown("### KPI Monitoring")

        col_kpi1, col_kpi2, col_kpi3, col_kpi4, col_kpi5, col_kpi6 = st.columns(6)

        with col_kpi1:
            st.metric("Total Spending", f"${dashboard_kpis['total_spending']:,.2f}")

        with col_kpi2:
            st.metric("Monthly Budget", f"${dashboard_kpis['monthly_budget']:,.2f}")

        with col_kpi3:
            st.metric("Remaining Budget", f"${dashboard_kpis['remaining_budget']:,.2f}")

        with col_kpi4:
            st.metric("Usage Ratio", f"{dashboard_kpis['usage_percent']:.2f}%")

        with col_kpi5:
            st.metric("Transactions", f"{dashboard_kpis['transaction_count']}")

        with col_kpi6:
            st.metric("Average Spend", f"${dashboard_kpis['average_spend']:,.2f}")

        st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)
        st.markdown("---")

        with st.expander("Daily Spend", expanded=False):
            df_daily = df_filtered.copy()
            df_daily["day"] = df_daily["tx_date"].dt.date
            daily_sum = df_daily.groupby("day", as_index=False)["amount"].sum()

            if daily_sum.empty:
                st.info("No daily data available.")
            else:
                daily_months = sorted(
                    daily_sum["day"].apply(lambda x: x.strftime("%b %Y")).unique()
                )

                selected_daily_month = st.selectbox(
                    "Select Month (Daily View)",
                    daily_months,
                    key="dashboard_daily_month",
                )

                daily_filtered = daily_sum[
                    daily_sum["day"].apply(lambda x: x.strftime("%b %Y"))
                    == selected_daily_month
                ].reset_index(drop=True)

                total_daily_month = reduce(
                    lambda acc, x: acc + x,
                    list(
                        map(
                            lambda x: safe_float(x, 0.0),
                            daily_filtered["amount"].tolist(),
                        )
                    ),
                    0.0,
                )

                st.markdown(
                    f"**Total for {selected_daily_month}: "
                    f"${total_daily_month:,.2f}**"
                )

                fig_daily, ax_daily = plt.subplots(figsize=(9.2, 3.8))
                x_values = np.arange(len(daily_filtered))

                ax_daily.bar(x_values, daily_filtered["amount"], width=0.55)
                ax_daily.plot(
                    x_values,
                    daily_filtered["amount"],
                    linewidth=2.0,
                    marker="o",
                    markersize=4,
                )

                for index, value in enumerate(daily_filtered["amount"]):
                    ax_daily.text(
                        index,
                        value + max(value * 0.03, 0.2),
                        f"${value:,.2f}",
                        ha="center",
                        va="bottom",
                        fontsize=8,
                    )

                ax_daily.set_xticks(x_values)
                ax_daily.set_xticklabels(
                    [day.strftime("%b %d") for day in daily_filtered["day"]],
                    rotation=45,
                    ha="right",
                )

                max_val = daily_filtered["amount"].max()
                ax_daily.set_ylim(0, max_val * 1.18 if max_val > 0 else 10)
                ax_daily.yaxis.set_major_formatter(
                    FuncFormatter(lambda y, pos: f"${y:,.0f}")
                )
                ax_daily.set_ylabel("Amount ($)")
                ax_daily.grid(axis="y", linestyle="--", alpha=0.35)
                fig_daily.tight_layout()

                st.pyplot(fig_daily)

        with st.expander("Weekly Spend", expanded=False):
            weekly_df = weekly_summary(df_filtered)

            if weekly_df.empty:
                st.info("No weekly data available.")
            else:
                week_labels = [
                    f"{week.strftime('%b %d')} - "
                    f"{(week + pd.Timedelta(days=6)).strftime('%b %d')}"
                    for week in weekly_df["week"]
                ]

                selected_week_label = st.selectbox(
                    "Select Week",
                    week_labels,
                    key="dashboard_week_label",
                )

                selected_week_index = week_labels.index(selected_week_label)
                selected_week_amount = weekly_df.loc[selected_week_index, "amount"]

                st.markdown(f"**Total: ${selected_week_amount:,.2f}**")

                fig_weekly, ax_weekly = plt.subplots(figsize=(4.8, 3.0))
                ax_weekly.bar([0], [selected_week_amount], width=0.38)
                ax_weekly.set_xticks([0])
                ax_weekly.set_xticklabels(
                    [selected_week_label],
                    rotation=18,
                    ha="right",
                )
                ax_weekly.yaxis.set_major_formatter(
                    FuncFormatter(lambda y, pos: f"${y:,.0f}")
                )
                ax_weekly.set_ylabel("Amount ($)")
                ax_weekly.set_ylim(
                    0,
                    selected_week_amount * 1.18 if selected_week_amount > 0 else 10,
                )
                ax_weekly.grid(axis="y", linestyle="--", alpha=0.4)
                fig_weekly.tight_layout()

                st.pyplot(fig_weekly)

        with st.expander("Monthly Spend", expanded=False):
            monthly_df = overall_monthly(df_filtered)

            if monthly_df.empty:
                st.info("No monthly data available.")
            else:
                month_labels = monthly_df["month"].dt.strftime("%b %Y").tolist()

                selected_month_label = st.selectbox(
                    "Select Month",
                    month_labels,
                    key="dashboard_month_label",
                )

                selected_month_index = month_labels.index(selected_month_label)
                selected_month_amount = monthly_df.loc[selected_month_index, "amount"]

                st.markdown(f"**Total: ${selected_month_amount:,.2f}**")

                fig_monthly, ax_monthly = plt.subplots(figsize=(4.8, 3.0))
                ax_monthly.bar(
                    [0],
                    [selected_month_amount],
                    width=0.38,
                    edgecolor="white",
                    linewidth=1,
                )
                ax_monthly.set_xticks([0])
                ax_monthly.set_xticklabels(
                    [selected_month_label],
                    rotation=18,
                    ha="right",
                    fontsize=10,
                )
                ax_monthly.yaxis.set_major_formatter(
                    FuncFormatter(lambda y, pos: f"${y:,.0f}")
                )
                ax_monthly.set_ylabel("Amount ($)")
                ax_monthly.grid(axis="y", linestyle="--", alpha=0.4)
                ax_monthly.spines["top"].set_visible(False)
                ax_monthly.spines["right"].set_visible(False)
                fig_monthly.tight_layout()

                st.pyplot(fig_monthly)

        with st.expander("Predictive Analytics", expanded=False):
            monthly_full, forecast_month, forecast_value = prepare_monthly_forecast_data(
                df_filtered
            )

            if monthly_full.empty or forecast_month is None or forecast_value is None:
                st.info(
                    "At least 2 months of data are required to forecast "
                    "next month's spending."
                )
            else:
                st.markdown(
                    f"**Forecast for {forecast_month.strftime('%B %Y')}: "
                    f"${forecast_value:,.2f}**"
                )

                last_actual = safe_float(monthly_full["amount"].iloc[-1], 0.0)
                change_value = forecast_value - last_actual
                change_pct = (
                    (change_value / last_actual * 100) if last_actual > 0 else 0.0
                )

                col_f1, col_f2, col_f3 = st.columns(3)

                with col_f1:
                    st.metric("Last Actual Month", f"${last_actual:,.2f}")

                with col_f2:
                    st.metric("Predicted Next Month", f"${forecast_value:,.2f}")

                with col_f3:
                    st.metric("Predicted Change", f"{change_pct:.2f}%")

                forecast_plot_df = monthly_full[["month", "amount"]].copy()
                forecast_plot_df = pd.concat(
                    [
                        forecast_plot_df,
                        pd.DataFrame(
                            [
                                {
                                    "month": forecast_month,
                                    "amount": forecast_value,
                                }
                            ]
                        ),
                    ],
                    ignore_index=True,
                )

                fig_forecast, ax_forecast = plt.subplots(figsize=(7.8, 3.8))

                actual_count = len(monthly_full)
                x_all = np.arange(len(forecast_plot_df))
                x_actual = np.arange(actual_count)
                x_forecast = np.array([actual_count])

                ax_forecast.plot(
                    x_actual,
                    monthly_full["amount"],
                    linewidth=2.0,
                    marker="o",
                    label="Actual Spending",
                )

                ax_forecast.plot(
                    x_forecast,
                    [forecast_value],
                    marker="o",
                    linestyle="None",
                    markersize=7,
                    label="Forecasted Spending",
                )

                ax_forecast.plot(
                    [x_actual[-1], x_forecast[0]],
                    [monthly_full["amount"].iloc[-1], forecast_value],
                    linestyle="--",
                    linewidth=1.5,
                )

                ax_forecast.set_xticks(x_all)
                ax_forecast.set_xticklabels(
                    forecast_plot_df["month"].dt.strftime("%b %Y"),
                    rotation=25,
                    ha="right",
                )
                ax_forecast.yaxis.set_major_formatter(
                    FuncFormatter(lambda y, pos: f"${y:,.0f}")
                )
                ax_forecast.set_ylabel("Amount ($)")
                ax_forecast.set_title("Monthly Spending Forecast")
                ax_forecast.grid(axis="y", linestyle="--", alpha=0.35)
                ax_forecast.legend()
                fig_forecast.tight_layout()

                st.pyplot(fig_forecast)

        with st.expander("Category Spending Overview", expanded=False):
            category_totals = calculate_category_totals_with_reduce(df_filtered)

            if category_totals:
                top_category, top_amount, top_share = get_top_category_summary(df_filtered)

                total_categories = len(category_totals)
                total_spending_all_categories = reduce(
                    lambda acc, item: acc + item[1],
                    category_totals.items(),
                    0.0,
                )

                col_fp1, col_fp2, col_fp3 = st.columns(3)

                with col_fp1:
                    st.metric("Tracked Categories", f"{total_categories}")

                with col_fp2:
                    st.metric("Top Category", top_category if top_category else "-")

                with col_fp3:
                    st.metric("Top Category Share", f"{top_share:.2f}%")

                functional_rows = [
                    {
                        "Category": category,
                        "Total Spending": round(amount, 2),
                        "Share %": round((amount / total_spending_all_categories * 100), 1)
                        if total_spending_all_categories > 0
                        else 0.0,
                    }
                    for category, amount in sorted(
                        category_totals.items(),
                        key=lambda item: item[1],
                        reverse=True,
                    )
                ]

                functional_df = pd.DataFrame(functional_rows)
                functional_df["Total Spending"] = functional_df["Total Spending"].map(
                    lambda x: f"${x:,.2f}"
                )
                functional_df["Share %"] = functional_df["Share %"].map(
                    lambda x: f"{x:.2f}%"
                )

                st.dataframe(functional_df, hide_index=True)
            else:
                st.info("No category spending data available.")

    except Exception as error:
        st.error(f"Error in Dashboard tab: {error}")