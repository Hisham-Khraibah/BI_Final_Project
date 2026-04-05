# -----------------------------------------------------------------------------
# DASHBOARD TAB
# -----------------------------------------------------------------------------
'''
Streamlit UI for spending analytics and forecasting.
'''
from __future__ import annotations
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from matplotlib.ticker import FuncFormatter
from app.core.analytics import (
    overall_monthly,
    prepare_monthly_forecast_data,
    weekly_summary,
)
from app.core.config import DB_PATH
from app.core.database import fetch_df
from app.core.helpers import safe_float

# -----------------------------------------------------------------------------
# FORMATTERS
# -----------------------------------------------------------------------------
def format_currency_axis(ax) -> None:
    '''Apply currency formatting to Y-axis.'''
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda value, _: f'${value:,.0f}')
    )

# -----------------------------------------------------------------------------
# GENERIC BAR CHART
# -----------------------------------------------------------------------------
def render_single_bar_chart(
    title: str,
    label: str,
    value: float,
    ylim_top: float,
    width: float,
    height: float,
) -> None:
    '''Render a single bar chart with consistent styling.'''
    st.markdown(f'#### {title}')
    st.markdown(f'**Total: ${value:,.2f}**')

    fig, ax = plt.subplots(figsize=(width, height))

    ax.bar([0], [value], width=0.45)
    ax.set_xticks([0])
    ax.set_xticklabels([label], rotation=35, ha='right')
    ax.set_ylabel('Amount ($)')
    ax.set_ylim(0, ylim_top)

    format_currency_axis(ax)

    ax.grid(axis='y', linestyle='--', alpha=0.35)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    fig.tight_layout()
    st.pyplot(fig)

# -----------------------------------------------------------------------------
# FORECAST SECTION
# -----------------------------------------------------------------------------
def render_forecast_section(df: pd.DataFrame) -> None:
    '''Render predictive analytics section.'''
    with st.expander('Predictive Analytics Overview', expanded=True):
        st.markdown('#### Predictive Analytics')

        monthly_df, forecast_month, forecast_value = (
            prepare_monthly_forecast_data(df)
        )

        if monthly_df.empty or forecast_month is None or forecast_value is None:
            st.info(
                'At least 2 months of data are required to forecast '
                "next month's spending."
            )
            return

        last_actual = safe_float(monthly_df['amount'].iloc[-1], 0.0)
        change_value = forecast_value - last_actual
        change_pct = (
            (change_value / last_actual * 100) if last_actual > 0 else 0.0
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric('Last Actual Month', f'${last_actual:,.2f}')

        with col2:
            st.metric('Predicted Next Month', f'${forecast_value:,.2f}')

        with col3:
            st.metric('Predicted Change', f'{change_pct:.2f}%')

        forecast_plot_df = pd.concat(
            [
                monthly_df[['month', 'amount']],
                pd.DataFrame(
                    [{'month': forecast_month, 'amount': forecast_value}]
                ),
            ],
            ignore_index=True,
        )

        fig, ax = plt.subplots(figsize=(8.6, 3.8))

        actual_count = len(monthly_df)

        ax.plot(
            range(actual_count),
            monthly_df['amount'],
            marker='o',
            linewidth=2,
            label='Actual',
        )

        ax.plot(
            [actual_count],
            [forecast_value],
            marker='o',
            linestyle='None',
            markersize=7,
            label='Forecast',
        )

        ax.plot(
            [actual_count - 1, actual_count],
            [monthly_df['amount'].iloc[-1], forecast_value],
            linestyle='--',
        )

        ax.set_xticks(range(len(forecast_plot_df)))
        ax.set_xticklabels(
            forecast_plot_df['month'].dt.strftime('%b %Y'),
            rotation=20,
            ha='right',
        )

        format_currency_axis(ax)

        ax.set_ylabel('Amount ($)')
        ax.set_title('Monthly Spending Forecast')
        ax.grid(axis='y', linestyle='--', alpha=0.35)
        ax.legend()

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        fig.tight_layout()
        st.pyplot(fig)

# -----------------------------------------------------------------------------
# MAIN RENDERER
# -----------------------------------------------------------------------------
def render_dashboard_tab() -> None:
    '''Render the Dashboard tab UI.'''
    try:
        st.subheader('Visualizations and Insights')

        df = fetch_df(DB_PATH)

        if df.empty:
            st.warning('No data available.')
            return

        df['tx_date'] = pd.to_datetime(df['tx_date'], errors='coerce')
        df = df.dropna(subset=['tx_date'])

        if df.empty:
            st.warning('No valid data available.')
            return

        st.markdown('### Spending Overview')

        # ---------------------------------------------------------------------
        # DATA PREPARATION
        # ---------------------------------------------------------------------
        daily_df = df.copy()
        daily_df['day'] = daily_df['tx_date'].dt.date
        daily_sum = daily_df.groupby('day', as_index=False)['amount'].sum()

        weekly_df = weekly_summary(df)
        monthly_df = overall_monthly(df)

        col_daily, col_weekly, col_monthly = st.columns(3)

        # ---------------------------------------------------------------------
        # SELECTIONS
        # ---------------------------------------------------------------------
        selected_day_amount = 0.0
        selected_week_amount = 0.0
        selected_month_amount = 0.0

        # Daily
        if not daily_sum.empty:
            daily_sum = daily_sum.sort_values('day')
            day_labels = [d.strftime('%b %d, %Y') for d in daily_sum['day']]

            selected_day = col_daily.selectbox(
                'Select Day',
                day_labels,
                key='dashboard_day',
            )

            idx = day_labels.index(selected_day)
            selected_day_amount = safe_float(
                daily_sum.loc[idx, 'amount'],
                0.0,
            )
        else:
            selected_day = None

        # Weekly
        if not weekly_df.empty:
            week_labels = [
                f'{w.strftime("%b %d")} - '
                f'{(w + pd.Timedelta(days=6)).strftime("%b %d")}'
                for w in weekly_df['week']
            ]

            selected_week = col_weekly.selectbox(
                'Select Week',
                week_labels,
                key='dashboard_week',
            )

            idx = week_labels.index(selected_week)
            selected_week_amount = safe_float(
                weekly_df.loc[idx, 'amount'],
                0.0,
            )
        else:
            selected_week = None

        # Monthly
        if not monthly_df.empty:
            month_labels = monthly_df['month'].dt.strftime('%b %Y').tolist()

            selected_month = col_monthly.selectbox(
                'Select Month',
                month_labels,
                key='dashboard_month',
            )

            idx = month_labels.index(selected_month)
            selected_month_amount = safe_float(
                monthly_df.loc[idx, 'amount'],
                0.0,
            )
        else:
            selected_month = None

        max_value = max(
            selected_day_amount,
            selected_week_amount,
            selected_month_amount,
            10.0,
        )
        ylim_top = max_value * 1.18 if max_value > 0 else 10.0

        chart_w, chart_h = 4.4, 3.2

        # ---------------------------------------------------------------------
        # CHARTS
        # ---------------------------------------------------------------------
        with col_daily:
            if daily_sum.empty or selected_day is None:
                st.info('No daily data available.')
            else:
                render_single_bar_chart(
                    'Daily Spend',
                    selected_day,
                    selected_day_amount,
                    ylim_top,
                    chart_w,
                    chart_h,
                )

        with col_weekly:
            if weekly_df.empty or selected_week is None:
                st.info('No weekly data available.')
            else:
                render_single_bar_chart(
                    'Weekly Spend',
                    selected_week,
                    selected_week_amount,
                    ylim_top,
                    chart_w,
                    chart_h,
                )

        with col_monthly:
            if monthly_df.empty or selected_month is None:
                st.info('No monthly data available.')
            else:
                render_single_bar_chart(
                    'Monthly Spend',
                    selected_month,
                    selected_month_amount,
                    ylim_top,
                    chart_w,
                    chart_h,
                )
        # ---------------------------------------------------------------------
        # FORECAST
        # ---------------------------------------------------------------------
        render_forecast_section(df)

    except Exception as error:
        st.error(f'Error in Dashboard tab: {error}')