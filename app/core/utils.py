"""
utils.py – Utilidades compartidas entre scrapers y analytics.
"""
from __future__ import annotations

import asyncio
import json
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from app.core.config import MIN_DELAY, MAX_DELAY
from app.core.logger import get_logger

log = get_logger(__name__)


# ── Delays humanizados ────────────────────────────────────────────────────────

async def human_delay(min_s: float = MIN_DELAY, max_s: float = MAX_DELAY) -> None:
    """Espera aleatoria entre acciones para simular comportamiento humano."""
    delay = random.uniform(min_s, max_s)
    log.debug(f"Sleeping {delay:.2f}s")
    await asyncio.sleep(delay)


def sync_human_delay(min_s: float = MIN_DELAY, max_s: float = MAX_DELAY) -> None:
    import time
    delay = random.uniform(min_s, max_s)
    time.sleep(delay)


# ── Parseo de precios ─────────────────────────────────────────────────────────

def parse_price(raw: str | None) -> float:
    """Extrae un float de un string con símbolo de moneda y/o comas."""
    if not raw:
        return 0.0
    cleaned = re.sub(r"[^\d.]", "", raw.replace(",", "."))
    try:
        return round(float(cleaned), 2)
    except ValueError:
        return 0.0


def parse_eta(raw: str | None) -> tuple[int, int]:
    """
    Convierte '20-35 min' → (20, 35).
    Devuelve (0, 0) si no puede parsear.
    """
    if not raw:
        return 0, 0
    nums = re.findall(r"\d+", raw)
    if len(nums) == 1:
        v = int(nums[0])
        return v, v
    if len(nums) >= 2:
        return int(nums[0]), int(nums[1])
    return 0, 0


# ── Timestamp ─────────────────────────────────────────────────────────────────

def now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Guardado de datos ─────────────────────────────────────────────────────────

def save_raw_json(records: list[dict[str, Any]], path: Path) -> None:
    """Guarda lista de registros como JSON con indentación."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2, default=str)
    log.info(f"Saved {len(records)} records → {path}")


def save_raw_csv(records: list[dict[str, Any]], path: Path) -> None:
    """Guarda lista de registros como CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(records)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    log.info(f"Saved {len(records)} records → {path}")


def append_record(record: dict[str, Any], csv_path: Path, json_path: Path) -> None:
    """Añade un registro tanto al CSV como al JSON de forma incremental."""
    # CSV
    df = pd.DataFrame([record])
    if csv_path.exists():
        df.to_csv(csv_path, mode="a", header=False, index=False, encoding="utf-8-sig")
    else:
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    # JSON
    existing: list = []
    if json_path.exists():
        with open(json_path, encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []
    existing.append(record)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2, default=str)


def load_data(csv_path: Path) -> pd.DataFrame:
    """Carga el CSV principal de datos competitivos."""
    if not csv_path.exists():
        return pd.DataFrame()
    return pd.read_csv(csv_path, encoding="utf-8-sig")


# ── Formato ejecutivo ─────────────────────────────────────────────────────────

def format_pct(value: float, decimals: int = 1) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.{decimals}f}%"


def format_currency(value: float) -> str:
    return f"${value:,.2f} MXN"
