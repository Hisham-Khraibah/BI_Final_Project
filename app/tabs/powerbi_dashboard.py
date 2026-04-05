# -----------------------------------------------------------------------------
# POWER BI DASHBOARD TAB
# -----------------------------------------------------------------------------
'''
Streamlit UI for executive KPI cards, monthly trends, category analysis,
vendor analysis.
'''
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from matplotlib.ticker import FuncFormatter

from app.core.budget_logic import load_budget_settings
from app.core.config import BUDGET_PATH, DB_PATH
from app.core.database import fetch_df
from app.ui.components import render_metric_card

# -----------------------------------------------------------------------------
# KPI & ANALYTICS
# -----------------------------------------------------------------------------
def calculate_power_bi_kpis(df: pd.DataFrame, monthly_budget: float) -> dict:
    '''Calculate executive KPI values for the selected year.'''
    try:
        if df.empty:
            return {
                'total_spending': 0.0,
                'transaction_count': 0,
                'average_spend': 0.0,
                'highest_expense': 0.0,
                'remaining_budget': 0.0,
                'budget_usage_percent': 0.0,
            }

        amounts = pd.to_numeric(df['amount'], errors='coerce').dropna()
        amounts = amounts[amounts >= 0]

        total_spending = float(amounts.sum())
        transaction_count = int(len(amounts))
        average_spend = (
            float(total_spending / transaction_count)
            if transaction_count > 0
            else 0.0
        )
        highest_expense = float(amounts.max()) if transaction_count > 0 else 0.0

        unique_months = 0

        if 'tx_date' in df.columns:
            tx_dates = pd.to_datetime(df['tx_date'], errors='coerce').dropna()

            if not tx_dates.empty:
                unique_months = int(tx_dates.dt.to_period('M').nunique())

        effective_budget = (
            float(monthly_budget) * unique_months
            if monthly_budget > 0
            else 0.0
        )
        remaining_budget = (
            effective_budget - total_spending
            if effective_budget > 0
            else 0.0
        )
        budget_usage_percent = (
            (total_spending / effective_budget) * 100
            if effective_budget > 0
            else 0.0
        )

        return {
            'total_spending': total_spending,
            'transaction_count': transaction_count,
            'average_spend': average_spend,
            'highest_expense': highest_expense,
            'remaining_budget': remaining_budget,
            'budget_usage_percent': budget_usage_percent,
        }

    except Exception:
        return {
            'total_spending': 0.0,
            'transaction_count': 0,
            'average_spend': 0.0,
            'highest_expense': 0.0,
            'remaining_budget': 0.0,
            'budget_usage_percent': 0.0,
        }

def build_monthly_trend_df(df: pd.DataFrame) -> pd.DataFrame:
    '''Build the monthly trend dataframe.'''
    try:
        if df.empty:
            return pd.DataFrame(columns=['Month', 'Amount', 'month_date'])

        trend_df = df.copy()
        trend_df['tx_date'] = pd.to_datetime(trend_df['tx_date'], errors='coerce')
        trend_df['amount'] = pd.to_numeric(trend_df['amount'], errors='coerce')
        trend_df = trend_df.dropna(subset=['tx_date', 'amount'])

        if trend_df.empty:
            return pd.DataFrame(columns=['Month', 'Amount', 'month_date'])

        trend_df['month_date'] = trend_df['tx_date'].dt.to_period('M').dt.to_timestamp()

        monthly_df = (
            trend_df.groupby('month_date', as_index=False)['amount']
            .sum()
            .sort_values('month_date')
            .reset_index(drop=True)
        )

        monthly_df['Month'] = monthly_df['month_date'].dt.strftime('%b %Y')
        monthly_df = monthly_df.rename(columns={'amount': 'Amount'})

        return monthly_df[['Month', 'Amount', 'month_date']]

    except Exception:
        return pd.DataFrame(columns=['Month', 'Amount', 'month_date'])

def build_category_analysis_df(df: pd.DataFrame) -> pd.DataFrame:
    '''Build the category summary dataframe.'''
    try:
        if df.empty or 'category' not in df.columns:
            return pd.DataFrame(columns=['Category', 'Amount', 'Share %'])

        category_df = df.copy()
        category_df['amount'] = pd.to_numeric(category_df['amount'], errors='coerce')
        category_df['category'] = (
            category_df['category']
            .fillna('')
            .astype(str)
            .str.strip()
        )
        category_df = category_df.dropna(subset=['amount'])
        category_df = category_df[
            (category_df['amount'] >= 0) & (category_df['category'] != '')
        ]

        if category_df.empty:
            return pd.DataFrame(columns=['Category', 'Amount', 'Share %'])

        category_df = (
            category_df.groupby('category', as_index=False)['amount']
            .sum()
            .sort_values('amount', ascending=False)
            .reset_index(drop=True)
        )

        total_amount = float(category_df['amount'].sum())
        category_df['Share %'] = category_df['amount'].apply(
            lambda value: (float(value) / total_amount * 100)
            if total_amount > 0
            else 0.0
        )

        category_df = category_df.rename(
            columns={
                'category': 'Category',
                'amount': 'Amount',
            }
        )

        return category_df[['Category', 'Amount', 'Share %']]

    except Exception:
        return pd.DataFrame(columns=['Category', 'Amount', 'Share %'])

def build_vendor_analysis_df(df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    '''Build the top vendor summary dataframe.'''
    try:
        if df.empty or 'merchant' not in df.columns:
            return pd.DataFrame(columns=['Vendor', 'Amount'])

        vendor_df = df.copy()
        vendor_df['amount'] = pd.to_numeric(vendor_df['amount'], errors='coerce')
        vendor_df['merchant'] = (
            vendor_df['merchant']
            .fillna('')
            .astype(str)
            .str.strip()
        )
        vendor_df = vendor_df.dropna(subset=['amount'])
        vendor_df = vendor_df[
            (vendor_df['amount'] >= 0) & (vendor_df['merchant'] != '')
        ]

        if vendor_df.empty:
            return pd.DataFrame(columns=['Vendor', 'Amount'])

        vendor_df = (
            vendor_df.groupby('merchant', as_index=False)['amount']
            .sum()
            .sort_values('amount', ascending=False)
            .head(top_n)
            .reset_index(drop=True)
        )

        vendor_df = vendor_df.rename(
            columns={
                'merchant': 'Vendor',
                'amount': 'Amount',
            }
        )

        return vendor_df[['Vendor', 'Amount']]

    except Exception:
        return pd.DataFrame(columns=['Vendor', 'Amount'])

# -----------------------------------------------------------------------------
# DASHBOARD RENDERER
# -----------------------------------------------------------------------------
def render_power_bi_dashboard(df: pd.DataFrame, budget_settings: dict) -> None:
    '''Render the Power BI-style dashboard.'''
    try:
        st.subheader('Power BI Dashboard')

        if df.empty:
            st.info('No data available for Power BI Dashboard.')
            return

        power_df = df.copy()
        power_df['tx_date'] = pd.to_datetime(power_df['tx_date'], errors='coerce')
        power_df = power_df.dropna(subset=['tx_date'])

        power_df['amount'] = pd.to_numeric(power_df['amount'], errors='coerce')
        power_df = power_df.dropna(subset=['amount'])

        if power_df.empty:
            st.info('No valid records available for Power BI Dashboard.')
            return

        available_years = sorted(power_df['tx_date'].dt.year.unique(), reverse=True)

        selected_year = st.selectbox(
            'Select Year',
            available_years,
            key='power_bi_selected_year',
        )

        filtered_df = power_df[power_df['tx_date'].dt.year == selected_year].copy()

        if filtered_df.empty:
            st.info('No data available for the selected year.')
            return

        monthly_budget = float(budget_settings.get('monthly_budget', 0.0))
        power_kpis = calculate_power_bi_kpis(filtered_df, monthly_budget)

        st.markdown('### Executive KPI Cards')

        kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5, kpi_col6 = st.columns(6)

        with kpi_col1:
            render_metric_card(
                'Total Spending',
                f'${power_kpis["total_spending"]:,.2f}',
                'Selected year total',
            )

        with kpi_col2:
            render_metric_card(
                'Transactions',
                f'{power_kpis["transaction_count"]}',
                'Valid expense rows',
            )

        with kpi_col3:
            render_metric_card(
                'Average Spend',
                f'${power_kpis["average_spend"]:,.2f}',
                'Average per transaction',
            )

        with kpi_col4:
            render_metric_card(
                'Highest Expense',
                f'${power_kpis["highest_expense"]:,.2f}',
                'Largest single expense',
            )

        with kpi_col5:
            render_metric_card(
                'Remaining Budget',
                f'${power_kpis["remaining_budget"]:,.2f}',
                'Budget vs selected year',
            )

        with kpi_col6:
            render_metric_card(
                'Budget Usage',
                f'{power_kpis["budget_usage_percent"]:.2f}%',
                'Budget consumption',
            )

        st.markdown('---')
        st.markdown('### Monthly Trend Analysis')

        monthly_trend_df = build_monthly_trend_df(filtered_df)

        if monthly_trend_df.empty:
            st.info('No monthly trend data available.')
        else:
            fig_monthly, ax_monthly = plt.subplots(figsize=(10.5, 4.2))
            x_values = np.arange(len(monthly_trend_df))

            ax_monthly.plot(
                x_values,
                monthly_trend_df['Amount'],
                linewidth=2.5,
                marker='o',
                markersize=6,
            )

            ax_monthly.fill_between(
                x_values,
                monthly_trend_df['Amount'],
                alpha=0.15,
            )

            ax_monthly.set_xticks(x_values)
            ax_monthly.set_xticklabels(
                monthly_trend_df['Month'],
                rotation=30,
                ha='right',
            )
            ax_monthly.set_ylabel('Amount ($)')
            ax_monthly.set_title('Monthly Spending Trend')
            ax_monthly.yaxis.set_major_formatter(
                FuncFormatter(lambda y_value, _: f'${y_value:,.0f}')
            )
            ax_monthly.grid(axis='y', linestyle='--', alpha=0.35)
            fig_monthly.tight_layout()

            st.pyplot(fig_monthly, width='stretch')

            monthly_display_df = monthly_trend_df[['Month', 'Amount']].copy()
            monthly_display_df['Amount'] = monthly_display_df['Amount'].map(
                lambda value: f'${value:,.2f}'
            )

            st.dataframe(monthly_display_df, hide_index=True, width='stretch')

        st.markdown('---')
        st.markdown('### Category Analysis')

        category_analysis_df = build_category_analysis_df(filtered_df)

        if category_analysis_df.empty:
            st.info('No category analysis data available.')
        else:
            cat_col1, cat_col2 = st.columns([1.15, 1])

            with cat_col1:
                fig_cat_bar, ax_cat_bar = plt.subplots(figsize=(8.5, 4.2))
                x_positions = np.arange(len(category_analysis_df))

                ax_cat_bar.bar(
                    x_positions,
                    category_analysis_df['Amount'],
                    width=0.6,
                )
                ax_cat_bar.set_title('Category Spending Comparison')
                ax_cat_bar.set_ylabel('Amount ($)')
                ax_cat_bar.yaxis.set_major_formatter(
                    FuncFormatter(lambda y_value, _: f'${y_value:,.0f}')
                )
                ax_cat_bar.set_xticks(x_positions)
                ax_cat_bar.set_xticklabels(
                    category_analysis_df['Category'],
                    rotation=35,
                    ha='right',
                )
                ax_cat_bar.grid(axis='y', linestyle='--', alpha=0.35)
                fig_cat_bar.tight_layout()

                st.pyplot(fig_cat_bar, width='stretch')

            with cat_col2:
                fig_cat_pie, ax_cat_pie = plt.subplots(figsize=(6.2, 4.2))

                ax_cat_pie.pie(
                    category_analysis_df['Amount'],
                    labels=None,
                    autopct=lambda pct: f'{pct:.1f}%' if pct >= 3 else '',
                    startangle=90,
                    wedgeprops={'linewidth': 1, 'edgecolor': 'white'},
                    textprops={'fontsize': 8},
                )
                ax_cat_pie.legend(
                    category_analysis_df['Category'],
                    loc='center left',
                    bbox_to_anchor=(1.0, 0.5),
                    frameon=False,
                    fontsize=8,
                    title='Category',
                )
                ax_cat_pie.set_title('Category Share')
                ax_cat_pie.axis('equal')
                fig_cat_pie.tight_layout()

                st.pyplot(fig_cat_pie, width='stretch')

            category_display_df = category_analysis_df.copy()
            category_display_df['Amount'] = category_display_df['Amount'].map(
                lambda value: f'${value:,.2f}'
            )
            category_display_df['Share %'] = category_display_df['Share %'].map(
                lambda value: f'{value:.2f}%'
            )

            st.dataframe(category_display_df, hide_index=True, width='stretch')

        st.markdown('---')
        st.markdown('### Top Vendor Analysis')

        vendor_df = build_vendor_analysis_df(filtered_df, top_n=5)

        if vendor_df.empty:
            st.info('No vendor analysis data available.')
        else:
            fig_vendor, ax_vendor = plt.subplots(figsize=(8.8, 4.0))

            ax_vendor.barh(vendor_df['Vendor'], vendor_df['Amount'])
            ax_vendor.invert_yaxis()
            ax_vendor.set_title('Top 5 Vendors by Spending')
            ax_vendor.set_xlabel('Amount ($)')
            ax_vendor.xaxis.set_major_formatter(
                FuncFormatter(lambda x_value, _: f'${x_value:,.0f}')
            )
            ax_vendor.grid(axis='x', linestyle='--', alpha=0.35)
            fig_vendor.tight_layout()

            st.pyplot(fig_vendor, width='stretch')

            vendor_display_df = vendor_df.copy()
            vendor_display_df['Amount'] = vendor_display_df['Amount'].map(
                lambda value: f'${value:,.2f}'
            )

            st.dataframe(vendor_display_df, hide_index=True, width='stretch')

    except Exception as error:
        st.error(f'Error rendering Power BI Dashboard tab: {error}')

# -----------------------------------------------------------------------------
# MAIN RENDERER
# -----------------------------------------------------------------------------
def render_power_bi_dashboard_tab() -> None:
    '''Render the Power BI Dashboard tab.'''
    try:
        df = fetch_df(DB_PATH)
        budget_settings = load_budget_settings(BUDGET_PATH)
        render_power_bi_dashboard(df, budget_settings)

    except Exception as error:
        st.error(f'Error in Power BI Dashboard tab: {error}')