# -----------------------------------------------------------------------------
# ANALYTICS MODULE
# -----------------------------------------------------------------------------
'''
Business logic for analytics, KPIs, aggregation, and forecasting.
'''
from __future__ import annotations
from functools import reduce
from typing import Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from app.core.helpers import safe_float

# -----------------------------------------------------------------------------
# DATE FILTERING
# -----------------------------------------------------------------------------
def get_current_month_df(
    df: pd.DataFrame,
    current_ts: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    '''Return rows that belong to the current month.'''
    try:
        if df.empty:
            return df.copy()

        if current_ts is None:
            current_ts = pd.Timestamp.now()

        return df[
            (df['tx_date'].dt.year == current_ts.year)
            & (df['tx_date'].dt.month == current_ts.month)
        ].copy()

    except Exception:
        return pd.DataFrame()

# -----------------------------------------------------------------------------
# KPI CALCULATIONS
# -----------------------------------------------------------------------------
def calculate_kpis(
    df: pd.DataFrame,
    settings: dict,
    current_ts: Optional[pd.Timestamp] = None,
) -> dict:
    '''Calculate current-month KPI values.'''
    try:
        current_month_df = get_current_month_df(df, current_ts)
        monthly_budget = float(settings.get('monthly_budget', 0.0))

        if current_month_df.empty:
            return {
                'total_spending': 0.0,
                'monthly_budget': monthly_budget,
                'remaining_budget': monthly_budget,
                'usage_ratio': 0.0,
                'usage_percent': 0.0,
                'transaction_count': 0,
                'average_spend': 0.0,
            }

        amounts = [
            safe_float(value, 0.0)
            for value in current_month_df['amount'].dropna().tolist()
        ]
        positive_amounts = [value for value in amounts if value >= 0]

        total_spending = reduce(lambda acc, value: acc + value, positive_amounts, 0.0)
        remaining_budget = (
            monthly_budget - total_spending if monthly_budget > 0 else 0.0
        )
        usage_ratio = (
            total_spending / monthly_budget if monthly_budget > 0 else 0.0
        )

        transaction_count = len(positive_amounts)
        average_spend = (
            total_spending / transaction_count if transaction_count > 0 else 0.0
        )

        return {
            'total_spending': total_spending,
            'monthly_budget': monthly_budget,
            'remaining_budget': remaining_budget,
            'usage_ratio': usage_ratio,
            'usage_percent': usage_ratio * 100,
            'transaction_count': transaction_count,
            'average_spend': average_spend,
        }

    except Exception:
        return {
            'total_spending': 0.0,
            'monthly_budget': 0.0,
            'remaining_budget': 0.0,
            'usage_ratio': 0.0,
            'usage_percent': 0.0,
            'transaction_count': 0,
            'average_spend': 0.0,
        }

# -----------------------------------------------------------------------------
# AGGREGATION
# -----------------------------------------------------------------------------
def weekly_summary(df: pd.DataFrame) -> pd.DataFrame:
    '''Aggregate spending by week.'''
    try:
        if df.empty:
            return df.copy()

        working_df = df.copy()
        working_df['week'] = (
            working_df['tx_date']
            - pd.to_timedelta(working_df['tx_date'].dt.weekday, unit='D')
        )

        return working_df.groupby('week', as_index=False)['amount'].sum()

    except Exception:
        return pd.DataFrame()

def overall_monthly(df: pd.DataFrame) -> pd.DataFrame:
    '''Aggregate spending by month.'''
    try:
        if df.empty:
            return df.copy()

        working_df = df.copy()
        working_df['month'] = working_df['tx_date'].dt.to_period('M').dt.start_time

        return working_df.groupby('month', as_index=False)['amount'].sum()

    except Exception:
        return pd.DataFrame()

# -----------------------------------------------------------------------------
# FORECASTING
# -----------------------------------------------------------------------------
def forecast_next(amounts, periods: int = 1) -> list[float]:
    '''Forecast future values using linear regression.'''
    try:
        if len(amounts) < 2:
            return []

        x_values = np.arange(len(amounts)).reshape(-1, 1)
        y_values = np.array(amounts, dtype=float)

        model = LinearRegression()
        model.fit(x_values, y_values)

        future_x = np.arange(len(amounts), len(amounts) + periods).reshape(-1, 1)
        predictions = model.predict(future_x)

        return [float(max(prediction, 0.0)) for prediction in predictions]

    except Exception:
        return []

def prepare_monthly_forecast_data(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, Optional[pd.Timestamp], Optional[float]]:
    '''Prepare monthly totals and a next-month forecast.'''
    try:
        if df.empty:
            return pd.DataFrame(), None, None

        monthly_df = overall_monthly(df).sort_values('month').reset_index(drop=True)

        if len(monthly_df) < 2:
            return monthly_df, None, None

        amounts = [safe_float(value, 0.0) for value in monthly_df['amount']]
        amounts = [value for value in amounts if value >= 0]

        if len(amounts) < 2:
            return monthly_df, None, None

        forecast_values = forecast_next(amounts, periods=1)

        if not forecast_values:
            return monthly_df, None, None

        last_month = monthly_df['month'].max()
        next_month = (
            pd.Timestamp(last_month) + pd.offsets.MonthBegin(1)
        ).to_period('M').to_timestamp()

        return monthly_df, next_month, forecast_values[0]

    except Exception:
        return pd.DataFrame(), None, None

# -----------------------------------------------------------------------------
# CATEGORY ANALYSIS
# -----------------------------------------------------------------------------
def calculate_category_totals_with_reduce(df: pd.DataFrame) -> dict:
    '''Calculate total spending per category.'''
    try:
        if df.empty:
            return {}

        records = df[['category', 'amount']].dropna().to_dict('records')

        clean_records = [
            {
                'category': str(row.get('category', '')).strip(),
                'amount': safe_float(row.get('amount', 0.0)),
            }
            for row in records
        ]

        valid_records = [
            row
            for row in clean_records
            if row['category'] != '' and row['amount'] >= 0
        ]

        totals = reduce(
            lambda acc, row: {
                **acc,
                row['category']: acc.get(row['category'], 0.0) + row['amount'],
            },
            valid_records,
            {},
        )

        return totals

    except Exception:
        return {}

def get_top_category_summary(
    df: pd.DataFrame,
) -> tuple[Optional[str], float, float]:
    '''Return the top spending category.'''
    try:
        totals = calculate_category_totals_with_reduce(df)

        if not totals:
            return None, 0.0, 0.0

        sorted_items = sorted(
            totals.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        top_category, top_amount = sorted_items[0]
        total_amount = reduce(lambda acc, item: acc + item[1], sorted_items, 0.0)
        share = (top_amount / total_amount * 100) if total_amount > 0 else 0.0

        return top_category, top_amount, share

    except Exception:
        return None, 0.0, 0.0