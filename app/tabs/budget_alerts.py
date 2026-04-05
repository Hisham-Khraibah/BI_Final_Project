# -----------------------------------------------------------------------------
# BUDGET ALERTS TAB
# -----------------------------------------------------------------------------
'''
Streamlit UI for budget settings, alerts, and category budget overview.
'''
from __future__ import annotations
import pandas as pd
import streamlit as st
from app.core.budget_logic import (
    build_budget_alerts,
    build_category_budget_overview,
    load_budget_settings,
    save_budget_settings,
)
from app.core.categories import get_all_categories
from app.core.config import BUDGET_PATH, CUSTOM_CAT_PATH, DB_PATH
from app.core.database import fetch_df
from app.core.helpers import safe_float

# -----------------------------------------------------------------------------
# SESSION STATE
# -----------------------------------------------------------------------------
def init_budget_alerts_state() -> None:
    '''Initialize session state values used by the Budget Alerts tab.'''
    if 'budget_saved_message' not in st.session_state:
        st.session_state['budget_saved_message'] = ''

    if 'budget_alerts_dismissed' not in st.session_state:
        st.session_state['budget_alerts_dismissed'] = False

    if 'budget_input_version' not in st.session_state:
        st.session_state['budget_input_version'] = 0

    if 'budget_form_defaults' not in st.session_state:
        st.session_state['budget_form_defaults'] = {
            'monthly_budget': 0.0,
            'category_budgets': {},
        }

# -----------------------------------------------------------------------------
# FORM DEFAULTS
# -----------------------------------------------------------------------------
def initialize_budget_form_defaults(saved_budget_settings: dict) -> None:
    '''Initialize form defaults from saved settings when needed.'''
    form_defaults = st.session_state['budget_form_defaults']

    has_default_budget = (
        safe_float(form_defaults.get('monthly_budget', 0.0), 0.0) > 0.0
    )
    has_default_categories = bool(form_defaults.get('category_budgets'))

    if has_default_budget or has_default_categories:
        return

    st.session_state['budget_form_defaults'] = {
        'monthly_budget': safe_float(
            saved_budget_settings.get('monthly_budget', 0.0),
            0.0,
        ),
        'category_budgets': dict(saved_budget_settings.get('category_budgets', {})),
    }

def build_effective_budget_settings(
    monthly_budget_input: float,
    updated_category_budgets: dict[str, float],
) -> dict:
    '''Build cleaned budget settings from the current form values.'''
    return {
        'monthly_budget': float(monthly_budget_input),
        'category_budgets': {
            category: float(amount)
            for category, amount in updated_category_budgets.items()
            if float(amount) > 0
        },
    }

# -----------------------------------------------------------------------------
# BUDGET SETTINGS FORM
# -----------------------------------------------------------------------------
def render_budget_settings_form(
    all_categories: list[str],
    saved_budget_settings: dict,
) -> dict:
    '''Render the monthly and category budget inputs and return live settings.'''
    initialize_budget_form_defaults(saved_budget_settings)

    form_defaults = st.session_state['budget_form_defaults']
    input_version = st.session_state['budget_input_version']

    st.markdown('### Set Monthly Budget')

    monthly_budget_input = st.number_input(
        'Overall Monthly Budget',
        min_value=0.0,
        value=safe_float(form_defaults.get('monthly_budget', 0.0), 0.0),
        step=10.0,
        format='%.2f',
        key=f'overall_monthly_budget_{input_version}',
    )

    current_category_budgets = form_defaults.get('category_budgets', {})
    updated_category_budgets: dict[str, float] = {}

    with st.expander('Set Category Budgets', expanded=False):
        for category in all_categories:
            updated_category_budgets[category] = st.number_input(
                f'{category} Budget',
                min_value=0.0,
                value=float(current_category_budgets.get(category, 0.0)),
                step=10.0,
                format='%.2f',
                key=f'budget_{category}_{input_version}',
            )

    col1, col2 = st.columns(2)

    with col1:
        if st.button('Save Budget Settings', use_container_width=True):
            settings = build_effective_budget_settings(
                monthly_budget_input,
                updated_category_budgets,
            )

            if save_budget_settings(
                BUDGET_PATH,
                settings['monthly_budget'],
                settings['category_budgets'],
            ):
                st.session_state['budget_form_defaults'] = settings
                st.session_state['budget_saved_message'] = 'Saved successfully'
                st.session_state['budget_alerts_dismissed'] = False
                st.rerun()

            st.error('Save failed')

    with col2:
        if st.button('Clear All Budgets', use_container_width=True):
            if save_budget_settings(BUDGET_PATH, 0.0, {}):
                st.session_state['budget_form_defaults'] = {
                    'monthly_budget': 0.0,
                    'category_budgets': {},
                }
                st.session_state['budget_input_version'] += 1
                st.session_state['budget_saved_message'] = 'Cleared'
                st.session_state['budget_alerts_dismissed'] = False
                st.rerun()

            st.error('Clear failed')

    return build_effective_budget_settings(
        monthly_budget_input,
        updated_category_budgets,
    )

# -----------------------------------------------------------------------------
# ALERTS
# -----------------------------------------------------------------------------
def render_alerts_section(df: pd.DataFrame, settings: dict) -> None:
    '''Render the alerts section.'''
    with st.expander('Alerts', expanded=True):
        alerts = build_budget_alerts(df, settings)

        if alerts and not st.session_state['budget_alerts_dismissed']:
            for alert in alerts:
                message = f'{alert["title"]} - {alert["message"]}'

                if alert['type'] == 'error':
                    st.error(message)
                elif alert['type'] == 'warning':
                    st.warning(message)
                else:
                    st.success(message)

            if st.button('Dismiss Budget Alert'):
                st.session_state['budget_alerts_dismissed'] = True
                st.rerun()
        else:
            st.info('No alerts')

# -----------------------------------------------------------------------------
# CATEGORY OVERVIEW
# -----------------------------------------------------------------------------
def render_category_budget_overview(df: pd.DataFrame, settings: dict) -> None:
    '''Render the category budget overview section.'''
    with st.expander('Category Budget Overview', expanded=True):
        overview_df = build_category_budget_overview(df, settings)

        if overview_df.empty:
            st.info('No data')
            return

        st.markdown('#### Category Budget Overview')

        headers = ['Category', 'Progress', 'Spent', 'Budget', 'Usage %', 'Status']
        header_cols = st.columns([2.2, 3, 1.3, 1.3, 1.2, 1.6])

        for column, header in zip(header_cols, headers):
            with column:
                st.markdown(
                    (
                        "<div style='text-align:center;font-weight:600;'>"
                        f'{header}'
                        '</div>'
                    ),
                    unsafe_allow_html=True,
                )

        st.markdown('---')

        for _, row in overview_df.iterrows():
            render_category_budget_row(row)

def render_category_budget_row(row: pd.Series) -> None:
    '''Render a single category budget overview row.'''
    category = str(row['Category'])
    spent = float(row['Spent'])
    budget = 0.0 if pd.isna(row['Budget']) else float(row['Budget'])
    usage = None if pd.isna(row['Usage %']) else float(row['Usage %'])
    status = str(row['Status'])

    row_cols = st.columns([2.2, 3, 1.3, 1.3, 1.2, 1.6])

    with row_cols[0]:
        st.markdown(
            f"<div style='text-align:center'>{category}</div>",
            unsafe_allow_html=True,
        )

    with row_cols[1]:
        if budget > 0:
            st.progress(min(max(spent / budget, 0.0), 1.0))
        else:
            st.markdown(
                "<div style='text-align:center;color:gray'>No budget</div>",
                unsafe_allow_html=True,
            )

    with row_cols[2]:
        st.markdown(
            f"<div style='text-align:center'>${spent:,.2f}</div>",
            unsafe_allow_html=True,
        )

    with row_cols[3]:
        budget_text = f'${budget:,.2f}' if budget > 0 else '-'
        st.markdown(
            f"<div style='text-align:center'>{budget_text}</div>",
            unsafe_allow_html=True,
        )

    with row_cols[4]:
        usage_text = f'{usage:.2f}%' if usage is not None else '-'
        st.markdown(
            f"<div style='text-align:center'>{usage_text}</div>",
            unsafe_allow_html=True,
        )

    with row_cols[5]:
        if status == 'Over Budget':
            st.error(status)
        elif status == 'Warning':
            st.warning(status)
        elif status == 'On Track':
            st.success(status)
        else:
            st.info('No Budget')

    st.markdown('')

# -----------------------------------------------------------------------------
# MAIN RENDERER
# -----------------------------------------------------------------------------
def render_budget_alerts_tab() -> None:
    '''Render the Budget Alerts tab UI.'''
    try:
        init_budget_alerts_state()

        st.subheader('Budget Alerts')

        df = fetch_df(DB_PATH)
        saved_budget_settings = load_budget_settings(BUDGET_PATH)

        all_categories = [
            category
            for category in get_all_categories(CUSTOM_CAT_PATH)
            if category != ''
        ]

        if not df.empty:
            df['tx_date'] = pd.to_datetime(df['tx_date'], errors='coerce')
            df = df.dropna(subset=['tx_date'])

        if st.session_state['budget_saved_message']:
            st.success(st.session_state['budget_saved_message'])
            st.session_state['budget_saved_message'] = ''

        settings = render_budget_settings_form(
            all_categories=all_categories,
            saved_budget_settings=saved_budget_settings,
        )

        st.markdown('---')

        render_alerts_section(df, settings)
        render_category_budget_overview(df, settings)

    except Exception as error:
        st.error(f'Error in Budget Alerts tab: {error}')