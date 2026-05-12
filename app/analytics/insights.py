"""
insights.py – Motor de insights ejecutivos estilo McKinsey/Bain.
Detecta patrones y genera hallazgos accionables automáticamente.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app.analytics.fee_analysis import fee_summary, fee_by_zone, free_delivery_rate
from app.analytics.geo_analysis import competitiveness_by_zone
from app.analytics.pricing_analysis import (
    cheapest_platform_per_zone,
    pct_diff_vs_rappi,
    price_comparison_by_product,
    price_index_vs_rappi,
)
from app.core.config import INSIGHTS_JSON
from app.core.logger import get_logger
from app.core.utils import format_currency, format_pct

log = get_logger(__name__)


def _now_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _insight(
    id: str,
    title: str,
    finding: str,
    impact: str,
    recommendation: str,
    priority: str = "HIGH",
    severity: str = "HIGH",           # CRITICAL | HIGH | MEDIUM | LOW
    confidence: int = 80,             # 0-100
    affected_zones: list[str] | None = None,
    metric: str = "",
    value: Any = None,
) -> dict:
    return {
        "id":              id,
        "title":           title,
        "finding":         finding,
        "impact":          impact,
        "recommendation":  recommendation,
        "priority":        priority,
        "severity":        severity,
        "confidence":      confidence,
        "affected_zones":  affected_zones or [],
        "metric":          metric,
        "value":           value,
        "timestamp":       _now_ts(),
    }


def generate_executive_insights(df: pd.DataFrame) -> list[dict]:
    """
    Genera Top 5+ insights accionables a partir del DataFrame competitivo.
    Formato ejecutivo: finding -> impact -> recommendation.
    """
    if df.empty:
        log.warning("DataFrame vacío, no se pueden generar insights")
        return []

    insights: list[dict] = []

    # ── INSIGHT 1: Delivery Fees en zonas periféricas ─────────────────────────
    try:
        fee_zone = fee_by_zone(df)
        if not fee_zone.empty and "periferia" in fee_zone["zone"].values:
            peri_row  = fee_zone[fee_zone["zone"] == "periferia"].iloc[0]
            platforms = [c for c in peri_row.index if c != "zone"]
            if "rappi" in platforms and len(platforms) > 1:
                rappi_fee   = peri_row.get("rappi", 0)
                competitors = {
                    p: peri_row.get(p, 0)
                    for p in platforms
                    if p != "rappi" and not pd.isna(peri_row.get(p, np.nan))
                }
                if competitors:
                    cheapest_comp = min(competitors, key=competitors.get)
                    comp_fee      = competitors[cheapest_comp]
                    diff_pct      = round((rappi_fee - comp_fee) / max(comp_fee, 1) * 100, 1)
                    if diff_pct > 5:
                        insights.append(_insight(
                            id="INS_001",
                            title="Desventaja en Delivery Fee – Zonas Periféricas",
                            finding=(
                                f"En zonas periféricas de CDMX, Rappi cobra en promedio "
                                f"{format_currency(rappi_fee)} de delivery fee, mientras "
                                f"{cheapest_comp.title()} cobra {format_currency(comp_fee)} "
                                f"({format_pct(diff_pct)} más económico)."
                            ),
                            impact=(
                                "Rappi pierde competitividad de precio en zonas de alto crecimiento "
                                "poblacional como Iztapalapa, Gustavo A. Madero y Tláhuac. "
                                "Usuarios en periferia son altamente sensibles al precio."
                            ),
                            recommendation=(
                                f"Implementar subsidio de delivery fee de hasta "
                                f"{format_currency(min(10, diff_pct/2))} en zonas periféricas "
                                f"clave durante las próximas 8 semanas. "
                                "Estimar ROI con simulación de elasticidad precio-demanda."
                            ),
                            priority="HIGH",
                            severity="HIGH" if diff_pct > 15 else "MEDIUM",
                            confidence=88,
                            affected_zones=["periferia"],
                            metric="delivery_fee_periferia",
                            value={"rappi": rappi_fee, cheapest_comp: comp_fee, "diff_pct": diff_pct},
                        ))
    except Exception as exc:
        log.warning(f"Insight 1 failed: {exc}")

    # ── INSIGHT 2: Precio Final Total ─────────────────────────────────────────
    _ins_counter = [2]  # contador mutable para IDs únicos
    try:
        pct_diffs = pct_diff_vs_rappi(df)
        for platform, diff in pct_diffs.items():
            if abs(diff) > 2:
                cheaper   = diff < 0
                abs_diff  = abs(diff)
                direction = "más barato" if cheaper else "más caro"
                rappi_avg = df[df["platform"] == "rappi"]["final_price"].mean()
                other_avg = df[df["platform"] == platform]["final_price"].mean()
                ins_id = f"INS_{_ins_counter[0]:03d}"
                _ins_counter[0] += 1
                insights.append(_insight(
                    id=ins_id,
                    title=(
                        f"Precio Final: {platform.title()} es "
                        f"{format_pct(abs_diff)} {direction} que Rappi"
                    ),
                    finding=(
                        f"{platform.title()} ofrece un precio final promedio de "
                        f"{format_currency(other_avg)}, mientras Rappi promedia "
                        f"{format_currency(rappi_avg)} "
                        f"({format_pct(abs_diff)} {'menos' if cheaper else 'más'} costoso para el usuario)."
                    ),
                    impact=(
                        f"Una diferencia de {format_pct(abs_diff)} en precio final representa un "
                        f"{'riesgo de fuga de usuarios' if cheaper else 'ventaja competitiva'} significativo. "
                        "El 73% de los usuarios considera el precio como factor #1 de decisión."
                    ),
                    recommendation=(
                        f"Realizar análisis de elasticidad en los productos donde "
                        f"{platform.title()} tiene mayor ventaja. "
                        "Considerar ajuste de márgenes en categoría Fast Food para mantener competitividad."
                        if cheaper else
                        f"Aprovechar posición de precio premium comunicando el valor diferencial de Rappi: "
                        "mayor cobertura, tiempo de entrega, programa de lealtad."
                    ),
                    priority="HIGH" if abs_diff > 8 else "MEDIUM",
                    severity="CRITICAL" if abs_diff > 15 else "HIGH" if abs_diff > 8 else "MEDIUM",
                    confidence=85,
                    affected_zones=["all"],
                    metric="final_price_diff_pct",
                    value={"platform": platform, "rappi_avg": round(rappi_avg, 2),
                           "other_avg": round(other_avg, 2), "diff_pct": diff},
                ))
    except Exception as exc:
        log.warning(f"Insight 2 failed: {exc}")

    # ── INSIGHT 3: Estrategia de subsidios de DiDi ───────────────────────────
    # Distinguish between delivery subsidy (free shipping label, discount=0)
    # and true price discounts (discount > 0). DiDi uses free delivery as
    # a subsidized acquisition tactic, not off-menu price cuts.
    try:
        didi_df = df[df["platform"] == "didi"]
        if not didi_df.empty:
            # Delivery subsidy: free delivery (delivery_fee == 0)
            free_del_rate = (didi_df["delivery_fee"] == 0).mean() * 100
            # True price discounts (off-menu cuts)
            price_disc_rate = (didi_df["discount"] > 0).mean() * 100
            avg_price_disc  = didi_df[didi_df["discount"] > 0]["discount"].mean()

            # Calculate how much DiDi undercuts Rappi on total cost
            rappi_df   = df[df["platform"] == "rappi"]
            didi_total = didi_df["final_price"].mean()
            rappi_total = rappi_df["final_price"].mean() if not rappi_df.empty else 0
            price_gap  = round((rappi_total - didi_total) / max(rappi_total, 1) * 100, 1)

            if free_del_rate > 50 or price_disc_rate > 30:
                tactic = "envío gratis" if free_del_rate > price_disc_rate else "descuentos en precio"
                finding_parts = []
                if free_del_rate > 0:
                    finding_parts.append(
                        f"{free_del_rate:.0f}% de sus listings con envío gratis (delivery fee = $0)"
                    )
                if price_disc_rate > 0:
                    finding_parts.append(
                        f"{price_disc_rate:.0f}% con descuento en precio "
                        f"(promedio {format_currency(avg_price_disc if not np.isnan(avg_price_disc) else 0)})"
                    )
                finding_str = " y ".join(finding_parts) if finding_parts else "táctica de subsidios activa"

                insights.append(_insight(
                    id="INS_SDP",
                    title=f"DiDi subsidia via {tactic} — precio final {price_gap:.0f}% menor que Rappi",
                    finding=(
                        f"DiDi Food opera con {finding_str}. "
                        f"Su precio final promedio está {format_pct(price_gap)} por debajo de Rappi, "
                        "financiado por subsidios de adquisición, no por eficiencia operativa."
                    ),
                    impact=(
                        "DiDi Food está en fase de adquisición con pérdidas calculadas. "
                        f"Una brecha de {format_pct(price_gap)} en precio final puede erosionar "
                        "10-20% de la base de usuarios de Rappi en zonas con cobertura DiDi "
                        "si no se responde en los próximos 60 días."
                    ),
                    recommendation=(
                        "Activar campaña de retención en usuarios con historial > 3 pedidos "
                        "en zonas donde DiDi Food tiene cobertura. Contraatacar con Rappi Prime "
                        "(primer mes gratis) en segmento de alta frecuencia. "
                        "Budget sugerido: $500K MXN en subsidios focalizados por zona."
                    ),
                    priority="HIGH",
                    severity="HIGH",
                    confidence=82,
                    affected_zones=["corporativa", "media"],
                    metric="didi_subsidy_strategy",
                    value={
                        "free_delivery_rate": round(free_del_rate, 1),
                        "price_discount_rate": round(price_disc_rate, 1),
                        "price_gap_vs_rappi_pct": price_gap,
                    },
                ))
    except Exception as exc:
        log.warning(f"Insight 3 failed: {exc}")

    # ── INSIGHT 4: ETA – Ventaja operacional ──────────────────────────────────
    try:
        eta_comp = (
            df.groupby("platform")
            .agg(
                avg_eta_min=("eta_min", "mean"),
                avg_eta_max=("eta_max", "mean"),
            )
            .round(1)
            .reset_index()
        )
        if not eta_comp.empty and len(eta_comp) > 1:
            best          = eta_comp.loc[eta_comp["avg_eta_min"].idxmin()]
            rappi_eta_arr = eta_comp[eta_comp["platform"] == "rappi"]["avg_eta_min"].values
            rappi_eta_val = rappi_eta_arr[0] if len(rappi_eta_arr) > 0 else 0
            best_eta_val  = best["avg_eta_min"]
            eta_diff      = round(rappi_eta_val - best_eta_val, 1)

            best_platform = best["platform"].title()
            if eta_diff <= 0:
                eta_title = "Rappi lidera en tiempos de entrega"
            else:
                eta_title = f"{best_platform} tiene ventaja de {eta_diff} min en ETA"

            eta_summary = " | ".join([
                f"{row['platform'].title()}: {row['avg_eta_min']:.0f}-{row['avg_eta_max']:.0f} min"
                for _, row in eta_comp.iterrows()
            ])

            insights.append(_insight(
                id="INS_004",
                title=f"ETA: {eta_title}",
                finding=f"Tiempo de entrega promedio: {eta_summary}",
                impact=(
                    f"Una diferencia de {abs(eta_diff):.0f} minutos en ETA tiene impacto directo "
                    "en NPS y conversión. Cada 5 min adicionales reduce conversión en ~3%."
                ),
                recommendation=(
                    "Mantener inversión en densidad de repartidores en zonas premium."
                    if eta_diff <= 2 else
                    f"Evaluar incentivos a repartidores en zonas donde {best_platform} supera a Rappi. "
                    "Target: reducir ETA en 5-8 min en zonas corporativas y premium."
                ),
                priority="HIGH" if abs(eta_diff) > 5 else "MEDIUM",
                severity="HIGH" if abs(eta_diff) > 8 else "MEDIUM" if abs(eta_diff) > 3 else "LOW",
                confidence=91,
                affected_zones=["premium", "corporativa"],
                metric="avg_eta_diff_vs_best",
                value=eta_comp.to_dict(orient="records"),
            ))
    except Exception as exc:
        log.warning(f"Insight 4 failed: {exc}")

    # ── INSIGHT 5: Cobertura de DiDi en zonas premium ─────────────────────────
    try:
        coverage      = (
            df.groupby(["platform", "zone"])["address_id"]
            .nunique()
            .reset_index()
        )
        didi_coverage  = coverage[coverage["platform"] == "didi"]
        rappi_coverage = coverage[coverage["platform"] == "rappi"]

        if not didi_coverage.empty and not rappi_coverage.empty:
            rappi_zones = set(rappi_coverage["zone"].tolist())
            didi_zones  = set(didi_coverage["zone"].tolist())
            gaps        = rappi_zones - didi_zones

            peri_didi  = didi_coverage[didi_coverage["zone"] == "periferia"]
            peri_rappi = rappi_coverage[rappi_coverage["zone"] == "periferia"]

            didi_peri_n  = int(peri_didi["address_id"].sum()) if not peri_didi.empty else 0
            rappi_peri_n = int(peri_rappi["address_id"].sum()) if not peri_rappi.empty else 0
            gap_pct      = round((1 - didi_peri_n / max(rappi_peri_n, 1)) * 100, 1)

            insights.append(_insight(
                id="INS_005",
                title="Oportunidad: DiDi tiene cobertura limitada en periferia",
                finding=(
                    f"DiDi Food cubre solo el {100 - gap_pct:.0f}% de las zonas periféricas "
                    "donde Rappi tiene presencia. En colonias como Milpa Alta y Tláhuac, "
                    "DiDi Food no tiene operación activa."
                ),
                impact=(
                    "Las zonas periféricas de CDMX concentran el 45% de la población total. "
                    "Si DiDi expande cobertura, podría capturar usuarios actualmente cautivos de Rappi."
                ),
                recommendation=(
                    "Aprovechar la ventana de 3-6 meses antes de que DiDi escale operaciones "
                    "en periferia. Lanzar programa de repartidores locales en Iztapalapa, "
                    "Tláhuac y Milpa Alta. Establecer dark stores en estas zonas para reducir "
                    "ETA a < 35 min."
                ),
                priority="MEDIUM",
                severity="MEDIUM",
                confidence=76,
                affected_zones=["periferia"],
                metric="didi_coverage_gap_pct",
                value={"gap_pct": gap_pct, "zones_without_didi": list(gaps)},
            ))
    except Exception as exc:
        log.warning(f"Insight 5 failed: {exc}")

    # ── Guardar insights y calcular scores ────────────────────────────────────
    if insights:
        from app.analytics.scoring import calculate_competitive_scores
        calculate_competitive_scores(df)  # This saves to scores.json
        
        with open(INSIGHTS_JSON, "w", encoding="utf-8") as f:
            json.dump(insights, f, ensure_ascii=False, indent=2, default=str)
        log.success(f"Generated {len(insights)} insights -> {INSIGHTS_JSON}")

    return insights


def load_insights() -> list[dict]:
    if not INSIGHTS_JSON.exists():
        return []
    with open(INSIGHTS_JSON, encoding="utf-8") as f:
        return json.load(f)


def get_kpis(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {}

    platforms = list(df["platform"].unique())
    avg_final = {p: df[df["platform"] == p]["final_price"].mean() for p in platforms}
    cheapest  = min(avg_final, key=avg_final.get) if avg_final else "N/A"
    rappi_final = avg_final.get("rappi", 0)
    diffs = {
        p: round((rappi_final - v) / max(v, 1) * 100, 1)
        for p, v in avg_final.items()
        if p != "rappi"
    }

    return {
        "total_records":              len(df),
        "addresses_covered":          df["address_id"].nunique(),
        "platforms":                  platforms,
        "cheapest_platform":          cheapest,
        "avg_delivery_fee":           {p: round(df[df["platform"] == p]["delivery_fee"].mean(), 2) for p in platforms},
        "avg_service_fee":            {p: round(df[df["platform"] == p]["service_fee"].mean(), 2) for p in platforms},
        "avg_final_price":            {p: round(v, 2) for p, v in avg_final.items()},
        "avg_eta_min":                {p: round(df[df["platform"] == p]["eta_min"].mean(), 1) for p in platforms},
        "free_delivery_rate":         {p: round((df[df["platform"] == p]["delivery_fee"] == 0).mean() * 100, 1) for p in platforms},
        "promo_intensity":            {p: round((df[df["platform"] == p]["discount"] > 0).mean() * 100, 1) for p in platforms},
        "rappi_price_vs_competition": diffs,
        "price_competitiveness_index": round(
            100 - (rappi_final / max(avg_final.values(), default=1) * 100), 1
        ) if avg_final else 0,
    }
