# -----------------------------------------------------------------------------
# BUDGET LOGIC MODULE
# -----------------------------------------------------------------------------
'''
Business logic for budget settings, calculations, alerts, and progress tracking.
'''
from __future__ import annotations
import json
import os
from typing import Any, Optional
import pandas as pd
import streamlit as st
from app.core.email_utils import send_email
from app.core.helpers import safe_float

# -----------------------------------------------------------------------------
# JSON READ / WRITE
# -----------------------------------------------------------------------------
def safe_read_json(path: str, default_value: Any) -> Any:
    '''Safely read a JSON file.'''
    try:
        if not os.path.exists(path):
            return default_value

        with open(path, 'r', encoding='utf-8') as file:
            return json.load(file)

    except Exception:
        return default_value

def safe_write_json(path: str, data: Any) -> bool:
    '''Safely write a JSON file.'''
    try:
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2)

        return True

    except Exception:
        return False

# -----------------------------------------------------------------------------
# DATA CLEANING
# -----------------------------------------------------------------------------
def get_clean_non_negative_amounts(df: pd.DataFrame) -> pd.Series:
    '''Return a numeric Series of non-negative amounts.'''
    try:
        if df.empty or 'amount' not in df.columns:
            return pd.Series(dtype=float)

        amounts = pd.to_numeric(df['amount'], errors='coerce').dropna()
        return amounts[amounts >= 0]

    except Exception:
        return pd.Series(dtype=float)

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
# BUDGET SETTINGS
# -----------------------------------------------------------------------------
def load_budget_settings(budget_path: str) -> dict:
    '''
    Load budget settings from JSON.

    Returns:
        {
            'monthly_budget': float,
            'category_budgets': dict,
        }
    '''
    try:
        default_data = {
            'monthly_budget': 0.0,
            'category_budgets': {},
        }

        data = safe_read_json(budget_path, default_data)

        if 'monthly_budget' not in data:
            data['monthly_budget'] = 0.0

        if 'category_budgets' not in data:
            data['category_budgets'] = {}

        return data

    except Exception:
        return {
            'monthly_budget': 0.0,
            'category_budgets': {},
        }

def save_budget_settings(
    budget_path: str,
    monthly_budget: Any,
    category_budgets: dict,
) -> bool:
    '''Save budget settings to JSON.'''
    try:
        data = {
            'monthly_budget': safe_float(monthly_budget),
            'category_budgets': category_budgets,
        }
        return safe_write_json(budget_path, data)

    except Exception:
        return False

# -----------------------------------------------------------------------------
# BUDGET PROGRESS & STATUS
# -----------------------------------------------------------------------------
def get_budget_status_label(usage_pct: float) -> str:
    '''Convert budget usage percentage into a status label.'''
    try:
        if usage_pct > 100:
            return 'Over Budget'

        if usage_pct >= 80:
            return 'Warning'

        return 'On Track'

    except Exception:
        return 'Unknown'

def calculate_budget_progress(spent: float, budget: float) -> dict:
    '''
    Calculate budget progress values.

    Returns:
        {
            'spent': float,
            'budget': float,
            'usage_pct': float,
            'progress_value': float,
            'remaining': float,
            'status': str,
        }
    '''
    try:
        spent = safe_float(spent, 0.0)
        budget = safe_float(budget, 0.0)

        if budget <= 0:
            return {
                'spent': spent,
                'budget': budget,
                'usage_pct': 0.0,
                'progress_value': 0.0,
                'remaining': 0.0,
                'status': 'No Budget',
            }

        usage_pct = (spent / budget) * 100
        progress_value = min(max(spent / budget, 0.0), 1.0)
        remaining = budget - spent
        status = get_budget_status_label(usage_pct)

        return {
            'spent': spent,
            'budget': budget,
            'usage_pct': usage_pct,
            'progress_value': progress_value,
            'remaining': remaining,
            'status': status,
        }

    except Exception:
        return {
            'spent': 0.0,
            'budget': 0.0,
            'usage_pct': 0.0,
            'progress_value': 0.0,
            'remaining': 0.0,
            'status': 'Unknown',
        }

# -----------------------------------------------------------------------------
# KPI CALCULATIONS
# -----------------------------------------------------------------------------
def calculate_kpis(
    df: pd.DataFrame,
    settings: dict,
    current_ts: Optional[pd.Timestamp] = None,
) -> dict:
    '''Calculate current-month KPI values for budget monitoring.'''
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

        amounts = get_clean_non_negative_amounts(current_month_df)
        total_spending = float(amounts.sum())
        transaction_count = int(len(amounts))
        average_spend = (
            float(total_spending / transaction_count)
            if transaction_count > 0
            else 0.0
        )
        remaining_budget = (
            monthly_budget - total_spending if monthly_budget > 0 else 0.0
        )
        usage_ratio = (
            total_spending / monthly_budget if monthly_budget > 0 else 0.0
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
# EMAIL NOTIFICATION
# -----------------------------------------------------------------------------
def send_overall_budget_email(
    status: str,
    total_spent: float,
    monthly_budget: float,
    usage_pct: float,
) -> None:
    '''Send the overall monthly budget email once per session per status.'''
    try:
        session_key = f'email_overall_{status.lower()}_sent'

        if session_key in st.session_state:
            return

        subject = f'Overall Monthly Budget {status}'
        body = (
            f'Your overall monthly budget status is now: {status}\n\n'
            f'Total spent: ${total_spent:,.2f}\n'
            f'Monthly budget: ${monthly_budget:,.2f}\n'
            f'Usage: {usage_pct:.2f}%\n'
        )

        if send_email(subject, body):
            st.session_state[session_key] = True

    except Exception:
        pass

def send_category_budget_email(
    status: str,
    category: str,
    spent: float,
    budget: float,
    usage_pct: float,
) -> None:
    '''Send the category budget email once per session per category and status.'''
    try:
        session_key = (
            f'email_category_{status.lower()}_sent_'
            f'{category.strip().lower()}'
        )

        if session_key in st.session_state:
            return

        subject = f'Category Budget {status} - {category}'
        body = (
            f'The budget status for category "{category}" is now: {status}\n\n'
            f'Total spent: ${spent:,.2f}\n'
            f'Category budget: ${budget:,.2f}\n'
            f'Usage: {usage_pct:.2f}%\n'
        )

        if send_email(subject, body):
            st.session_state[session_key] = True

    except Exception:
        pass

# -----------------------------------------------------------------------------
# ALERTS
# -----------------------------------------------------------------------------
def build_budget_alerts(
    df: pd.DataFrame,
    settings: dict,
    current_ts: Optional[pd.Timestamp] = None,
) -> list[dict]:
    '''
    Build budget alerts for the current month.

    Returns:
        List of dicts:
        {
            'type': 'error' | 'warning' | 'success',
            'title': str,
            'message': str,
        }
    '''
    try:
        alerts: list[dict] = []
        current_month_df = get_current_month_df(df, current_ts)

        amounts = get_clean_non_negative_amounts(current_month_df)
        total_spent = float(amounts.sum())
        monthly_budget = float(settings.get('monthly_budget', 0.0))

        if monthly_budget > 0:
            usage_pct = (total_spent / monthly_budget) * 100

            if usage_pct > 100:
                alert_type = 'error'
                status = 'Exceeded'
                title = 'Overall Monthly Budget Exceeded'
                send_overall_budget_email(
                    status=status,
                    total_spent=total_spent,
                    monthly_budget=monthly_budget,
                    usage_pct=usage_pct,
                )
            elif usage_pct >= 80:
                alert_type = 'warning'
                status = 'Warning'
                title = 'Overall Monthly Budget Warning'
                send_overall_budget_email(
                    status=status,
                    total_spent=total_spent,
                    monthly_budget=monthly_budget,
                    usage_pct=usage_pct,
                )
            else:
                alert_type = 'success'
                title = 'Overall Monthly Budget Status'

            alerts.append(
                {
                    'type': alert_type,
                    'title': title,
                    'message': (
                        f'You spent ${total_spent:,.2f} out of '
                        f'${monthly_budget:,.2f} ({usage_pct:.2f}%).'
                    ),
                }
            )

        category_budgets = settings.get('category_budgets', {})

        if current_month_df.empty or not category_budgets:
            return alerts

        working_df = current_month_df.copy()
        working_df['amount'] = pd.to_numeric(working_df['amount'], errors='coerce')
        working_df = working_df.dropna(subset=['amount'])
        working_df = working_df[working_df['amount'] >= 0]

        category_spend = (
            working_df.groupby('category', as_index=False)['amount'].sum()
        )

        for _, row in category_spend.iterrows():
            category = str(row['category'])
            spent = float(row['amount'])
            budget = float(category_budgets.get(category, 0.0))

            if budget <= 0:
                continue

            usage_pct = (spent / budget) * 100

            if usage_pct > 100:
                alert_type = 'error'
                status = 'Exceeded'
                title = f'Category Budget Exceeded - {category}'
                send_category_budget_email(
                    status=status,
                    category=category,
                    spent=spent,
                    budget=budget,
                    usage_pct=usage_pct,
                )
            elif usage_pct >= 80:
                alert_type = 'warning'
                status = 'Warning'
                title = f'Category Budget Warning - {category}'
                send_category_budget_email(
                    status=status,
                    category=category,
                    spent=spent,
                    budget=budget,
                    usage_pct=usage_pct,
                )
            else:
                alert_type = 'success'
                title = f'Category Budget Status - {category}'

            alerts.append(
                {
                    'type': alert_type,
                    'title': title,
                    'message': (
                        f'You spent ${spent:,.2f} out of '
                        f'${budget:,.2f} ({usage_pct:.2f}%).'
                    ),
                }
            )

        return alerts

    except Exception:
        return []

def get_budget_popup_messages(
    df: pd.DataFrame,
    settings: dict,
    current_ts: Optional[pd.Timestamp] = None,
) -> list[dict]:
    '''
    Build exceeded-budget popup messages.

    Returns:
        List of dicts:
        {
            'title': str,
            'message': str,
        }
    '''
    try:
        popups: list[dict] = []
        current_month_df = get_current_month_df(df, current_ts)

        if current_month_df.empty:
            return popups

        amounts = get_clean_non_negative_amounts(current_month_df)
        total_spent = float(amounts.sum())
        monthly_budget = float(settings.get('monthly_budget', 0.0))

        if monthly_budget > 0 and total_spent > monthly_budget:
            popups.append(
                {
                    'title': 'Overall Monthly Budget Exceeded',
                    'message': (
                        f'You spent ${total_spent:,.2f} '
                        f'out of ${monthly_budget:,.2f}.'
                    ),
                }
            )

        category_budgets = settings.get('category_budgets', {})

        if not category_budgets:
            return popups

        working_df = current_month_df.copy()
        working_df['amount'] = pd.to_numeric(working_df['amount'], errors='coerce')
        working_df = working_df.dropna(subset=['amount'])
        working_df = working_df[working_df['amount'] >= 0]

        category_spend = (
            working_df.groupby('category', as_index=False)['amount'].sum()
        )

        for _, row in category_spend.iterrows():
            category = str(row['category'])
            spent = float(row['amount'])
            budget = float(category_budgets.get(category, 0.0))

            if budget > 0 and spent > budget:
                popups.append(
                    {
                        'title': f'Category Budget Exceeded - {category}',
                        'message': f'You spent ${spent:,.2f} out of ${budget:,.2f}.',
                    }
                )

        return popups

    except Exception:
        return []

# -----------------------------------------------------------------------------
# CATEGORY BUDGET OVERVIEW
# -----------------------------------------------------------------------------
def build_category_budget_overview(
    df: pd.DataFrame,
    settings: dict,
    current_ts: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    '''Build a category budget overview dataframe for the UI.'''
    try:
        current_month_df = get_current_month_df(df, current_ts)

        if current_month_df.empty:
            return pd.DataFrame()

        working_df = current_month_df.copy()
        working_df['amount'] = pd.to_numeric(working_df['amount'], errors='coerce')
        working_df = working_df.dropna(subset=['amount'])
        working_df = working_df[working_df['amount'] >= 0]

        category_spend = (
            working_df.groupby('category', as_index=False)['amount'].sum()
        )

        if category_spend.empty:
            return pd.DataFrame()

        rows = []

        for _, row in category_spend.iterrows():
            category = str(row['category'])
            spent = float(row['amount'])
            budget = float(settings.get('category_budgets', {}).get(category, 0.0))

            usage = (spent / budget * 100) if budget > 0 else 0.0
            remaining = (budget - spent) if budget > 0 else 0.0
            status = get_budget_status_label(usage) if budget > 0 else '-'

            rows.append(
                {
                    'Category': category,
                    'Spent': spent,
                    'Budget': budget,
                    'Remaining': remaining if budget > 0 else None,
                    'Usage %': usage if budget > 0 else None,
                    'Status': status,
                }
            )

        return pd.DataFrame(rows)

    except Exception:
        return pd.DataFrame()