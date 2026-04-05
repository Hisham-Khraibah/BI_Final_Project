# -----------------------------------------------------------------------------
# DATABASE MODULE
# -----------------------------------------------------------------------------
"""
Database and storage logic for SQLite operations and CSV export.
"""
from __future__ import annotations
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
import pandas as pd
from zoneinfo import ZoneInfo
from app.core.helpers import safe_float

# -----------------------------------------------------------------------------
# TIME HELPERS
# -----------------------------------------------------------------------------
def get_now_local(app_timezone: str = "America/Toronto") -> datetime:
    """Return the current local datetime using the configured timezone."""
    try:
        return datetime.now(ZoneInfo(app_timezone))
    except Exception:
        return datetime.now()

# -----------------------------------------------------------------------------
# CONNECTION MANAGEMENT
# -----------------------------------------------------------------------------
def get_conn(db_path: str | Path) -> Optional[sqlite3.Connection]:
    """Create and return a SQLite connection."""
    try:
        return sqlite3.connect(str(db_path), check_same_thread=False)
    except Exception:
        return None

# -----------------------------------------------------------------------------
# DATABASE INITIALIZATION
# -----------------------------------------------------------------------------
def init_db(db_path: str | Path) -> bool:
    """
    Initialize the Expenses table if it does not exist.

    Also handles legacy migration from `notes` to `note`.
    """
    conn = None

    try:
        conn = get_conn(db_path)
        if conn is None:
            return False
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tx_date TEXT,
                merchant TEXT,
                amount REAL,
                category TEXT,
                note TEXT,
                created_at TEXT
            )
        """)
        conn.commit()

        columns = [row[1] for row in cur.execute("PRAGMA table_info(Expenses)").fetchall()]

        if "notes" in columns and "note" not in columns:
            cur.execute("ALTER TABLE Expenses ADD COLUMN note TEXT")
            cur.execute("UPDATE Expenses SET note = notes WHERE note IS NULL")
            conn.commit()

        return True

    except Exception:
        return False

    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

# -----------------------------------------------------------------------------
# INSERT OPERATIONS
# -----------------------------------------------------------------------------
def insert_expense(
    db_path: str | Path,
    tx_date: str,
    merchant: str,
    amount,
    category: str,
    note: str,
    app_timezone: str = "America/Toronto",
) -> bool:
    """Insert a new expense row into the database."""
    conn = None

    try:
        conn = get_conn(db_path)
        if conn is None:
            return False

        cur = conn.cursor()

        cur.execute("""
            INSERT INTO Expenses (
                tx_date,
                merchant,
                amount,
                category,
                note,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            tx_date,
            merchant,
            safe_float(amount),
            category,
            note,
            get_now_local(app_timezone).isoformat(),
        ))

        conn.commit()
        return cur.rowcount > 0

    except Exception:
        return False

    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

# -----------------------------------------------------------------------------
# UPDATE OPERATIONS
# -----------------------------------------------------------------------------
def update_expense(
    db_path: str | Path,
    row_id: int,
    tx_date: str,
    merchant: str,
    amount,
    category: str,
    note: str,
) -> bool:
    """
    Update an existing expense row by ID.

    Returns True only if at least one row was updated.
    """
    conn = None

    try:
        conn = get_conn(db_path)
        if conn is None:
            return False

        cur = conn.cursor()
        cur.execute("""
            UPDATE Expenses
            SET tx_date = ?, merchant = ?, amount = ?, category = ?, note = ?
            WHERE id = ?
        """, (
            tx_date,
            merchant,
            safe_float(amount),
            category,
            note,
            row_id,
        ))

        conn.commit()
        return cur.rowcount > 0

    except Exception:
        return False

    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

# -----------------------------------------------------------------------------
# DELETE OPERATIONS
# -----------------------------------------------------------------------------
def delete_expense(db_path: str | Path, row_id: int) -> bool:
    """
    Delete an expense row by ID.

    Returns True only if at least one row was deleted.
    """
    conn = None

    try:
        conn = get_conn(db_path)
        if conn is None:
            return False

        cur = conn.cursor()
        cur.execute("DELETE FROM Expenses WHERE id = ?", (row_id,))
        conn.commit()
        return cur.rowcount > 0

    except Exception:
        return False

    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

# -----------------------------------------------------------------------------
# FETCH OPERATIONS
# -----------------------------------------------------------------------------
def fetch_df(db_path: str | Path) -> pd.DataFrame:
    """
    Fetch all expenses as a pandas DataFrame.

    Returns:
        DataFrame ordered by transaction date descending, then ID descending.
    """
    conn = None

    try:
        conn = get_conn(db_path)
        if conn is None:
            return pd.DataFrame()

        df = pd.read_sql_query(
            "SELECT * FROM Expenses ORDER BY date(tx_date) DESC, id DESC",
            conn,
        )

        if not df.empty:
            if "notes" in df.columns and "note" not in df.columns:
                df["note"] = df["notes"]
                df = df.drop(columns=["notes"])

            if "source" in df.columns:
                df = df.drop(columns=["source"])

            df["tx_date"] = pd.to_datetime(df["tx_date"], errors="coerce")
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

        return df

    except Exception:
        return pd.DataFrame()

    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

# -----------------------------------------------------------------------------
# CSV EXPORT
# -----------------------------------------------------------------------------
def export_csv_append(csv_path: str | Path, row: dict) -> bool:
    """Append a single row to the CSV file."""
    try:
        csv_path = Path(csv_path)
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        file_exists = csv_path.exists()

        df = pd.DataFrame([row])
        df.to_csv(
            csv_path,
            mode="a",
            header=not file_exists,
            index=False,
        )

        return True

    except Exception:
        return False