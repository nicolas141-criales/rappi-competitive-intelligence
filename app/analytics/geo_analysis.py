"""
geo_analysis.py – Análisis geográfico por zona y dirección.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from app.core.logger import get_logger

log = get_logger(__name__)

# Coordenadas aproximadas de las zonas para mapas
ZONE_COORDS = {
    "addr_01": (19.4330, -99.1900),  # Polanco
    "addr_02": (19.3654, -99.2727),  # Santa Fe
    "addr_03": (19.4200, -99.2100),  # Lomas Chapultepec
    "addr_04": (19.4121, -99.1760),  # Condesa
    "addr_05": (19.4160, -99.1640),  # Roma Norte
    "addr_06": (19.3450, -99.1620),  # Coyoacán
    "addr_07": (19.3820, -99.1700),  # Del Valle
    "addr_08": (19.3910, -99.1650),  # Narvarte
    "addr_09": (19.2900, -99.1530),  # Tlalpan
    "addr_10": (19.2570, -99.1030),  # Xochimilco
    "addr_11": (19.4270, -99.1680),  # Reforma
    "addr_12": (19.4320, -99.1330),  # Centro Histórico
    "addr_13": (19.3990, -99.1760),  # Insurgentes Sur
    "addr_14": (19.3180, -99.2050),  # Pedregal
    "addr_15": (19.3570, -99.0720),  # Iztapalapa
    "addr_16": (19.4890, -99.1310),  # Gustavo A. Madero
    "addr_17": (19.4860, -99.1830),  # Azcapotzalco
    "addr_18": (19.2860, -99.0020),  # Tláhuac
    "addr_19": (19.1890, -99.0230),  # Milpa Alta
    "addr_20": (19.3260, -99.2350),  # Magdalena Contreras
}


def add_geo_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega columnas lat/lon al DataFrame."""
    if df.empty:
        return df
    df2 = df.copy()
    df2["lat"] = df2["address_id"].map(lambda aid: ZONE_COORDS.get(aid, (19.4326, -99.1332))[0])
    df2["lon"] = df2["address_id"].map(lambda aid: ZONE_COORDS.get(aid, (19.4326, -99.1332))[1])
    return df2


def price_heatmap_data(df: pd.DataFrame, platform: str = "rappi") -> pd.DataFrame:
    """
    Datos para heatmap de precios finales.
    Devuelve: address_label, zone, lat, lon, avg_final_price.
    """
    if df.empty:
        return pd.DataFrame()

    df2 = add_geo_columns(df)
    sub = df2[df2["platform"] == platform] if platform != "all" else df2

    return (
        sub.groupby(["address_id", "address_label", "zone", "lat", "lon"])
        .agg(avg_final_price=("final_price", "mean"))
        .round(2)
        .reset_index()
    )


def competitiveness_by_zone(df: pd.DataFrame) -> pd.DataFrame:
    """
    Para cada zona: ¿cuál es la plataforma más cara y más barata?
    Incluye diferencia porcentual.
    """
    if df.empty:
        return pd.DataFrame()

    avg = (
        df.groupby(["zone", "platform"])["final_price"]
        .mean()
        .round(2)
        .reset_index()
    )

    result = []
    for zone, group in avg.groupby("zone"):
        if group.empty:
            continue
        min_row   = group.loc[group["final_price"].idxmin()]
        max_row   = group.loc[group["final_price"].idxmax()]
        rappi_row = group[group["platform"] == "rappi"]
        rappi_price = rappi_row["final_price"].values[0] if not rappi_row.empty else None

        pct_diff = None
        if rappi_price and min_row["platform"] != "rappi":
            pct_diff = round((rappi_price - min_row["final_price"]) / min_row["final_price"] * 100, 1)

        result.append({
            "zone":            zone,
            "cheapest":        min_row["platform"],
            "cheapest_price":  min_row["final_price"],
            "most_expensive":  max_row["platform"],
            "expensive_price": max_row["final_price"],
            "rappi_price":     rappi_price,
            "rappi_vs_cheapest_pct": pct_diff,
        })

    return pd.DataFrame(result)


def coverage_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cobertura de cada plataforma por zona.
    % de direcciones con datos disponibles.
    """
    if df.empty:
        return pd.DataFrame()

    total_addresses = df["address_id"].nunique()
    return (
        df.groupby(["platform", "zone"])["address_id"]
        .nunique()
        .reset_index()
        .rename(columns={"address_id": "addresses_covered"})
    )


def geo_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """Tabla resumen completa por zona con coords para mapas."""
    if df.empty:
        return pd.DataFrame()

    df2 = add_geo_columns(df)
    return (
        df2.groupby(["address_label", "zone", "lat", "lon", "platform"])
        .agg(
            avg_final  =("final_price",   "mean"),
            avg_eta    =("eta_min",        "mean"),
            avg_fee    =("delivery_fee",   "mean"),
        )
        .round(2)
        .reset_index()
    )
