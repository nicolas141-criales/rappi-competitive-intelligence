"""
scoring.py – Competitiveness Engine.
Genera scores ejecutivos 0-100 que resumen la posición competitiva de Rappi.
Diseñado para el Executive Dashboard — simple, accionable, premium.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from app.core.logger import get_logger

log = get_logger(__name__)

# Pesos de scoring por componente
_W = {
    "price":    0.35,
    "fee":      0.25,
    "eta":      0.25,
    "promo":    0.15,
}


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


# ── Scores individuales ────────────────────────────────────────────────────────

def price_score(df: pd.DataFrame) -> float:
    """100 = Rappi es el más barato. 0 = Rappi es el más caro."""
    if df.empty:
        return 50.0
    avg = df.groupby("platform")["final_price"].mean()
    if "rappi" not in avg.index or len(avg) < 2:
        return 50.0
    rappi  = avg["rappi"]
    others = avg.drop("rappi")
    min_comp = others.min()
    max_comp = others.max()
    if max_comp == min_comp:
        return 50.0
    # Rango: si rappi == min_comp → 100, si rappi == max_comp → 0
    raw = (max_comp - rappi) / (max_comp - min_comp) * 100
    return round(_clamp(raw), 1)


def delivery_performance_score(df: pd.DataFrame) -> float:
    """100 = Rappi tiene el fee más bajo y ETA más rápido."""
    if df.empty:
        return 50.0
    fee_avg = df.groupby("platform")["delivery_fee"].mean()
    eta_avg = df.groupby("platform")["eta_min"].mean()
    scores  = []
    for metric, higher_is_worse in [(fee_avg, True), (eta_avg, True)]:
        if "rappi" not in metric.index or len(metric) < 2:
            scores.append(50.0)
            continue
        r = metric["rappi"]
        others = metric.drop("rappi")
        mn, mx = others.min(), others.max()
        if mx == mn:
            scores.append(50.0)
            continue
        # lower = better, so invert
        raw = (mx - r) / (mx - mn) * 100 if higher_is_worse else (r - mn) / (mx - mn) * 100
        scores.append(_clamp(raw))
    return round(np.mean(scores), 1)


def promo_aggressiveness_score(df: pd.DataFrame) -> float:
    """100 = competencia mucho más agresiva en promos (riesgo alto para Rappi)."""
    if df.empty:
        return 50.0
    if "discount" not in df.columns:
        return 50.0
    promo_rate = (
        df[df["discount"] > 0]
        .groupby("platform")
        .size()
        .div(df.groupby("platform").size())
        .fillna(0)
        * 100
    )
    if "rappi" not in promo_rate.index or len(promo_rate) < 2:
        return 50.0
    rappi_rate  = promo_rate["rappi"]
    comp_avg    = promo_rate.drop("rappi").mean()
    # Gap: cuánto más agresiva es la competencia
    gap = comp_avg - rappi_rate
    score = _clamp(50 + gap * 2)
    return round(score, 1)


def market_pressure_score(df: pd.DataFrame) -> float:
    """Presión competitiva global. 100 = máxima presión sobre Rappi."""
    ps = price_score(df)
    dp = delivery_performance_score(df)
    pm = promo_aggressiveness_score(df)
    # Invertir price y delivery (alto score = favorable para Rappi = baja presión)
    pressure = 100 - (ps * _W["price"] + dp * _W["fee"] + dp * _W["eta"]) / (
        _W["price"] + _W["fee"] + _W["eta"]
    )
    return round(_clamp(pressure + pm * _W["promo"]), 1)


def zone_opportunity_index(df: pd.DataFrame) -> dict[str, float]:
    """Score de oportunidad por zona (100 = mayor oportunidad de crecimiento)."""
    if df.empty or "zone" not in df.columns:
        return {}
    result = {}
    for zone in df["zone"].unique():
        sub = df[df["zone"] == zone]
        # Zonas donde DiDi no está presente = oportunidad alta
        platforms_in_zone = sub["platform"].unique()
        didi_gap  = 30.0 if "didi"     not in platforms_in_zone else 0.0
        uber_gap  = 30.0 if "ubereats" not in platforms_in_zone else 0.0
        # Zonas donde Rappi tiene ventaja de fee
        rappi_fee    = sub[sub["platform"] == "rappi"]["delivery_fee"].mean() if "rappi" in platforms_in_zone else 0
        comp_fee_avg = sub[sub["platform"] != "rappi"]["delivery_fee"].mean() if len(platforms_in_zone) > 1 else rappi_fee
        fee_adv = _clamp((comp_fee_avg - rappi_fee) / max(comp_fee_avg, 1) * 100 + 50)
        result[zone] = round(_clamp(fee_adv * 0.4 + didi_gap + uber_gap), 1)
    return result


def strategic_risk_score(df: pd.DataFrame) -> float:
    """Riesgo estratégico global. 100 = riesgo crítico de pérdida de market share."""
    ps = price_score(df)
    dp = delivery_performance_score(df)
    pm = promo_aggressiveness_score(df)
    # Bajo score de precio o delivery = alto riesgo
    risk = ((100 - ps) * 0.40 + (100 - dp) * 0.35 + pm * 0.25)
    return round(_clamp(risk), 1)


# ── Score consolidado ─────────────────────────────────────────────────────────

def calculate_competitive_scores(df: pd.DataFrame) -> dict:
    import json
    from app.core.config import DATA_DIR
    scores = competitiveness_scores(df)
    
    score_file = DATA_DIR / "scores.json"
    try:
        with open(score_file, "w", encoding="utf-8") as f:
            json.dump(scores, f, ensure_ascii=False, indent=2)
        log.success(f"Generated competitive scores -> {score_file}")
    except Exception as e:
        log.warning(f"Failed to save scores.json: {e}")
        
    return scores

def competitiveness_scores(df: pd.DataFrame) -> dict:
    """
    Retorna todos los scores ejecutivos en un diccionario limpio.
    Usado directamente por el dashboard.
    """
    if df.empty:
        # Valores neutros si no hay datos
        return {
            "competitiveness_index":        50.0,
            "delivery_performance_score":   50.0,
            "promo_aggressiveness_score":   50.0,
            "market_pressure_score":        50.0,
            "strategic_risk_score":         50.0,
            "zone_opportunity":             {},
        }
    try:
        ci  = price_score(df)
        dp  = delivery_performance_score(df)
        pm  = promo_aggressiveness_score(df)
        mp  = market_pressure_score(df)
        rs  = strategic_risk_score(df)
        zo  = zone_opportunity_index(df)
        scores = {
            "competitiveness_index":        ci,
            "delivery_performance_score":   dp,
            "promo_aggressiveness_score":   pm,
            "market_pressure_score":        mp,
            "strategic_risk_score":         rs,
            "zone_opportunity":             zo,
        }
        log.info(f"Scores: CI={ci} | DP={dp} | PM={pm} | Risk={rs}")
        return scores
    except Exception as exc:
        log.warning(f"Scoring failed: {exc}")
        return {"competitiveness_index": 50.0, "strategic_risk_score": 50.0,
                "delivery_performance_score": 50.0, "promo_aggressiveness_score": 50.0,
                "market_pressure_score": 50.0, "zone_opportunity": {}}


def severity_label(score: float, inverted: bool = False) -> str:
    """
    Convierte un score en una etiqueta de severidad ejecutiva.
    inverted=True → alto score = bueno (ej: Competitiveness Index).
    inverted=False → alto score = riesgo (ej: Strategic Risk Score).
    """
    if inverted:
        score = 100 - score
    if score >= 75:
        return "CRITICAL"
    if score >= 55:
        return "HIGH"
    if score >= 35:
        return "MEDIUM"
    return "LOW"


SEVERITY_COLORS = {
    "CRITICAL": "#DC2626",   # Rojo premium
    "HIGH":     "#EA580C",   # Naranja ejecutivo
    "MEDIUM":   "#D97706",   # Ámbar suave
    "LOW":      "#16A34A",   # Verde operacional
}

SEVERITY_BG = {
    "CRITICAL": "#FEF2F2",
    "HIGH":     "#FFF7ED",
    "MEDIUM":   "#FFFBEB",
    "LOW":      "#F0FDF4",
}
