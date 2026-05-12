"""
pricing_analysis.py – Análisis comparativo de precios por plataforma y zona.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from app.core.logger import get_logger

log = get_logger(__name__)


def price_comparison_by_product(df: pd.DataFrame) -> pd.DataFrame:
    """
    Precio promedio por plataforma y producto.
    Devuelve pivot table: índice=product, columnas=platform.
    """
    if df.empty:
        return pd.DataFrame()

    pivot = (
        df.groupby(["product", "platform"])["base_price"]
        .mean()
        .round(2)
        .unstack("platform")
    )
    return pivot


def price_index_vs_rappi(df: pd.DataFrame) -> pd.DataFrame:
    """
    Índice de precio relativo a Rappi (base = 100).
    Valores > 100 → más caro que Rappi.
    Valores < 100 → más barato que Rappi.
    """
    if df.empty or "rappi" not in df["platform"].unique():
        return pd.DataFrame()

    avg = (
        df.groupby(["product", "platform"])["base_price"]
        .mean()
        .unstack("platform")
    )

    rappi_col = avg.get("rappi", avg.iloc[:, 0])
    for col in avg.columns:
        avg[f"{col}_index"] = (avg[col] / rappi_col * 100).round(1)

    index_cols = [c for c in avg.columns if c.endswith("_index")]
    return avg[index_cols].rename(columns=lambda c: c.replace("_index", ""))


def final_price_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """Precio final (todo incluido) por plataforma y zona."""
    if df.empty:
        return pd.DataFrame()

    return (
        df.groupby(["zone", "platform"])["final_price"]
        .mean()
        .round(2)
        .unstack("platform")
        .reset_index()
    )


def cheapest_platform_per_zone(df: pd.DataFrame) -> pd.DataFrame:
    """Identifica la plataforma más barata por zona (precio final promedio)."""
    if df.empty:
        return pd.DataFrame()

    avg = (
        df.groupby(["zone", "platform"])["final_price"]
        .mean()
        .round(2)
        .reset_index()
    )
    idx    = avg.groupby("zone")["final_price"].idxmin()
    result = avg.loc[idx].copy()
    result.columns = ["zone", "cheapest_platform", "avg_final_price"]
    return result.reset_index(drop=True)


def price_variance_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Variabilidad de precios: desviación estándar por plataforma."""
    if df.empty:
        return pd.DataFrame()

    return (
        df.groupby("platform")
        .agg(
            avg_base_price =("base_price",  "mean"),
            std_base_price =("base_price",  "std"),
            avg_final_price=("final_price", "mean"),
            std_final_price=("final_price", "std"),
            count          =("base_price",  "count"),
        )
        .round(2)
        .reset_index()
    )


def pct_diff_vs_rappi(df: pd.DataFrame) -> dict[str, float]:
    """
    % diferencia promedio de precio final vs Rappi por plataforma.
    Positivo = más caro que Rappi.
    """
    if df.empty:
        return {}

    rappi_avg = df[df["platform"] == "rappi"]["final_price"].mean()
    result    = {}
    for plt in df["platform"].unique():
        if plt == "rappi":
            continue
        other_avg   = df[df["platform"] == plt]["final_price"].mean()
        result[plt] = round((other_avg - rappi_avg) / rappi_avg * 100, 2)
    return result
