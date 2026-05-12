"""
fee_analysis.py – Análisis de delivery fees y service fees por plataforma y zona.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from app.core.logger import get_logger

log = get_logger(__name__)


def fee_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Resumen de fees promedio por plataforma."""
    if df.empty:
        return pd.DataFrame()

    return (
        df.groupby("platform")
        .agg(
            avg_delivery_fee=("delivery_fee", "mean"),
            avg_service_fee =("service_fee",  "mean"),
            avg_total_fee   =("delivery_fee",  lambda x: (x + df.loc[x.index, "service_fee"]).mean()),
            pct_free_delivery=("delivery_fee", lambda x: (x == 0).mean() * 100),
        )
        .round(2)
        .reset_index()
    )


def fee_by_zone(df: pd.DataFrame) -> pd.DataFrame:
    """Delivery fee promedio por zona y plataforma."""
    if df.empty:
        return pd.DataFrame()

    return (
        df.groupby(["zone", "platform"])["delivery_fee"]
        .mean()
        .round(2)
        .unstack("platform")
        .reset_index()
    )


def fee_burden_pct(df: pd.DataFrame) -> pd.DataFrame:
    """
    % que representan los fees sobre el precio base.
    (delivery_fee + service_fee) / base_price * 100
    """
    if df.empty:
        return pd.DataFrame()

    df2 = df.copy()
    df2["total_fee"]     = df2["delivery_fee"] + df2["service_fee"]
    df2["fee_burden_pct"] = (df2["total_fee"] / df2["base_price"].replace(0, np.nan) * 100).round(1)

    return (
        df2.groupby("platform")
        .agg(
            avg_fee_burden_pct=("fee_burden_pct", "mean"),
            avg_total_fee     =("total_fee",       "mean"),
        )
        .round(2)
        .reset_index()
    )


def free_delivery_rate(df: pd.DataFrame) -> pd.DataFrame:
    """% de registros con envío gratis por plataforma."""
    if df.empty:
        return pd.DataFrame()

    df2 = df.copy()
    df2["free_delivery"] = df2["delivery_fee"] == 0.0

    return (
        df2.groupby("platform")["free_delivery"]
        .agg(["mean", "count"])
        .rename(columns={"mean": "free_delivery_rate", "count": "total_records"})
        .assign(free_delivery_rate=lambda x: (x["free_delivery_rate"] * 100).round(1))
        .reset_index()
    )


def fee_competitiveness_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Score de competitividad en fees (0-100).
    100 = fees más bajos del mercado.
    """
    if df.empty:
        return pd.DataFrame()

    summary = fee_summary(df)
    if summary.empty:
        return pd.DataFrame()

    max_fee = summary["avg_delivery_fee"].max()
    min_fee = summary["avg_delivery_fee"].min()
    rng     = max_fee - min_fee if max_fee != min_fee else 1

    summary["fee_score"] = (
        (max_fee - summary["avg_delivery_fee"]) / rng * 100
    ).round(1)

    return summary[["platform", "avg_delivery_fee", "avg_service_fee", "fee_score"]]
