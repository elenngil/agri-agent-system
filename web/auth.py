from __future__ import annotations

import hashlib
from typing import Optional

from web.db import get_connection


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def register_user(
    email: str,
    password: str,
    station: str,
    ccaa: str,
    variety: str,
    soil_type: str = "",
    irrigation_system: str = "",
    objective: str = "equilibrio",
) -> tuple[bool, str]:
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()

        if existing:
            return False, "Ese email ya existe."

        conn.execute(
            """
            INSERT INTO users (
                email, password_hash, station, ccaa, variety,
                soil_type, irrigation_system, objective
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                email.strip().lower(),
                hash_password(password),
                station.strip(),
                ccaa.strip(),
                variety.strip(),
                soil_type.strip(),
                irrigation_system.strip(),
                objective.strip(),
            ),
        )
        conn.commit()
        return True, "Cuenta creada correctamente."
    finally:
        conn.close()


def login_user(email: str, password: str) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT *
            FROM users
            WHERE email = ? AND password_hash = ?
            """,
            (email.strip().lower(), hash_password(password)),
        ).fetchone()

        return dict(row) if row else None
    finally:
        conn.close()


def update_user_preferences(
    user_id: int,
    station: str,
    ccaa: str,
    variety: str,
    soil_type: str,
    irrigation_system: str,
    objective: str,
) -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE users
            SET station = ?, ccaa = ?, variety = ?, soil_type = ?,
                irrigation_system = ?, objective = ?
            WHERE id = ?
            """,
            (
                station.strip(),
                ccaa.strip(),
                variety.strip(),
                soil_type.strip(),
                irrigation_system.strip(),
                objective.strip(),
                user_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()