from __future__ import annotations

import logging_config  # PRIMERA linea
import logging

import json
from datetime import date
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from smolagents import InferenceClientModel

from orchestrator import Orchestrator
from models.shared_state import SharedState
from web.db import get_connection

import os

load_dotenv()

logger = logging.getLogger(__name__)

# Pesos de la funcion de utilidad segun objetivo del usuario
OBJECTIVE_WEIGHTS = {
    "calidad": {
        "quality":        0.55,
        "production":     0.25,
        "cost":           0.12,
        "sustainability": 0.08,
    },
    "produccion": {
        "quality":        0.25,
        "production":     0.55,
        "cost":           0.12,
        "sustainability": 0.08,
    },
    "equilibrio": {
        "quality":        0.40,
        "production":     0.35,
        "cost":           0.15,
        "sustainability": 0.10,
    },
}


def build_model() -> InferenceClientModel:
    return InferenceClientModel(
        model_id="Qwen/Qwen2.5-72B-Instruct",
        token=os.environ["HF_TOKEN"],
    )


def build_state(
    station:    str,
    ccaa:       str,
    variety:    str,
    start_date: date,
    end_date:   date,
    soil_type: str | None = None,
) -> SharedState:
    state = SharedState(
        station=station,
        ccaa=ccaa,
        start_date=start_date,
        end_date=end_date,
        soil_type=soil_type
    )
    state.selected_variety = variety
    return state


def run_analysis(
    station:    str,
    ccaa:       str,
    variety:    str,
    start_date: date,
    end_date:   date,
    objective:  str = "equilibrio",
    soil_type: str | None = None,
) -> dict[str, Any]:

    # Seleccionar pesos segun el objetivo del usuario
    weights = OBJECTIVE_WEIGHTS.get(objective, OBJECTIVE_WEIGHTS["equilibrio"])
    logger.info("Objetivo de produccion: %s — pesos: %s", objective, weights)

    model        = build_model()
    orchestrator = Orchestrator(model=model, deliberative_weights=weights)
    state        = build_state(
        station=station, ccaa=ccaa, variety=variety,
        start_date=start_date, end_date=end_date, soil_type=soil_type
    )

    final_state = orchestrator.run(state)

    explanation = getattr(final_state, "explanation", {}) or {}
    daily_plan  = getattr(final_state, "daily_plan",  None)

    result = {
        "meta": {
            "station":    getattr(final_state, "station", station),
            "ccaa":       getattr(final_state, "ccaa",    ccaa),
            "variety":    getattr(getattr(final_state, "crop_data", None), "variety", variety),
            "start_date": str(start_date),
            "end_date":   str(end_date),
            "objective":  objective,
        },
        "summary":                  explanation.get("summary",                  ""),
        "risk_explanation":         explanation.get("risk_explanation",         []),
        "recommendation_reasoning": explanation.get("recommendation_reasoning", ""),
        "alternatives":             explanation.get("alternatives",             []),
        "sms_text":                 explanation.get("sms_text",                 ""),
        "daily_plan_text":          getattr(daily_plan, "explanation", "") if daily_plan else "",
    }
    return result


def save_analysis(user_id: int, result: dict[str, Any]) -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO analyses (
                user_id, station, ccaa, variety, start_date, end_date,
                summary, sms_text, risk_json, output_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                result["meta"]["station"],
                result["meta"]["ccaa"],
                result["meta"]["variety"],
                result["meta"]["start_date"],
                result["meta"]["end_date"],
                result.get("summary",  ""),
                result.get("sms_text", ""),
                json.dumps(result.get("risk_explanation", []), ensure_ascii=False),
                json.dumps(result, ensure_ascii=False),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_last_analyses(user_id: int, limit: int = 5) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT created_at, station, ccaa, variety, start_date, end_date, summary
            FROM analyses
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()