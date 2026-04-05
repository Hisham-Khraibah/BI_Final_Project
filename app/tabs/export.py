# -----------------------------------------------------------------------------
# EXPORT TAB
# -----------------------------------------------------------------------------
'''
Streamlit UI for exporting transaction data to CSV.
'''
from __future__ import annotations
import pandas as pd
import streamlit as st
from app.core.config import DB_PATH
from app.core.database import fetch_df
from app.core.helpers import get_now_local, safe_float

# -----------------------------------------------------------------------------
# DATA PREPARATION
# -----------------------------------------------------------------------------
def prepare_export_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    '''Prepare and clean the dataframe for CSV export.'''
    try:
        if df.empty:
            return pd.DataFrame()

        export_df = df.sort_values(['tx_date', 'id']).reset_index(drop=True)

        if 'created_at' in export_df.columns:
            created_dt = pd.to_datetime(export_df['created_at'], errors='coerce')

            export_df['created_date'] = created_dt.apply(
                lambda value: value.strftime('%Y-%m-%d') if pd.notnull(value) else ''
            )
            export_df['created_time'] = created_dt.apply(
                lambda value: value.strftime('%I:%M:%S %p') if pd.notnull(value) else ''
            )

            export_df = export_df.drop(columns=['created_at'])

        if 'notes' in export_df.columns:
            export_df = export_df.drop(columns=['notes'])

        if 'source' in export_df.columns:
            export_df = export_df.drop(columns=['source'])

        if 'id' in export_df.columns:
            export_df = export_df.drop(columns=['id'])

        export_df.insert(0, 'excel_id', export_df.index + 1)

        export_df = export_df.rename(
            columns={
                'excel_id': 'ID',
                'tx_date': 'Transaction Date',
                'merchant': 'Vendor',
                'amount': 'Amount',
                'category': 'Category',
                'note': 'Description',
                'created_date': 'Date of creation',
                'created_time': 'Time of creation',
            }
        )

        export_columns = [
            'ID',
            'Transaction Date',
            'Vendor',
            'Amount',
            'Category',
            'Description',
            'Date of creation',
            'Time of creation',
        ]

        export_df = export_df[
            [column for column in export_columns if column in export_df.columns]
        ]

        if 'Transaction Date' in export_df.columns:
            tx_series = pd.to_datetime(
                export_df['Transaction Date'],
                errors='coerce',
            )
            export_df['Transaction Date'] = tx_series.apply(
                lambda value: value.strftime('%Y-%m-%d')
                if pd.notnull(value)
                else ''
            )

        if 'Amount' in export_df.columns:
            export_df['Amount'] = export_df['Amount'].map(
                lambda value: f'${safe_float(value, 0.0):,.2f}'
            )

        return export_df

    except Exception:
        return pd.DataFrame()

# -----------------------------------------------------------------------------
# MAIN RENDERER
# -----------------------------------------------------------------------------
def render_export_tab() -> None:
    '''Render the Export tab UI.'''
    try:
        st.subheader('CSV Export')
        st.caption('Download your transaction history as a CSV file')

        df = fetch_df(DB_PATH)

        if df.empty:
            st.info('No data to export.')
            return

        export_df = prepare_export_dataframe(df)

        if export_df.empty:
            st.warning('Export data could not be prepared.')
            return

        st.download_button(
            label='Download CSV',
            data=export_df.to_csv(index=False).encode('utf-8'),
            file_name=f'Expenses_{get_now_local().strftime("%Y-%m-%d")}.csv',
            mime='text/csv',
        )

    except Exception as error:
        st.error(f'Error in Export tab: {error}')