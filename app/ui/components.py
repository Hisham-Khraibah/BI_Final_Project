# -----------------------------------------------------------------------------
# UI COMPONENTS MODULE
# -----------------------------------------------------------------------------
'''
Reusable Streamlit UI components for date inputs, KPI cards,
budget progress, alerts, and charts.
'''
from __future__ import annotations
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from app.core.budget_logic import calculate_budget_progress
from app.core.helpers import get_today_local, safe_float

# -----------------------------------------------------------------------------
# DATE INPUT
# -----------------------------------------------------------------------------
def render_date_input(
    label: str,
    value,
    max_value,
    key: str,
    app_timezone: str,
):
    '''Render a protected Streamlit date input.'''
    try:
        return st.date_input(
            label=label,
            value=value,
            max_value=max_value,
            key=key,
        )

    except Exception:
        return get_today_local(app_timezone)

# -----------------------------------------------------------------------------
# KPI CARD
# -----------------------------------------------------------------------------
def render_metric_card(title: str, value: str, help_text: str = '') -> None:
    '''Render a reusable bordered KPI card.'''
    try:
        with st.container(border=True):
            st.markdown(f'#### {title}')
            st.markdown(f'### {value}')

            if help_text:
                st.caption(help_text)

    except Exception as error:
        st.error(f'Error rendering metric card: {error}')

# -----------------------------------------------------------------------------
# BUDGET PROGRESS
# -----------------------------------------------------------------------------
def render_budget_progress(title: str, spent: float, budget: float) -> None:
    '''Render a visual budget progress block.'''
    try:
        st.markdown(f'**{title}**')

        progress_data = calculate_budget_progress(spent, budget)

        if progress_data['budget'] <= 0:
            st.info('No budget set.')
            return

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.progress(progress_data['progress_value'])

        with col2:
            st.write(
                f'${progress_data["spent"]:,.2f} / '
                f'${progress_data["budget"]:,.2f}'
            )

        with col3:
            status = progress_data['status']

            if status == 'Over Budget':
                st.error(status)
            elif status == 'Warning':
                st.warning(status)
            else:
                st.success(status)

        st.caption(f'Usage: {progress_data["usage_pct"]:.2f}%')

    except Exception as error:
        st.error(f'Error rendering budget progress: {error}')

# -----------------------------------------------------------------------------
# INLINE BUDGET POPUP
# -----------------------------------------------------------------------------
def render_budget_popup_inline(session_key: str = 'active_budget_popup') -> None:
    '''Render an inline dismissible budget popup using session state.'''
    try:
        popup_data = st.session_state.get(session_key)

        if not popup_data:
            return

        with st.container(border=True):
            st.error(popup_data.get('title', 'Budget Alert'))
            st.write(popup_data.get('message', ''))

            if st.button(
                'Dismiss Budget Alert',
                key=f'dismiss_{session_key}_btn',
                width='content',
            ):
                st.session_state[session_key] = None
                st.rerun()

    except Exception as error:
        st.error(f'Error displaying budget popup panel: {error}')

# -----------------------------------------------------------------------------
# PIE CHART
# -----------------------------------------------------------------------------
def render_clean_pie_chart(
    pie_df: pd.DataFrame,
    title: str = 'Current Month Category Spending',
    category_col: str = 'category',
    amount_col: str = 'amount',
) -> None:
    '''Render a pie chart with small categories grouped into Other.'''
    try:
        if pie_df.empty or pie_df[amount_col].sum() <= 0:
            st.info('No data available for category pie chart.')
            return

        pie_df = pie_df.copy()
        pie_df = pie_df.sort_values(amount_col, ascending=False).reset_index(drop=True)

        total_amount = float(pie_df[amount_col].sum())

        pie_df['percent'] = pie_df[amount_col].apply(
            lambda value: (safe_float(value, 0.0) / total_amount * 100)
            if total_amount > 0
            else 0.0
        )

        display_df = pie_df[pie_df['percent'] >= 3.0].copy()
        other_df = pie_df[pie_df['percent'] < 3.0].copy()

        if not other_df.empty:
            display_df = pd.concat(
                [
                    display_df,
                    pd.DataFrame(
                        [
                            {
                                category_col: 'Other',
                                amount_col: float(other_df[amount_col].sum()),
                                'percent': float(other_df['percent'].sum()),
                            }
                        ]
                    ),
                ],
                ignore_index=True,
            )

        fig_pie, ax_pie = plt.subplots(figsize=(8.5, 3.8))

        wedges, _, _ = ax_pie.pie(
            display_df[amount_col],
            labels=None,
            autopct=lambda pct: f'{pct:.2f}%' if pct >= 3 else '',
            startangle=90,
            pctdistance=0.78,
            radius=0.82,
            wedgeprops={'linewidth': 1, 'edgecolor': 'white'},
            textprops={'fontsize': 9},
        )

        legend_labels = [
            f'{category} ({amount:,.0f})'
            for category, amount in zip(
                display_df[category_col],
                display_df[amount_col],
            )
        ]

        ax_pie.legend(
            wedges,
            legend_labels,
            title='Category',
            loc='center left',
            bbox_to_anchor=(1.02, 0.5),
            frameon=False,
            fontsize=9,
        )

        ax_pie.set_title(title, fontsize=13, pad=12)
        ax_pie.axis('equal')
        fig_pie.tight_layout()

        st.pyplot(fig_pie, width='stretch')

    except Exception as error:
        st.error(f'Error rendering pie chart: {error}')