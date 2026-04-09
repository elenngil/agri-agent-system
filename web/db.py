from __future__ import annotations

import sqlite3
from pathlib import Path

DB_DIR = Path("data")
DB_PATH = DB_DIR / "app.db"


def get_connection() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                station TEXT NOT NULL,
                ccaa TEXT NOT NULL,
                variety TEXT NOT NULL,
                soil_type TEXT DEFAULT '',
                irrigation_system TEXT DEFAULT '',
                objective TEXT DEFAULT 'equilibrio',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                station TEXT NOT NULL,
                ccaa TEXT NOT NULL,
                variety TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                summary TEXT DEFAULT '',
                sms_text TEXT DEFAULT '',
                risk_json TEXT DEFAULT '',
                output_json TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()