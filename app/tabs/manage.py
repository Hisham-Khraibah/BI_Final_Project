# -----------------------------------------------------------------------------
# MANAGE TAB
# -----------------------------------------------------------------------------
'''
Streamlit UI for viewing, editing, and deleting transactions.
'''
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
    '''Prepare dataframe for display.'''
    try:
        if df.empty:
            return pd.DataFrame()

        result_df = df.copy()

        if 'created_at' in result_df.columns:
            created_dt = pd.to_datetime(result_df['created_at'], errors='coerce')

            result_df['created_date'] = created_dt.dt.strftime('%Y-%m-%d')
            result_df['created_time'] = created_dt.dt.strftime('%I:%M:%S %p')

            result_df = result_df.drop(columns=['created_at'])

        result_df = result_df.drop(
            columns=[col for col in ['notes', 'source'] if col in result_df.columns],
            errors='ignore',
        )

        if 'tx_date' in result_df.columns:
            result_df['tx_date'] = pd.to_datetime(
                result_df['tx_date'], errors='coerce'
            ).dt.strftime('%Y-%m-%d')

        if 'amount' in result_df.columns:
            result_df['amount'] = result_df['amount'].apply(
                lambda value: f'${safe_float(value, 0.0):,.2f}'
            )

        result_df = result_df.rename(
            columns={
                'id': 'ID',
                'tx_date': 'Transaction Date',
                'merchant': 'Vendor',
                'amount': 'Amount',
                'category': 'Category',
                'note': 'Description',
                'created_date': 'Date of creation',
                'created_time': 'Time of creation',
            }
        )

        ordered_columns = [
            'ID',
            'Transaction Date',
            'Vendor',
            'Amount',
            'Category',
            'Description',
            'Date of creation',
            'Time of creation',
        ]

        return result_df[[col for col in ordered_columns if col in result_df.columns]]

    except Exception:
        return pd.DataFrame()

# -----------------------------------------------------------------------------
# ACTION BUTTONS
# -----------------------------------------------------------------------------
def render_action_buttons(mode: str) -> dict:
    '''Render action buttons based on mode.'''
    left_col, _ = st.columns([2.2, 12], gap='small')

    with left_col:
        col1, col2 = st.columns(2, gap='small')

        if mode == 'delete':
            return {
                'confirm_delete': col1.button(
                    'Confirm Delete',
                    key='confirm_delete_btn',
                    use_container_width=True,
                ),
                'cancel_delete': col2.button(
                    'Cancel',
                    key='cancel_delete_btn',
                    use_container_width=True,
                ),
                'edit_clicked': False,
                'delete_clicked': False,
            }

        return {
            'confirm_delete': False,
            'cancel_delete': False,
            'edit_clicked': col1.button(
                'Edit',
                key='edit_top_btn',
                use_container_width=True,
            ),
            'delete_clicked': col2.button(
                'Delete',
                key='delete_top_btn',
                use_container_width=True,
            ),
        }

# -----------------------------------------------------------------------------
# DELETE HANDLER
# -----------------------------------------------------------------------------
def handle_delete(selected_ids: list[int]) -> None:
    '''Handle delete action.'''
    failed_ids = [row_id for row_id in selected_ids if not delete_expense(DB_PATH, row_id)]

    if not failed_ids:
        st.success('Deleted successfully')
        st.session_state['manage_mode'] = None
        st.rerun()

    st.error(f'Could not delete: {", ".join(map(str, failed_ids))}')

# -----------------------------------------------------------------------------
# EDIT FORM
# -----------------------------------------------------------------------------
def render_edit_form(selected_row: pd.Series) -> None:
    '''Render edit form for a single transaction.'''
    row_id = int(selected_row['id'])

    col1, col2, col3 = st.columns(3)

    with col1:
        edit_date = render_date_input(
            label='Transaction Date',
            value=min(
                pd.to_datetime(selected_row['tx_date']).date(),
                get_today_local(APP_TIMEZONE),
            ),
            max_value=get_today_local(APP_TIMEZONE),
            key=f'edit_date_{row_id}',
            app_timezone=APP_TIMEZONE,
        )

    with col2:
        edit_merchant = st.text_input(
            'Vendor',
            value=str(selected_row['merchant']),
            key=f'edit_merchant_{row_id}',
        )

    with col3:
        edit_amount = st.number_input(
            'Amount',
            value=float(selected_row['amount']),
            min_value=0.0,
            step=0.01,
            key=f'edit_amount_{row_id}',
        )

    categories = get_all_categories(CUSTOM_CAT_PATH)

    try:
        default_index = categories.index(selected_row['category'])
    except ValueError:
        default_index = 0

    edit_category = st.selectbox(
        'Category',
        categories,
        index=default_index,
        key=f'edit_category_{row_id}',
    )

    edit_note = st.text_input(
        'Description',
        value=str(selected_row.get('note', '')),
        key=f'edit_note_{row_id}',
    )

    col_btn, _ = st.columns([2.6, 10])

    with col_btn:
        save_col, cancel_col = st.columns(2, gap='small')

        save_clicked = save_col.button(
            'Save Changes',
            key=f'save_{row_id}',
            use_container_width=True,
        )

        cancel_clicked = cancel_col.button(
            'Cancel',
            key=f'cancel_{row_id}',
            use_container_width=True,
        )

    if save_clicked:
        if update_expense(
            DB_PATH,
            row_id,
            edit_date.isoformat(),
            edit_merchant,
            edit_amount,
            edit_category,
            edit_note,
        ):
            st.success('Updated successfully')
            st.session_state['manage_mode'] = None
            st.rerun()

        st.error('Update failed')

    if cancel_clicked:
        st.session_state['manage_mode'] = None
        st.rerun()

# -----------------------------------------------------------------------------
# MAIN RENDERER
# -----------------------------------------------------------------------------
def render_manage_tab() -> None:
    '''Render the Manage tab UI.'''
    try:
        st.subheader('Transaction Manager')
        st.info('Select one or more rows to edit or delete.')

        df = fetch_df(DB_PATH)

        if df.empty:
            st.info('No records available.')
            return

        display_df = prepare_manage_dataframe(df)

        if display_df.empty:
            st.info('No records available.')
            return

        if 'manage_mode' not in st.session_state:
            st.session_state['manage_mode'] = None

        warning_placeholder = st.empty()
        action_placeholder = st.empty()

        if st.session_state['manage_mode'] == 'delete':
            with warning_placeholder.container():
                st.warning('Confirm deletion of selected row(s).')
        else:
            warning_placeholder.empty()

        event = st.dataframe(
            display_df,
            hide_index=True,
            on_select='rerun',
            selection_mode='multi-row',
            width='stretch',
        )

        selected_rows = event.selection.rows or []

        if not selected_rows:
            st.session_state['manage_mode'] = None
            action_placeholder.empty()
            return

        selected_df = df.iloc[selected_rows]
        selected_ids = selected_df['id'].astype(int).tolist()

        with action_placeholder.container():
            buttons = render_action_buttons(st.session_state['manage_mode'])

        if buttons['edit_clicked']:
            st.session_state['manage_mode'] = 'edit'
            st.rerun()

        if buttons['delete_clicked']:
            st.session_state['manage_mode'] = 'delete'
            st.rerun()

        if buttons['cancel_delete']:
            st.session_state['manage_mode'] = None
            st.rerun()

        if buttons['confirm_delete']:
            handle_delete(selected_ids)

        if st.session_state['manage_mode'] == 'edit':
            if len(selected_rows) != 1:
                st.warning('Select exactly one row to edit.')
                return

            render_edit_form(selected_df.iloc[0])

    except Exception as error:
        st.error(f'Error in Manage tab: {error}')