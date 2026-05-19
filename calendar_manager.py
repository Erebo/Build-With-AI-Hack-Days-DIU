"""
calendar_manager.py — SQLite persistence layer for events.
"""

import sqlite3
import os
from datetime import datetime, date
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")


# ─── Schema ───────────────────────────────────────────────────────────────────

def init_db():
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                date        TEXT    NOT NULL,
                start_time  TEXT    NOT NULL,
                end_time    TEXT    NOT NULL,
                category    TEXT    DEFAULT 'other',
                note        TEXT    DEFAULT '',
                created_at  TEXT    DEFAULT (datetime('now'))
            )
        """)
        conn.commit()


def _conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


# ─── CRUD ─────────────────────────────────────────────────────────────────────

def add_event(title: str, date: str, start_time: str, end_time: str,
              category: str = "other", note: str = "") -> int:
    """Insert a new event; return its id."""
    with _conn() as conn:
        cur = conn.execute(
            """INSERT INTO events (title, date, start_time, end_time, category, note)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title, date, start_time, end_time, category or "other", note or "")
        )
        conn.commit()
        return cur.lastrowid


def get_events_for_date(date_str: str) -> list[dict]:
    with _conn() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM events WHERE date = ? ORDER BY start_time", (date_str,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_events_for_month(year: int, month: int) -> list[dict]:
    prefix = f"{year:04d}-{month:02d}"
    with _conn() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM events WHERE date LIKE ? ORDER BY date, start_time",
            (f"{prefix}%",)
        ).fetchall()
    return [dict(r) for r in rows]


def get_events_in_range(start_date: str, end_date: str) -> list[dict]:
    with _conn() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM events WHERE date BETWEEN ? AND ? ORDER BY date, start_time",
            (start_date, end_date)
        ).fetchall()
    return [dict(r) for r in rows]


def get_all_events() -> list[dict]:
    with _conn() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM events ORDER BY date, start_time"
        ).fetchall()
    return [dict(r) for r in rows]


def delete_event(event_id: int) -> bool:
    with _conn() as conn:
        cur = conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.commit()
    return cur.rowcount > 0


def update_event(event_id: int, **kwargs) -> bool:
    allowed = {"title", "date", "start_time", "end_time", "category", "note"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return False
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [event_id]
    with _conn() as conn:
        cur = conn.execute(f"UPDATE events SET {set_clause} WHERE id = ?", values)
        conn.commit()
    return cur.rowcount > 0


def get_event_by_id(event_id: int) -> Optional[dict]:
    with _conn() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    return dict(row) if row else None


# ─── Bootstrap ────────────────────────────────────────────────────────────────
init_db()