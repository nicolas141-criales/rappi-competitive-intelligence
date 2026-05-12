"""
logger.py – Logger estructurado con Loguru y Rich.
Escribe a consola (coloreado) y a archivo rotativo.
"""
from __future__ import annotations

import sys
from pathlib import Path
from loguru import logger

# ── Rutas ─────────────────────────────────────────────────────────────────────
LOG_DIR  = Path(__file__).resolve().parents[2] / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "scraper_{time:YYYY-MM-DD}.log"

# ── Quitar handler por defecto ────────────────────────────────────────────────
logger.remove()

# ── Handler consola (coloreado) ───────────────────────────────────────────────
logger.add(
    sys.stdout,
    level="INFO",
    colorize=True,
    format=(
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level:<8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> – "
        "<level>{message}</level>"
    ),
)

# ── Handler archivo (rotativo 50 MB, retención 7 días) ────────────────────────
logger.add(
    str(LOG_FILE),
    level="DEBUG",
    rotation="50 MB",
    retention="7 days",
    compression="zip",
    encoding="utf-8",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function}:{line} – {message}",
)

def get_logger(name: str):
    """Devuelve un logger con contexto de módulo."""
    return logger.bind(name=name)

__all__ = ["logger", "get_logger"]
