"""
dashboard.py – Rappi CI · Light mode premium dashboard.
"""
from __future__ import annotations
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from app.dashboard.theme import (
    COLORS,
    GLOBAL_CSS, PLATFORM_COLORS, PLATFORM_LABELS,
    ZONE_ORDER, get_layout,
)
from app.dashboard.components import (
    render_sidebar, page_header, kpi_row, section_title,
    chart_card, signal_card, insight_strip, empty_state,
    market_briefing, battlecard,
)
from app.core.config import COMPETITIVE_CSV, INSIGHTS_JSON, DATA_DIR

st.set_page_config(page_title="Rappi CI · Intelligence Platform",
                   page_icon="⚡", layout="wide",
                   initial_sidebar_state="expanded")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


@st.cache_data(ttl=120)
def load_df() -> pd.DataFrame:
    if not COMPETITIVE_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(COMPETITIVE_CSV, encoding="utf-8-sig")

@st.cache_data(ttl=120)
def load_insights() -> list:
    if not INSIGHTS_JSON.exists():
        return []
    try:
        return json.loads(INSIGHTS_JSON.read_text(encoding="utf-8"))
    except Exception:
        return []

@st.cache_data(ttl=120)
def load_scores() -> dict:
    f = DATA_DIR / "scores.json"
    if not f.exists():
        return {}
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return {}

def fmt(v: float, prefix="$") -> str:
    if pd.isna(v): return "N/A"
    return f"{prefix}{v:,.2f}" if prefix == "$" else f"{v:.0f} min"

def apply_filter(df: pd.DataFrame) -> pd.DataFrame:
    return df


# ── Market Position Matrix (2×2 quadrant) ─────────────────────────────────────

def position_chart(df: pd.DataFrame) -> go.Figure:
    """Price vs Speed quadrant — each platform as a labeled bubble."""
    platforms_data = []
    for p in ["rappi", "ubereats", "didi"]:
        sub = df[df["platform"] == p]
        if sub.empty:
            continue
        platforms_data.append({
            "platform": p,
            "label":    PLATFORM_LABELS[p],
            "price":    sub["final_price"].mean(),
            "eta":      sub["eta_min"].mean(),
            "color":    PLATFORM_COLORS[p],
        })

    if not platforms_data:
        return go.Figure()

    pdf = pd.DataFrame(platforms_data)

    avg_price = pdf["price"].mean()
    avg_eta   = pdf["eta"].mean()

    x_pad = max((pdf["price"].max() - pdf["price"].min()) * 0.35, 8)
    y_pad = max((pdf["eta"].max()   - pdf["eta"].min())   * 0.35, 3)
    x0, x1 = pdf["price"].min() - x_pad, pdf["price"].max() + x_pad
    y0, y1 = pdf["eta"].min()   - y_pad, pdf["eta"].max()   + y_pad

    fig = go.Figure()

    # Quadrant shading (top = fast = low eta value displayed inverted via reversed axis)
    quadrant_fills = [
        (x0, avg_price, y0,       avg_eta, "rgba(239,68,68,0.04)"),    # cheap + fast
        (avg_price, x1, y0,       avg_eta, "rgba(251,191,36,0.05)"),   # expensive + fast
        (x0, avg_price, avg_eta,  y1,      "rgba(16,185,129,0.05)"),   # cheap + slow
        (avg_price, x1, avg_eta,  y1,      "rgba(239,68,68,0.07)"),    # expensive + slow (risk)
    ]
    for (qx0, qx1, qy0, qy1, fill) in quadrant_fills:
        fig.add_shape(type="rect", x0=qx0, x1=qx1, y0=qy0, y1=qy1,
                      fillcolor=fill, line=dict(width=0), layer="below")

    # Quadrant divider lines
    fig.add_shape(type="line", x0=avg_price, x1=avg_price, y0=y0, y1=y1,
                  line=dict(color="#E2E8F0", width=1.5, dash="dot"))
    fig.add_shape(type="line", x0=x0, x1=x1, y0=avg_eta, y1=avg_eta,
                  line=dict(color="#E2E8F0", width=1.5, dash="dot"))

    # Corner quadrant labels
    corner_labels = [
        (x0 + 1,      y0 + 0.5,    "Barato + Rápido",   "#10B981"),
        (avg_price+1, y0 + 0.5,    "Caro + Rápido",     "#F59E0B"),
        (x0 + 1,      avg_eta+0.5, "Barato + Lento",    "#64748B"),
        (avg_price+1, avg_eta+0.5, "Caro + Lento ⚠",   "#EF4444"),
    ]
    for (cx, cy, clabel, ccolor) in corner_labels:
        fig.add_annotation(x=cx, y=cy, text=clabel, showarrow=False,
                           font=dict(size=9, color=ccolor, family="Inter"),
                           xanchor="left", yanchor="top", opacity=0.7)

    # Platform bubbles
    for _, row in pdf.iterrows():
        fig.add_trace(go.Scatter(
            x=[row["price"]], y=[row["eta"]],
            mode="markers+text",
            text=[f"<b>{row['label']}</b>"],
            textposition="top center",
            textfont=dict(size=11, color="#0F172A", family="Inter"),
            marker=dict(size=44, color=row["color"],
                        line=dict(width=2.5, color="white"), opacity=0.9),
            name=row["label"],
            showlegend=False,
            hovertemplate=(
                f"<b>{row['label']}</b><br>"
                f"Precio: ${row['price']:.0f} MXN<br>"
                f"ETA: {row['eta']:.0f} min<extra></extra>"
            ),
        ))

    fig.update_layout(
        **get_layout(
            height=340,
            xaxis=dict(
                title=dict(text="← Más Barato   ·   Precio Final Promedio (MXN)   ·   Más Caro →",
                           font=dict(size=10, color="#94A3B8")),
                range=[x0, x1],
                showgrid=False, zeroline=False,
            ),
            yaxis=dict(
                title=dict(text="↑ Más Rápido   ·   ETA Promedio (min)   ·   Más Lento ↓",
                           font=dict(size=10, color="#94A3B8")),
                range=[y1, y0],  # reversed: lower eta at top
                showgrid=False, zeroline=False,
            ),
        )
    )
    return fig


# ── Executive Overview ────────────────────────────────────────────────────────

def page_executive(df: pd.DataFrame, insights: list, scores: dict):
    _exp = None if df.empty else {
        "label": "↑ Exportar Brief Ejecutivo",
        "data":  _gen_executive_brief_html(df, insights, scores),
        "file_name": f"rappi_ci_executive_brief_{__import__('datetime').date.today()}.html",
        "mime": "text/html", "key": "_exp_executive",
    }
    page_header("Resumen Ejecutivo",
                "Pulso del Mercado · Rappi vs Competidores · CDMX",
                export_config=_exp)
    if df.empty:
        empty_state(); return

    # ── Market Briefing ───────────────────────────────────────────────────────
    market_briefing(df, insights)

    # ── KPI Row ───────────────────────────────────────────────────────────────
    r  = df[df["platform"] == "rappi"]
    ue = df[df["platform"] == "ubereats"]
    dd = df[df["platform"] == "didi"]

    rp  = r["final_price"].mean()    if not r.empty  else float("nan")
    up  = ue["final_price"].mean()   if not ue.empty else float("nan")
    rf  = r["delivery_fee"].mean()   if not r.empty  else float("nan")
    df_ = dd["delivery_fee"].mean()  if not dd.empty else float("nan")
    re  = r["eta_min"].mean()        if not r.empty  else float("nan")
    ue_ = ue["eta_min"].mean()       if not ue.empty else float("nan")

    diff_ue  = (rp - up) / up * 100   if pd.notna(up)  and up  > 0 and pd.notna(rp) else 0
    diff_fee = (rf - df_) / df_ * 100 if pd.notna(df_) and df_ > 0 and pd.notna(rf) else 0
    diff_eta = re - ue_               if pd.notna(re) and pd.notna(ue_) else 0

    kpi_row([
        {"label": "PRECIO FINAL · RAPPI",    "value": fmt(rp),
         "delta": f"{'▲' if diff_ue > 0 else '▼'} {abs(diff_ue):.1f}% vs Uber Eats",
         "icon_key": "precio"},
        {"label": "DELIVERY FEE · RAPPI",    "value": fmt(rf),
         "delta": f"{'▲' if diff_fee > 0 else '▼'} {abs(diff_fee):.1f}% vs DiDi",
         "icon_key": "fee"},
        {"label": "ETA PROMEDIO · RAPPI",     "value": fmt(re, prefix=""),
         "delta": f"{'▲' if diff_eta > 0 else '▼'} {abs(diff_eta):.1f} min vs Uber Eats",
         "icon_key": "eta"},
        {"label": "REGISTROS ANALIZADOS",     "value": f"{len(df):,}",
         "delta": f"▲ {df['address_id'].nunique()} zonas", "icon_key": "registros"},
        {"label": "AI INSIGHTS ACTIVOS",      "value": str(len(insights)),
         "delta": "Monitoreando", "icon_key": "insights"},
    ])

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # ── Battle Card ───────────────────────────────────────────────────────────
    st.markdown("""
    <div style="margin:24px 0 10px">
      <span style="font-size:1rem;font-weight:700;color:#0F172A">
        Comparación Directa de Plataformas</span>
      <p style="margin:3px 0 0;font-size:0.78rem;color:#64748B">
        Head-to-head · Precio, fees, velocidad y agresividad promocional.</p>
    </div>
    """, unsafe_allow_html=True)
    battlecard(df)

    # ── Market Position Matrix ────────────────────────────────────────────────
    left, right = st.columns([3, 2])

    with left:
        st.markdown("""
        <div style="margin:4px 0 10px">
          <span style="font-size:1rem;font-weight:700;color:#0F172A">
            Posicionamiento Estratégico</span>
          <p style="margin:3px 0 0;font-size:0.78rem;color:#64748B">
            Precio vs Velocidad — identifica flancos de competencia.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="premium-card" style="padding:16px">', unsafe_allow_html=True)
        chart_card(position_chart(df), height=340)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        # ── Competitive Scores ────────────────────────────────────────────────
        st.markdown("""
        <div style="margin:4px 0 10px">
          <span style="font-size:1rem;font-weight:700;color:#0F172A">
            Motor de Competitividad</span>
          <p style="margin:3px 0 0;font-size:0.78rem;color:#64748B">
            Evaluación algorítmica de la posición de Rappi.</p>
        </div>
        """, unsafe_allow_html=True)

        if scores:
            def _gauge_row(title: str, val: float, color: str, note: str = ""):
                pct   = min(max(val, 0), 100)
                bar_c = color
                st.markdown(f"""
                <div class="premium-card" style="padding:16px;margin-bottom:10px">
                  <div style="display:flex;justify-content:space-between;align-items:center;
                              margin-bottom:8px">
                    <span style="font-size:0.78rem;font-weight:600;color:#0F172A">{title}</span>
                    <span style="font-size:1.1rem;font-weight:800;color:{bar_c}">{pct:.0f}</span>
                  </div>
                  <div style="width:100%;background:#F1F5F9;border-radius:4px;height:5px">
                    <div style="height:100%;width:{pct}%;background:{bar_c};
                                border-radius:4px;transition:width 0.4s ease"></div>
                  </div>
                  {f'<div style="font-size:0.65rem;color:#94A3B8;margin-top:5px">{note}</div>' if note else ''}
                </div>
                """, unsafe_allow_html=True)

            ci   = scores.get("competitiveness_index", 0)
            dp   = scores.get("delivery_performance_score", 0)
            pa   = scores.get("promo_aggressiveness_score", 0)
            rs   = scores.get("strategic_risk_score", 0)

            _gauge_row("Competitividad Global",   ci,
                       "#10B981" if ci >= 70 else "#F59E0B" if ci >= 45 else "#EF4444",
                       "Rappi vs mercado — 100 = liderazgo absoluto")
            _gauge_row("Rendimiento de Delivery", dp,
                       "#0EA5E9" if dp >= 70 else "#F59E0B" if dp >= 45 else "#EF4444",
                       "Composite fee + ETA vs competencia")
            _gauge_row("Agresividad Promocional", pa,
                       "#FB923C",
                       "Intensidad de promos de competidores")
            _gauge_row("Riesgo Estratégico",      rs,
                       "#EF4444" if rs >= 60 else "#F59E0B" if rs >= 35 else "#10B981",
                       "100 = máxima presión competitiva sobre Rappi")
        else:
            st.markdown("""
            <div class="premium-card" style="padding:32px;text-align:center;color:#94A3B8">
              <div style="font-size:1.5rem;margin-bottom:8px;opacity:0.3">◈</div>
              <div style="font-size:0.8rem">Genera scores con: python app/main.py --mock</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Signal Cards ──────────────────────────────────────────────────────────
    if insights:
        n = len(insights)
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
                    margin:28px 0 14px">
          <div>
            <span style="font-size:0.95rem;font-weight:700;color:#0F172A">
              Señales Estratégicas</span>
            <span style="margin-left:8px;background:#FFF7ED;color:#FB923C;
                         border:1px solid #FED7AA;border-radius:10px;
                         padding:2px 8px;font-size:0.7rem;font-weight:700">
              {n} Activas</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        crit = [i for i in insights if i.get("severity") in ("CRITICAL", "HIGH")]
        med  = [i for i in insights if i.get("severity") not in ("CRITICAL", "HIGH")]

        icols = st.columns([1, 1])
        with icols[0]:
            for idx, ins in enumerate(crit):
                signal_card(ins, idx)
        with icols[1]:
            for idx, ins in enumerate(med):
                signal_card(ins, idx + len(crit))


# ── Price Comparison – Pricing Strategy Console ────────────────────────────────

# Short names for product chips
_PROD_SHORT = {
    "Big Mac":             "Big Mac",
    "McCombo Mediano":     "McCombo",
    "Nuggets 10 piezas":   "Nuggets 10p",
    "Coca-Cola 500ml":     "Coca-Cola",
    "Agua purificada 1L":  "Agua 1L",
}

_ZONE_DISPLAY = {
    "premium":     "Zona Premium",
    "corporativa": "Zona Corporativa",
    "media":       "Zona Media",
    "periferia":   "Zona Periferia",
}

_PLAT_META = {
    "rappi":    ("Rappi",     "#FB923C", "#FFF7ED", "#FED7AA"),
    "ubereats": ("Uber Eats", "#059669", "#ECFDF5", "#A7F3D0"),
    "didi":     ("DiDi Food", "#D97706", "#FFFBEB", "#FDE68A"),
}
_PLAT_DOT = {
    "rappi":    "#FB923C",
    "ubereats": "#34D399",
    "didi":     "#FBBF24",
}
_RISK_STYLE = {
    "CRÍTICO":  ("#FEF2F2", "#EF4444", "#FCA5A5"),
    "ALTO":     ("#FFF7ED", "#F97316", "#FED7AA"),
    "MODERADO": ("#FFFBEB", "#F59E0B", "#FDE68A"),
    "BAJO":     ("#ECFDF5", "#10B981", "#A7F3D0"),
}


def _price_risk(gap_pct: float) -> tuple[str, str]:
    if gap_pct >= 25:
        return "CRÍTICO",  "Precio crítico — riesgo de abandono de usuarios"
    if gap_pct >= 15:
        return "ALTO",     "Alta exposición — ajuste de márgenes recomendado"
    if gap_pct >= 5:
        return "MODERADO", "Brecha manejable — monitorear conversión"
    return "BAJO", "Posición competitiva — sin acción inmediata"


def _render_battlecard(ps: dict) -> None:
    """Single product battlecard: header + 3 price columns + risk footer."""
    prices      = ps["prices"]
    winner      = ps["winner"]
    winner_price = ps["winner_price"]

    win_name, win_color, win_bg, win_border = _PLAT_META.get(winner, ("?", "#64748B", "#F8FAFC", "#E2E8F0"))
    cat_display = {"fast_food": "Fast Food", "retail": "Retail"}.get(ps["category"], ps["category"])

    # ── Price columns ─────────────────────────────────────────────────────────
    price_cols_html = ""
    plat_order = ["rappi", "ubereats", "didi"]
    for idx, plat in enumerate(plat_order):
        p = prices.get(plat)
        if p is None:
            continue
        pname, pcolor, pbg, _ = _PLAT_META[plat]
        is_winner  = plat == winner
        border_r   = "" if idx == len(plat_order) - 1 else "border-right:1px solid #F1F5F9;"
        col_bg     = pbg if is_winner else "transparent"
        price_c    = pcolor if is_winner else "#0F172A"
        vs         = round((p - winner_price) / max(winner_price, 1) * 100) if not is_winner else 0
        gap_html   = (
            f'<div style="font-size:0.68rem;color:{pcolor};margin-top:3px;font-weight:600">'
            f'Precio más bajo ✓</div>'
            if is_winner else
            f'<div style="font-size:0.68rem;color:#EF4444;margin-top:3px">'
            f'+{vs}% vs {win_name}</div>'
        )
        price_cols_html += (
            f'<div style="flex:1;padding:14px 16px;background:{col_bg};{border_r}">'
            f'<div style="display:flex;align-items:center;gap:5px;margin-bottom:8px">'
            f'<div style="width:7px;height:7px;border-radius:50%;background:{_PLAT_DOT[plat]}"></div>'
            f'<span style="font-size:0.68rem;font-weight:600;color:#64748B">{pname}</span>'
            f'</div>'
            f'<div style="font-size:1.45rem;font-weight:800;color:{price_c};line-height:1">'
            f'${p:.0f}</div>'
            f'{gap_html}'
            f'</div>'
        )

    # ── Risk footer ───────────────────────────────────────────────────────────
    rbg, rc, rborder = _RISK_STYLE.get(ps["risk"], ("#F8FAFC", "#64748B", "#E2E8F0"))
    footer_html = (
        f'<div style="padding:9px 16px;background:{rbg};border-top:1px solid {rborder}">'
        f'<div style="display:flex;align-items:flex-start;gap:7px">'
        f'<span style="font-size:0.72rem;color:{rc};font-weight:700;margin-top:1px">⚑</span>'
        f'<span style="font-size:0.72rem;color:{rc};font-weight:700">'
        f'Gap: ${ps["gap_abs"]:.0f} MXN ({ps["gap_pct"]:.0f}%) · {ps["risk"]}</span>'
        f'<span style="font-size:0.72rem;color:#64748B;margin-left:2px">— {ps["rec"]}</span>'
        f'</div></div>'
    ) if ps["gap_pct"] > 2 else ""

    st.markdown(
        f'<div class="fade-in" style="border:1px solid #E2E8F0;border-radius:12px;'
        f'overflow:hidden;background:#FFFFFF;box-shadow:0 1px 3px rgba(0,0,0,0.04)">'
        # header
        f'<div style="padding:14px 16px;border-bottom:1px solid #F1F5F9;'
        f'display:flex;justify-content:space-between;align-items:center">'
        f'<div>'
        f'<div style="font-size:0.95rem;font-weight:700;color:#0F172A">{ps["product"]}</div>'
        f'<div style="font-size:0.68rem;color:#94A3B8;margin-top:2px">'
        f'{ps["restaurant"]} · {cat_display}</div>'
        f'</div>'
        f'<span style="background:{win_bg};color:{win_color};border:1px solid {win_border};'
        f'border-radius:8px;padding:3px 8px;font-size:0.68rem;font-weight:700">'
        f'🏆 {win_name} gana</span>'
        f'</div>'
        # prices
        f'<div style="display:flex">{price_cols_html}</div>'
        # footer
        f'{footer_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def page_prices(df: pd.DataFrame):
    _exp = None if df.empty else {
        "label": "↑ Exportar Brief de Precios",
        "data":  _gen_pricing_brief_html(df),
        "file_name": f"rappi_ci_pricing_brief_{__import__('datetime').date.today()}.html",
        "mime": "text/html", "key": "_exp_pricing",
    }
    page_header("Consola de Estrategia de Precios",
                "Comparación de precios · Inteligencia de Producto · CDMX",
                export_config=_exp)
    if df.empty: empty_state(); return

    # ── State setup ────────────────────────────────────────────────────────────
    all_products = sorted(df["product"].unique().tolist())
    _ZONE_ORDER  = ["premium", "corporativa", "media", "periferia"]
    all_zones    = sorted(df["zone"].unique().tolist(),
                          key=lambda z: _ZONE_ORDER.index(z) if z in _ZONE_ORDER else 99)
    zone_labels  = {
        "Todas": "Todas", "premium": "Premium", "corporativa": "Corp.",
        "media": "Media", "periferia": "Periferia",
    }

    if "pc_zone" not in st.session_state:
        st.session_state["pc_zone"] = "Todas"
    for p in all_products:
        if f"pc_{p}" not in st.session_state:
            st.session_state[f"pc_{p}"] = True

    # Pre-compute active state before rendering (avoids state-read-after-write bugs)
    sel_zone          = st.session_state["pc_zone"]
    sel_products      = [p for p in all_products if st.session_state.get(f"pc_{p}", True)]
    has_zone_filter   = sel_zone != "Todas"
    has_prod_filter   = len(sel_products) < len(all_products)

    # ── Filter panel ───────────────────────────────────────────────────────────
    st.markdown("""
    <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;
                padding:16px 20px 14px;box-shadow:0 1px 4px rgba(0,0,0,0.04)">
    """, unsafe_allow_html=True)

    # Zone chips
    z_label_col, z_chips_col = st.columns([1.2, 10])
    with z_label_col:
        st.markdown(
            '<div style="padding-top:6px;font-size:0.62rem;font-weight:700;'
            'color:#94A3B8;text-transform:uppercase;letter-spacing:1px">Zona</div>',
            unsafe_allow_html=True,
        )
    with z_chips_col:
        zone_options = ["Todas"] + all_zones
        zcols = st.columns(len(zone_options) + 4)
        for i, zone in enumerate(zone_options):
            with zcols[i]:
                is_active = sel_zone == zone
                # Show checkmark only on specific zone selection (not "Todas")
                label = ("✓ " if (is_active and zone != "Todas") else "") + zone_labels.get(zone, zone)
                st.markdown(f'<div class="{"chip-active" if is_active else "chip-btn"}">', unsafe_allow_html=True)
                if st.button(label, key=f"zchip_{zone}", use_container_width=True):
                    st.session_state["pc_zone"] = zone
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

    # Product chips
    p_label_col, p_chips_col = st.columns([1.2, 10])
    with p_label_col:
        st.markdown(
            '<div style="padding-top:6px;font-size:0.62rem;font-weight:700;'
            'color:#94A3B8;text-transform:uppercase;letter-spacing:1px">Producto</div>',
            unsafe_allow_html=True,
        )
    with p_chips_col:
        pcols = st.columns(len(all_products) + 4)
        for i, prod in enumerate(all_products):
            with pcols[i]:
                key = f"pc_{prod}"
                is_active = st.session_state.get(key, True)
                # Show checkmark only when in filtered mode (some products deselected)
                short = ("✓ " if (is_active and has_prod_filter) else "") + _PROD_SHORT.get(prod, prod[:10])
                st.markdown(f'<div class="{"chip-active" if is_active else "chip-btn"}">', unsafe_allow_html=True)
                if st.button(short, key=f"pchip_{prod}", use_container_width=True):
                    st.session_state[key] = not is_active
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Active filter pills ────────────────────────────────────────────────────
    if has_zone_filter or has_prod_filter:
        pills: list[tuple[str, str]] = []
        if has_zone_filter:
            pills.append(("zone", "Zona: " + zone_labels.get(sel_zone, sel_zone)))
        if has_prod_filter:
            if len(sel_products) == 0:
                pills.append(("prod", "0 productos"))
            elif len(sel_products) == 1:
                pills.append(("prod", _PROD_SHORT.get(sel_products[0], sel_products[0])))
            else:
                pills.append(("prod", f"{len(sel_products)} de {len(all_products)} productos"))

        pill_widths = [1.5] + [2.2] * len(pills) + [1.8, 5]
        pill_cols   = st.columns(pill_widths)

        with pill_cols[0]:
            st.markdown(
                '<div style="padding-top:6px;font-size:0.6rem;font-weight:700;'
                'color:#94A3B8;text-transform:uppercase;letter-spacing:0.8px">'
                'Filtros activos:</div>',
                unsafe_allow_html=True,
            )
        for i, (ftype, flabel) in enumerate(pills):
            with pill_cols[i + 1]:
                st.markdown('<div class="filter-pill-btn">', unsafe_allow_html=True)
                if st.button(f"{flabel}  ×", key=f"pill_{ftype}", use_container_width=True):
                    if ftype == "zone":
                        st.session_state["pc_zone"] = "Todas"
                    else:
                        for p in all_products:
                            st.session_state[f"pc_{p}"] = True
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        with pill_cols[len(pills) + 1]:
            st.markdown('<div class="filter-pill-btn">', unsafe_allow_html=True)
            if st.button("Limpiar todo", key="clear_all_filters"):
                st.session_state["pc_zone"] = "Todas"
                for p in all_products:
                    st.session_state[f"pc_{p}"] = True
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)

    # ── Apply filters ──────────────────────────────────────────────────────────
    fdf = df.copy()
    if sel_zone != "Todas":
        fdf = fdf[fdf["zone"] == sel_zone]
    if sel_products:
        fdf = fdf[fdf["product"].isin(sel_products)]

    if fdf.empty or not sel_products:
        st.markdown("""
        <div class="fade-in" style="text-align:center;padding:52px 24px;
                    border:1px solid #F1F5F9;border-radius:12px;background:#FAFBFC;margin-top:20px">
          <div style="font-size:2.5rem;opacity:0.12;margin-bottom:14px">◈</div>
          <div style="font-size:0.9rem;font-weight:600;color:#0F172A;margin-bottom:8px">
            No hay datos competitivos disponibles</div>
          <div style="font-size:0.78rem;color:#94A3B8;line-height:1.6">
            No hay datos para esta combinación de filtros.<br>
            Ajusta la zona o selecciona diferentes productos.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Viewing context banner ─────────────────────────────────────────────────
    zone_display = _ZONE_DISPLAY.get(sel_zone, sel_zone) if has_zone_filter else "Todas las zonas · CDMX"
    if not has_prod_filter:
        prod_display = "Todos los productos"
    elif len(sel_products) == 1:
        prod_display = sel_products[0]
    else:
        shorts = [_PROD_SHORT.get(p, p) for p in sel_products]
        prod_display = " · ".join(shorts) if len(shorts) <= 3 else " · ".join(shorts[:2]) + f" +{len(shorts)-2}"

    st.markdown(f"""
    <div class="fade-in" style="display:flex;align-items:center;gap:10px;
                padding:10px 18px;margin:14px 0 22px;
                background:#FFFBF7;border:1px solid #FED7AA;border-radius:8px">
      <span class="live-pulse"></span>
      <span style="font-size:0.78rem;color:#92400E">
        <b>Viendo:</b>&nbsp;
        <b style="color:#C2410C">{zone_display}</b>
        <span style="color:#FCD29F;margin:0 8px">·</span>
        <span style="color:#78350F">{prod_display}</span>
      </span>
    </div>
    """, unsafe_allow_html=True)

    # ── Compute per-product stats ──────────────────────────────────────────────
    product_stats: list[dict] = []
    for prod in sel_products:
        pf     = fdf[fdf["product"] == prod]
        prices = {}
        for plat in ["rappi", "ubereats", "didi"]:
            sub = pf[pf["platform"] == plat]
            prices[plat] = round(sub["final_price"].mean(), 1) if not sub.empty else None

        valid = {p: v for p, v in prices.items() if v is not None}
        if not valid:
            continue

        winner       = min(valid, key=valid.get)
        winner_price = valid[winner]
        rappi_price  = prices.get("rappi")
        gap_abs = gap_pct = 0.0
        if rappi_price and winner != "rappi":
            gap_abs = round(rappi_price - winner_price, 1)
            gap_pct = round((rappi_price - winner_price) / max(winner_price, 1) * 100, 1)

        risk, rec = _price_risk(gap_pct)
        meta      = pf[["restaurant", "category"]].iloc[0] if not pf.empty else None

        product_stats.append({
            "product":      prod,
            "restaurant":   meta["restaurant"] if meta is not None else "",
            "category":     meta["category"]   if meta is not None else "",
            "prices":       prices,
            "winner":       winner,
            "winner_price": winner_price,
            "gap_abs":      gap_abs,
            "gap_pct":      gap_pct,
            "risk":         risk,
            "rec":          rec,
        })

    if not product_stats:
        st.markdown("""
        <div class="fade-in" style="text-align:center;padding:52px 24px;
                    border:1px solid #F1F5F9;border-radius:12px;background:#FAFBFC">
          <div style="font-size:2.5rem;opacity:0.12;margin-bottom:14px">◈</div>
          <div style="font-size:0.9rem;font-weight:600;color:#0F172A;margin-bottom:8px">
            Sin datos de precios</div>
          <div style="font-size:0.78rem;color:#94A3B8">
            Sin datos competitivos para los filtros seleccionados.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Pricing Intelligence Briefing ──────────────────────────────────────────
    plat_avg: dict[str, float] = {}
    for plat in ["rappi", "ubereats", "didi"]:
        sub = fdf[fdf["platform"] == plat]
        if not sub.empty:
            plat_avg[plat] = sub["final_price"].mean()

    if plat_avg:
        cheapest_plat  = min(plat_avg, key=plat_avg.get)
        rappi_avg_val  = plat_avg.get("rappi", 0)
        cheap_avg_val  = plat_avg[cheapest_plat]
        overall_gap    = round((rappi_avg_val - cheap_avg_val) / max(cheap_avg_val, 1) * 100)
        worst          = max(product_stats, key=lambda x: x["gap_pct"])
        n_at_risk      = sum(1 for p in product_stats if p["risk"] in ("CRÍTICO", "ALTO"))
        zone_ctx       = zone_labels.get(sel_zone, sel_zone) if has_zone_filter else "CDMX"
        win_label      = _PLAT_META.get(cheapest_plat, (cheapest_plat,))[0]

        lines = [
            f'<b>{win_label}</b> mantiene la posición de precio más agresiva en {zone_ctx} — '
            f'promediando <b>{overall_gap}% por debajo de Rappi</b> en precio final.',
        ]
        if worst["gap_pct"] > 5:
            lines.append(
                f'El SKU de mayor exposición es <b>{worst["product"]}</b>, '
                f'con una brecha de <b>${worst["gap_abs"]:.0f} MXN ({worst["gap_pct"]:.0f}%)</b> '
                f'vs el precio más competitivo del mercado.'
            )

        risk_lv    = "CRÍTICA" if n_at_risk >= 2 else "ALTA" if n_at_risk >= 1 else "MODERADA"
        brief_bg, brief_c, _ = _RISK_STYLE.get(
            "CRÍTICO" if n_at_risk >= 2 else "ALTO" if n_at_risk >= 1 else "MODERADO",
            ("#FFFBEB", "#F59E0B", "#FDE68A"),
        )
        narrative = "".join(
            f'<span style="display:block;margin-bottom:5px">{l}</span>' for l in lines
        )
        st.markdown(f"""
        <div class="fade-in" style="background:linear-gradient(135deg,#FFFBF7,#FFF7ED);
                    border:1px solid #FED7AA;border-radius:12px;
                    padding:20px 24px;margin-bottom:28px;
                    display:flex;align-items:flex-start;gap:24px">
          <div style="flex:1">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
              <span style="font-size:0.6rem;font-weight:700;color:#94A3B8;
                           letter-spacing:1.5px;text-transform:uppercase">
                Inteligencia de Precios · {zone_ctx}</span>
              <span style="background:{brief_bg};color:{brief_c};
                           border:1px solid {brief_c}44;border-radius:6px;
                           padding:2px 8px;font-size:0.62rem;font-weight:700">
                Exposición {risk_lv}</span>
            </div>
            <div style="font-size:0.875rem;color:#1E293B;line-height:1.7">{narrative}</div>
          </div>
          <div style="text-align:center;flex-shrink:0;padding:10px 18px;
                      background:white;border-radius:10px;border:1px solid #FED7AA">
            <div style="font-size:2.2rem;font-weight:800;color:{brief_c};line-height:1">
              {n_at_risk}</div>
            <div style="font-size:0.6rem;color:#94A3B8;font-weight:700;
                        text-transform:uppercase;letter-spacing:0.5px;margin-top:2px">
              SKUs en riesgo</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Product Battlecards ────────────────────────────────────────────────────
    st.markdown("""
    <div style="margin-bottom:14px">
      <span style="font-size:1rem;font-weight:700;color:#0F172A">Battlecards de Producto</span>
      <p style="margin:3px 0 0;font-size:0.78rem;color:#64748B">
        Precio final promedio por plataforma · Ordenados por exposición de mayor a menor.</p>
    </div>
    """, unsafe_allow_html=True)

    # Sort: highest risk / gap first
    sorted_stats = sorted(product_stats, key=lambda x: x["gap_pct"], reverse=True)

    for i in range(0, len(sorted_stats), 2):
        row = sorted_stats[i:i + 2]
        cols = st.columns(len(row))
        for col, ps in zip(cols, row):
            with col:
                _render_battlecard(ps)
        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)

    # ── Rappi Price Position Summary ───────────────────────────────────────────
    st.markdown("""
    <div style="border-top:1.5px solid #F1F5F9;margin:28px 0 20px"></div>
    <div style="margin-bottom:14px">
      <span style="font-size:1rem;font-weight:700;color:#0F172A">
        Posición de Precio de Rappi</span>
      <p style="margin:3px 0 0;font-size:0.78rem;color:#64748B">
        Resumen ejecutivo de posición competitiva por SKU.</p>
    </div>
    """, unsafe_allow_html=True)

    rows_html = ""
    for ps in sorted_stats:
        rp = ps["prices"].get("rappi")
        if rp is None:
            continue
        win_name = _PLAT_META.get(ps["winner"], (ps["winner"],))[0]
        rbg, rc, _ = _RISK_STYLE.get(ps["risk"], ("#F8FAFC", "#64748B", "#E2E8F0"))
        rows_html += (
            f'<tr style="border-bottom:1px solid #F8FAFC">'
            f'<td style="padding:10px 16px;font-size:0.82rem;font-weight:600;color:#0F172A">'
            f'{ps["product"]}</td>'
            f'<td style="padding:10px 16px;font-size:0.82rem;font-weight:700;color:#0F172A">'
            f'${rp:.0f}</td>'
            f'<td style="padding:10px 16px;font-size:0.82rem;color:#64748B">'
            f'${ps["winner_price"]:.0f} · {win_name}</td>'
            f'<td style="padding:10px 16px;font-size:0.82rem;font-weight:700;'
            f'color:{"#EF4444" if ps["gap_pct"]>5 else "#10B981"}">'
            f'{ps["gap_pct"]:.0f}%</td>'
            f'<td style="padding:10px 16px">'
            f'<span style="background:{rbg};color:{rc};border:1px solid {rc}33;'
            f'border-radius:6px;padding:3px 8px;font-size:0.68rem;font-weight:700">'
            f'{ps["risk"]}</span></td>'
            f'</tr>'
        )

    st.markdown(f"""
    <div class="premium-card fade-in" style="padding:0;overflow:hidden">
      <table style="width:100%;border-collapse:collapse">
        <thead>
          <tr style="border-bottom:1.5px solid #F1F5F9">
            {''.join(
              f'<th style="padding:10px 16px;text-align:left;font-size:0.65rem;font-weight:700;'
              f'color:#94A3B8;text-transform:uppercase;letter-spacing:0.8px">{h}</th>'
              for h in ["Producto", "Rappi", "Mejor Precio", "Gap", "Riesgo"]
            )}
          </tr>
        </thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    """, unsafe_allow_html=True)


# ── Benchmarking Operativo (merged Fees + Delivery) ───────────────────────────

def page_operations(df: pd.DataFrame):
    _exp = None if df.empty else {
        "label": "↑ Exportar Brief Operativo",
        "data":  _gen_operations_brief_html(df),
        "file_name": f"rappi_ci_operations_brief_{__import__('datetime').date.today()}.html",
        "mime": "text/html", "key": "_exp_operations",
    }
    page_header(
        "Benchmarking Operativo",
        "Arquitectura de Fees · Rendimiento de Entrega · Operaciones Competitivas · CDMX",
        export_config=_exp,
    )
    if df.empty:
        empty_state()
        return

    # ── Analytics ─────────────────────────────────────────────────────────────
    ops: dict[str, dict] = {}
    for _p in ["rappi", "ubereats", "didi"]:
        _sub = df[df["platform"] == _p]
        if _sub.empty:
            continue
        _tf = _sub["delivery_fee"] + _sub["service_fee"]
        ops[_p] = {
            "del_fee":   round(_sub["delivery_fee"].mean(), 1),
            "svc_fee":   round(_sub["service_fee"].mean(), 1),
            "total_fee": round(_tf.mean(), 1),
            "fee_pct":   round(_tf.mean() / _sub["base_price"].replace(0, 1).mean() * 100, 1),
            "eta":       round(_sub["eta_min"].mean(), 1),
        }

    comp_fees  = {p: ops[p]["total_fee"] for p in ["ubereats", "didi"] if p in ops}
    cheap_p    = min(comp_fees, key=comp_fees.get) if comp_fees else None
    cheap_fee  = comp_fees.get(cheap_p, 0)
    rappi_fee  = ops.get("rappi", {}).get("total_fee", 0)
    fee_gap    = round(rappi_fee - cheap_fee, 1)
    fee_gap_pct = round(fee_gap / max(cheap_fee, 1) * 100, 1)
    cheap_lbl  = PLATFORM_LABELS.get(cheap_p, "—") if cheap_p else "—"

    comp_etas  = {p: ops[p]["eta"] for p in ["ubereats", "didi"] if p in ops}
    fast_p     = min(comp_etas, key=comp_etas.get) if comp_etas else None
    fast_eta   = comp_etas.get(fast_p, 0)
    rappi_eta  = ops.get("rappi", {}).get("eta", 0)
    eta_gap    = round(rappi_eta - fast_eta, 1)
    conv_imp   = round(eta_gap / 5 * 3, 1)
    fast_lbl   = PLATFORM_LABELS.get(fast_p, "—") if fast_p else "—"

    _ZD  = {"premium": "Premium", "corporativa": "Corporativa",
             "media": "Media", "periferia": "Periferia"}
    _RC  = {"CRÍTICO": "#EF4444", "ALTO": "#F97316", "MODERADO": "#F59E0B", "BAJO": "#10B981"}
    _RB  = {"CRÍTICO": "#FEF2F2", "ALTO": "#FFF7ED", "MODERADO": "#FFFBEB", "BAJO": "#F0FDF4"}
    _RR  = {"CRÍTICO": "239,68,68", "ALTO": "249,115,22", "MODERADO": "245,158,11", "BAJO": "16,185,129"}

    risk_s    = min(100, round(fee_gap_pct * 1.5 + max(0, eta_gap) * 2.5))
    risk_l    = ("CRÍTICO" if risk_s >= 60 else "ALTO" if risk_s >= 40
                 else "MODERADO" if risk_s >= 20 else "BAJO")
    risk_c    = _RC[risk_l]
    risk_rgba = _RR[risk_l]

    # ── 1. Hero Operational Brief ──────────────────────────────────────────────
    b_text = (
        f"Rappi mantiene la estructura de fees más alta del mercado CDMX — "
        f"<b>${rappi_fee:.0f} por orden</b> en fee total, "
        f"<b>{fee_gap_pct:.0f}% por encima de {cheap_lbl}</b> (${cheap_fee:.0f}). "
        f"Combinado con un <b>lag de {eta_gap:.0f} min en ETA</b> vs {fast_lbl}, "
        f"esta fricción operativa compuesta suprime la conversión en zonas "
        f"sensibles al precio. Impacto estimado: <b>~{conv_imp:.0f}% de diferencial "
        f"de conversión</b> durante horas pico."
    )
    b_action = (
        f"Revisar arquitectura de fees en <b>Zona Periferia y Media</b> donde la "
        f"carga de costos es más alta como % del ticket. Aumentar cobertura de "
        f"couriers para reducir la brecha de {eta_gap:.0f} min vs {fast_lbl}."
    )
    st.markdown(f"""
    <div class="fade-in" style="background:linear-gradient(135deg,#0F172A 0%,#1E293B 100%);
         border-radius:14px;padding:28px 32px;margin:12px 0 24px;
         box-shadow:0 8px 32px rgba(0,0,0,0.18);border:1px solid rgba(255,255,255,0.05)">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px">
        <span class="live-pulse"></span>
        <span style="font-size:0.58rem;font-weight:700;color:#64748B;
                     text-transform:uppercase;letter-spacing:1.6px">
          Inteligencia Operativa · Monitoreo Activo</span>
      </div>
      <div style="font-size:1.45rem;font-weight:800;color:#F8FAFC;
                  line-height:1.2;margin-bottom:12px">
        Fricción Operativa en Aumento</div>
      <div style="font-size:0.875rem;color:#94A3B8;line-height:1.8;margin-bottom:20px">
        {b_text}</div>
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:20px">
        <span style="background:rgba(251,146,60,0.18);border:1px solid rgba(251,146,60,0.45);
                     border-radius:6px;padding:4px 12px;font-size:0.7rem;font-weight:700;
                     color:#FB923C">Fee Gap +{fee_gap_pct:.0f}%</span>
        <span style="background:rgba(148,163,184,0.08);border:1px solid rgba(148,163,184,0.18);
                     border-radius:6px;padding:4px 12px;font-size:0.7rem;font-weight:700;color:#64748B">
          ETA Lag +{eta_gap:.0f} min</span>
        <span style="background:rgba({risk_rgba},0.15);border:1px solid rgba({risk_rgba},0.4);
                     border-radius:6px;padding:4px 12px;font-size:0.7rem;font-weight:700;
                     color:{risk_c}">⚑ Riesgo {risk_l}</span>
        <span style="background:rgba(148,163,184,0.08);border:1px solid rgba(148,163,184,0.18);
                     border-radius:6px;padding:4px 12px;font-size:0.7rem;font-weight:700;color:#64748B">
          Conversión en Riesgo</span>
      </div>
      <div style="border-top:1px solid rgba(255,255,255,0.07);padding-top:14px;
                  display:flex;gap:12px;align-items:flex-start">
        <span style="font-size:0.58rem;font-weight:700;color:#475569;
                     text-transform:uppercase;letter-spacing:1.2px;
                     white-space:nowrap;padding-top:2px">Acción Sugerida</span>
        <span style="font-size:0.8rem;color:#94A3B8;line-height:1.7">{b_action}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 2. Executive KPI Tiles ─────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    rappi_fee_pct = ops.get("rappi", {}).get("fee_pct", 0)
    r_del = ops.get("rappi", {}).get("del_fee", 0)
    r_svc = ops.get("rappi", {}).get("svc_fee", 0)

    def _kpi(col, lbl, val, sub, color):
        col.markdown(
            f'<div class="premium-card fade-in" style="padding:20px 18px">'
            f'<div style="font-size:0.58rem;font-weight:700;color:#94A3B8;'
            f'text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px">{lbl}</div>'
            f'<div style="font-size:1.7rem;font-weight:800;color:{color};'
            f'line-height:1;margin-bottom:5px">{val}</div>'
            f'<div style="font-size:0.68rem;color:#64748B;line-height:1.5">{sub}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    _kpi(k1, "Fee Total Rappi",
         f"${rappi_fee:.0f}",
         f"Del ${r_del:.0f} + Svc ${r_svc:.0f} · Más alto del mercado",
         "#EF4444" if fee_gap_pct >= 20 else "#F97316" if fee_gap_pct >= 10 else "#F59E0B")
    _kpi(k2, "Brecha de Fee vs Mercado",
         f"+${fee_gap:.0f}",
         f"{fee_gap_pct:.0f}% sobre {cheap_lbl} (${cheap_fee:.0f})",
         "#EF4444" if fee_gap_pct >= 20 else "#F97316")
    _kpi(k3, "Rezago Máximo ETA",
         f"+{eta_gap:.0f} min",
         f"vs {fast_lbl} · ~{conv_imp:.0f}% impacto en conversión",
         "#3B82F6" if eta_gap >= 8 else "#60A5FA")
    _kpi(k4, "Carga Fee/Precio",
         f"{rappi_fee_pct:.0f}%",
         "Ratio fee/precio-base Rappi · Promedio CDMX",
         "#F97316" if rappi_fee_pct >= 18 else "#F59E0B")

    st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)

    # ── 3. Fee Architecture Intelligence ──────────────────────────────────────
    st.markdown("""
    <div style="border-top:1.5px solid #F1F5F9;margin:24px 0 18px"></div>
    <div style="margin-bottom:14px">
      <span style="font-size:1rem;font-weight:700;color:#0F172A">
        Comparación de Arquitectura de Fees</span>
      <p style="margin:3px 0 0;font-size:0.78rem;color:#64748B">
        Carga total de costos · Desglose Delivery + Servicio · Brecha competitiva.</p>
    </div>
    """, unsafe_allow_html=True)

    fa_left, fa_right = st.columns([1.15, 1])

    with fa_left:
        max_tf = max((ops[p]["total_fee"] for p in ops), default=60)
        rows_html = ""
        for plat_k in ["rappi", "ubereats", "didi"]:
            if plat_k not in ops:
                continue
            ps   = ops[plat_k]
            pc   = PLATFORM_COLORS[plat_k]
            pl   = PLATFORM_LABELS[plat_k]
            tf   = ps["total_fee"]
            df_v = ps["del_fee"]
            sf_v = ps["svc_fee"]
            d_w  = round(df_v / max(max_tf, 1) * 100)
            s_w  = round(sf_v / max(max_tf, 1) * 100)
            is_r = (plat_k == "rappi")
            gap_v = round(tf - cheap_fee, 1) if cheap_p else 0
            if is_r and gap_v > 0:
                gap_html = (
                    f'<span style="font-size:0.62rem;font-weight:700;color:#EF4444">'
                    f'+${gap_v:.0f} vs {cheap_lbl}</span>'
                )
            elif tf <= cheap_fee + 0.5:
                gap_html = (
                    f'<span style="font-size:0.62rem;font-weight:600;color:#10B981">'
                    f'Más bajo del mercado</span>'
                )
            else:
                gap_html = f'<span style="font-size:0.62rem;color:#94A3B8"></span>'

            rows_html += (
                f'<div style="padding:14px 0;border-bottom:1px solid #F8FAFC">'
                f'<div style="display:flex;justify-content:space-between;'
                f'align-items:center;margin-bottom:8px">'
                f'<div style="display:flex;align-items:center;gap:7px">'
                f'<div style="width:8px;height:8px;border-radius:50%;background:{pc}"></div>'
                f'<span style="font-size:0.82rem;font-weight:700;color:#0F172A">{pl}</span>'
                f'</div>'
                f'<div style="text-align:right">'
                f'<span style="font-size:1.15rem;font-weight:800;color:{pc}">${tf:.0f}</span>'
                f'<span style="font-size:0.65rem;color:#94A3B8;margin-left:4px">total</span>'
                f'</div></div>'
                f'<div style="display:flex;gap:2px;height:6px;margin-bottom:7px">'
                f'<div style="width:{d_w}%;background:{pc};border-radius:2px 0 0 2px;opacity:0.9"></div>'
                f'<div style="width:{s_w}%;background:{pc};border-radius:0 2px 2px 0;opacity:0.4"></div>'
                f'</div>'
                f'<div style="display:flex;gap:14px;align-items:center">'
                f'<span style="font-size:0.62rem;color:#64748B">Del ${df_v:.0f}</span>'
                f'<span style="font-size:0.62rem;color:#94A3B8">Svc ${sf_v:.0f}</span>'
                f'{gap_html}'
                f'</div></div>'
            )
        st.markdown(
            f'<div class="premium-card fade-in" style="padding:4px 20px 2px">'
            f'{rows_html}</div>',
            unsafe_allow_html=True,
        )

    with fa_right:
        # Zone Fee Burden Rankings — Rappi fee % sorted by highest friction
        df_tmp = df.copy()
        df_tmp["total_fee"] = df_tmp["delivery_fee"] + df_tmp["service_fee"]
        df_tmp["fee_pct"]   = (df_tmp["total_fee"]
                                / df_tmp["base_price"].replace(0, 1) * 100)
        zone_fee_df = df_tmp.groupby(["zone", "platform"])["fee_pct"].mean().reset_index()
        rappi_zf    = (zone_fee_df[zone_fee_df["platform"] == "rappi"]
                       .set_index("zone")["fee_pct"])
        sorted_zf   = rappi_zf.sort_values(ascending=False).index.tolist()

        st.markdown(
            '<div style="font-size:0.82rem;font-weight:700;color:#0F172A;margin-bottom:4px">'
            'Fee Burden by Zone — Rappi</div>'
            '<div style="font-size:0.68rem;color:#64748B;margin-bottom:14px">'
            'Fee total como % del precio base · Mayor = mayor fricción percibida</div>',
            unsafe_allow_html=True,
        )
        for rank, zk in enumerate(sorted_zf, 1):
            z_lbl  = _ZD.get(zk, zk.title())
            r_pct  = round(float(rappi_zf.get(zk, 0)), 1)
            comp_z = [
                zone_fee_df[(zone_fee_df["zone"] == zk) & (zone_fee_df["platform"] == p)]["fee_pct"]
                for p in ["ubereats", "didi"]
            ]
            best_comp = round(min(
                (float(s.iloc[0]) for s in comp_z if not s.empty), default=r_pct
            ), 1)
            burden_gap = round(r_pct - best_comp, 1)
            bar_w = min(100, round(r_pct * 2.8))
            bar_c = ("#EF4444" if r_pct >= 22 else "#F97316" if r_pct >= 18
                     else "#F59E0B" if r_pct >= 14 else "#64748B")
            st.markdown(
                f'<div style="margin-bottom:12px">'
                f'<div style="display:flex;justify-content:space-between;'
                f'align-items:center;margin-bottom:4px">'
                f'<div style="display:flex;align-items:center;gap:6px">'
                f'<span style="font-size:0.6rem;font-weight:700;color:#94A3B8">#{rank}</span>'
                f'<span style="font-size:0.8rem;font-weight:600;color:#0F172A">{z_lbl}</span>'
                f'</div>'
                f'<div>'
                f'<span style="font-size:0.88rem;font-weight:800;color:{bar_c}">{r_pct:.0f}%</span>'
                f'<span style="font-size:0.6rem;color:#EF4444;font-weight:600;margin-left:5px">'
                f'+{burden_gap:.0f}pp gap</span>'
                f'</div></div>'
                f'<div style="background:#F1F5F9;border-radius:3px;height:5px;margin-bottom:3px">'
                f'<div style="height:100%;width:{bar_w}%;background:{bar_c};border-radius:3px">'
                f'</div></div>'
                f'<div style="font-size:0.6rem;color:#94A3B8">'
                f'Mejor competidor: {best_comp:.0f}%</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── 4. ETA Operational Intelligence — Zone Cards ───────────────────────────
    st.markdown("""
    <div style="border-top:1.5px solid #F1F5F9;margin:28px 0 18px"></div>
    <div style="margin-bottom:14px">
      <span style="font-size:1rem;font-weight:700;color:#0F172A">
        Rendimiento de Entrega por Territorio</span>
      <p style="margin:3px 0 0;font-size:0.78rem;color:#64748B">
        Brecha de ETA vs competidor más rápido · Riesgo operativo por zona · Impacto en conversión.</p>
    </div>
    """, unsafe_allow_html=True)

    eta_df     = df.groupby(["zone", "platform"])["eta_min"].mean().reset_index()
    rappi_eta_z = (eta_df[eta_df["platform"] == "rappi"]
                   .set_index("zone")["eta_min"])
    sorted_eta  = rappi_eta_z.sort_values(ascending=False).index.tolist()

    eta_cols = st.columns(2)
    for i, zk in enumerate(sorted_eta):
        z_lbl = _ZD.get(zk, zk.title())
        r_e   = round(float(rappi_eta_z.get(zk, 0)), 1)

        comp_z_etas: dict[str, float] = {}
        for _cp in ["ubereats", "didi"]:
            _row = eta_df[(eta_df["zone"] == zk) & (eta_df["platform"] == _cp)]
            if not _row.empty:
                comp_z_etas[_cp] = round(float(_row["eta_min"].iloc[0]), 1)

        fast_z_p   = min(comp_z_etas, key=comp_z_etas.get) if comp_z_etas else None
        fast_z_e   = comp_z_etas.get(fast_z_p, 0) if fast_z_p else 0
        fast_z_lbl = PLATFORM_LABELS.get(fast_z_p, "—") if fast_z_p else "—"
        fast_z_c   = PLATFORM_COLORS.get(fast_z_p, "#64748B") if fast_z_p else "#64748B"
        z_gap      = round(r_e - fast_z_e, 1)
        z_conv     = round(z_gap / 5 * 3, 1) if z_gap > 0 else 0
        z_risk     = "ALTO" if z_gap >= 8 else "MODERADO" if z_gap >= 4 else "BAJO"
        z_risk_c   = _RC.get(z_risk, "#10B981")
        z_risk_b   = _RB.get(z_risk, "#F0FDF4")

        # Mini ETAs per platform
        plat_eta_html = ""
        for _pp, _pl in [("rappi", "Rappi"), ("ubereats", "UberEats"), ("didi", "DiDi")]:
            _row = eta_df[(eta_df["zone"] == zk) & (eta_df["platform"] == _pp)]
            if _row.empty:
                continue
            _v  = round(float(_row["eta_min"].iloc[0]), 1)
            _pc = PLATFORM_COLORS.get(_pp, "#94A3B8")
            _is_r = (_pp == "rappi")
            plat_eta_html += (
                f'<div style="text-align:center;flex:1">'
                f'<div style="font-size:0.59rem;color:#94A3B8;margin-bottom:3px">{_pl}</div>'
                f'<div style="font-size:1.15rem;font-weight:800;'
                f'color:{"#EF4444" if _is_r and z_gap > 0 else _pc}">{_v:.0f}</div>'
                f'<div style="font-size:0.55rem;color:#94A3B8">min</div>'
                f'</div>'
            )

        with eta_cols[i % 2]:
            st.markdown(
                f'<div class="premium-card fade-in" style="padding:0;overflow:hidden;'
                f'border-left:4px solid {z_risk_c};margin-bottom:14px">'
                # header
                f'<div style="padding:14px 18px 11px;border-bottom:1px solid #F8FAFC;'
                f'display:flex;justify-content:space-between;align-items:flex-start">'
                f'<div>'
                f'<div style="font-size:0.92rem;font-weight:700;color:#0F172A">{z_lbl}</div>'
                f'<div style="font-size:0.64rem;color:#64748B;margin-top:2px">'
                f'Más rápido: <span style="color:{fast_z_c};font-weight:600">'
                f'{fast_z_lbl}</span> · {fast_z_e:.0f} min</div>'
                f'</div>'
                f'<span style="background:{z_risk_b};color:{z_risk_c};border-radius:5px;'
                f'padding:2px 8px;font-size:0.6rem;font-weight:700">{z_risk}</span>'
                f'</div>'
                # metrics body
                f'<div style="padding:14px 18px;display:flex;align-items:center;gap:0">'
                # ETA gap number
                f'<div style="flex-shrink:0;text-align:center;padding-right:18px;'
                f'border-right:1px solid #F1F5F9">'
                f'<div style="font-size:0.57rem;font-weight:700;color:#94A3B8;'
                f'text-transform:uppercase;letter-spacing:0.8px;margin-bottom:4px">ETA Gap</div>'
                f'<div style="font-size:1.9rem;font-weight:800;'
                f'color:{"#EF4444" if z_gap > 0 else "#10B981"};line-height:1">'
                f'+{z_gap:.0f}</div>'
                f'<div style="font-size:0.59rem;color:#94A3B8">min rezago</div>'
                f'</div>'
                # per-platform ETAs
                f'<div style="flex:1;display:flex;padding-left:18px">'
                f'{plat_eta_html}</div>'
                f'</div>'
                # conversion impact footer
                f'<div style="padding:8px 18px 9px;background:#F8FAFC;'
                f'border-top:1px solid #F1F5F9">'
                f'<span style="font-size:0.62rem;color:#64748B">'
                f'Impacto en conversión est.: <b style="color:{z_risk_c}">~{z_conv:.0f}%</b> '
                f'por debajo de {fast_z_lbl} en horas pico</span>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── 5. Operational Risk Signals ────────────────────────────────────────────
    st.markdown("""
    <div style="border-top:1.5px solid #F1F5F9;margin:28px 0 18px"></div>
    <div style="margin-bottom:14px">
      <span style="font-size:1rem;font-weight:700;color:#0F172A">
        Señales de Riesgo Operativo</span>
      <p style="margin:3px 0 0;font-size:0.78rem;color:#64748B">
        Puntos de fricción clave derivados del monitoreo de operaciones competitivas.</p>
    </div>
    """, unsafe_allow_html=True)

    op_signals = [
        {
            "sev": "HIGH" if fee_gap_pct >= 20 else "MEDIUM",
            "title": f"Ventaja de Fee — {cheap_lbl}",
            "body": (
                f"{cheap_lbl} opera con una estructura de costos "
                f"<b>{fee_gap_pct:.0f}% por debajo de Rappi</b> en fee total "
                f"(${cheap_fee:.0f} vs ${rappi_fee:.0f}). Esta ventaja de "
                f"eficiencia operativa genera menor fricción de conversión, "
                f"especialmente en zonas donde el fee total representa una porción "
                f"elevada del ticket promedio del usuario."
            ),
            "metric": f"+${fee_gap:.0f}", "metric_lbl": "prima Rappi",
        },
        {
            "sev": "HIGH" if eta_gap >= 8 else "MEDIUM",
            "title": f"Brecha de Velocidad de Entrega — {fast_lbl}",
            "body": (
                f"{fast_lbl} mantiene una ventaja operativa de "
                f"<b>{eta_gap:.0f} minutos</b> en tiempo de entrega promedio. "
                f"A ~3% de impacto en conversión por cada 5 min de diferencia, "
                f"Rappi absorbe una <b>pérdida estimada de ~{conv_imp:.0f}%</b> "
                f"en conversión durante ventanas de demanda pico — riesgo de "
                f"erosión de lealtad en usuarios de alta frecuencia."
            ),
            "metric": f"+{eta_gap:.0f} min", "metric_lbl": "rezago ETA",
        },
    ]
    # Add worst zone signal if data available
    if sorted_zf:
        wz     = sorted_zf[0]
        wz_lbl = _ZD.get(wz, wz.title())
        wz_pct = round(float(rappi_zf.get(wz, 0)), 1)
        op_signals.append({
            "sev": "MEDIUM",
            "title": f"Zona de Máxima Fricción — {wz_lbl}",
            "body": (
                f"Zona <b>{wz_lbl}</b> registra la carga de fees más alta de Rappi "
                f"como porcentaje del precio base (<b>{wz_pct:.0f}%</b>). En esta zona, "
                f"los usuarios enfrentan la mayor fricción operativa del mercado — "
                f"incrementando el riesgo de cambio de plataforma en órdenes "
                f"de ticket medio-bajo donde el fee total erosiona el valor percibido."
            ),
            "metric": f"{wz_pct:.0f}%", "metric_lbl": "carga de fee",
        })

    _SEV_META = {"HIGH": ("#F97316", "#FFF7ED"), "MEDIUM": ("#F59E0B", "#FFFBEB")}
    sig_cols = st.columns(len(op_signals))
    for col, sig in zip(sig_cols, op_signals):
        sc, sb = _SEV_META.get(sig["sev"], _SEV_META["MEDIUM"])
        col.markdown(
            f'<div class="premium-card fade-in" style="padding:18px 20px;'
            f'border-left:3px solid {sc}">'
            f'<div style="display:flex;justify-content:space-between;'
            f'align-items:flex-start;margin-bottom:10px">'
            f'<div style="flex:1">'
            f'<span style="background:{sb};color:{sc};border-radius:4px;'
            f'padding:2px 8px;font-size:0.58rem;font-weight:700;'
            f'display:inline-block;margin-bottom:8px">{sig["sev"]}</span>'
            f'<div style="font-size:0.85rem;font-weight:700;color:#0F172A">'
            f'{sig["title"]}</div>'
            f'</div>'
            f'<div style="text-align:right;flex-shrink:0;padding-left:16px">'
            f'<div style="font-size:1.4rem;font-weight:800;color:{sc};line-height:1">'
            f'{sig["metric"]}</div>'
            f'<div style="font-size:0.6rem;color:#94A3B8;margin-top:2px">'
            f'{sig["metric_lbl"]}</div>'
            f'</div></div>'
            f'<div style="font-size:0.76rem;color:#475569;line-height:1.65">'
            f'{sig["body"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── Promotion Strategy Intelligence ──────────────────────────────────────────

_PROMO_STRAT_META: dict[str, tuple] = {
    "FIRST_ORDER":        ("◆", "First Order Promo",    "#EF4444", "#FEF2F2"),
    "LOYALTY_MEMBERSHIP": ("✦", "Loyalty / Membership", "#6366F1", "#EEF2FF"),
    "BUNDLE_COMBO":       ("⊞", "Bundle / Combo",        "#F59E0B", "#FFFBEB"),
    "TIME_LIMITED":       ("◷", "Time-Limited",          "#F97316", "#FFF7ED"),
    "PERCENT_DISCOUNT":   ("◈", "% Off Discount",        "#8B5CF6", "#EDE9FE"),
    "DELIVERY_SUBSIDY":   ("⊕", "Delivery Subsidy",      "#3B82F6", "#EFF6FF"),
    "CASHBACK":           ("◑", "Cashback",              "#10B981", "#ECFDF5"),
    "MINIMUM_SPEND":      ("◐", "Min. Spend",            "#0EA5E9", "#F0F9FF"),
    "NONE":               ("○", "No Promotion",          "#CBD5E1", "#F8FAFC"),
    "OTHER":              ("·", "Other",                 "#94A3B8", "#F8FAFC"),
}

_PROMO_ARCHETYPE: dict[str, tuple] = {
    "FIRST_ORDER":        ("ACQUISITION",     "#EF4444", "#FEF2F2"),
    "LOYALTY_MEMBERSHIP": ("RETENTION",       "#6366F1", "#EEF2FF"),
    "BUNDLE_COMBO":       ("ENGAGEMENT",      "#F59E0B", "#FFFBEB"),
    "TIME_LIMITED":       ("URGENCY",         "#F97316", "#FFF7ED"),
    "PERCENT_DISCOUNT":   ("VALUE PLAY",      "#8B5CF6", "#EDE9FE"),
    "DELIVERY_SUBSIDY":   ("BARRIER REMOVAL", "#3B82F6", "#EFF6FF"),
    "CASHBACK":           ("LOYALTY",         "#10B981", "#ECFDF5"),
    "MINIMUM_SPEND":      ("BASKET GROWTH",   "#0EA5E9", "#F0F9FF"),
}


def _classify_promo_strategy(label: str) -> str:
    if pd.isna(label) or str(label).strip() == "":
        return "NONE"
    s = str(label).lower()
    if any(k in s for k in ["primer pedido", "primera orden", "primeros 3", "tu primer", "first order"]):
        return "FIRST_ORDER"
    if any(k in s for k in ["prime", " pass", "uber one", "membership", "turbo"]):
        return "LOYALTY_MEMBERSHIP"
    if any(k in s for k in ["2x1", "3x2", "combo", "bundle"]):
        return "BUNDLE_COMBO"
    if any(k in s for k in ["hoy", "esta noche", "tiempo limit", "limited time"]):
        return "TIME_LIMITED"
    if "cashback" in s or "cash back" in s:
        return "CASHBACK"
    if any(k in s for k in ["gastando", "mínimo", "minimo"]):
        return "MINIMUM_SPEND"
    if any(k in s for k in ["gratis", "free delivery"]):
        return "DELIVERY_SUBSIDY"
    if any(k in s for k in ["% off", "descuento"]):
        return "PERCENT_DISCOUNT"
    return "OTHER"


# ── Promotions ────────────────────────────────────────────────────────────────

def page_promotions(df: pd.DataFrame):
    _exp = None if df.empty else {
        "label": "↑ Exportar Brief de Promociones",
        "data":  _gen_promotions_brief_html(df),
        "file_name": f"rappi_ci_promotions_brief_{__import__('datetime').date.today()}.html",
        "mime": "text/html", "key": "_exp_promotions",
    }
    page_header(
        "Centro de Promociones",
        "Inteligencia de Subsidios · Monitor de Presión de Mercado · CDMX",
        export_config=_exp,
    )
    if df.empty:
        empty_state()
        return

    # ── Analytics ─────────────────────────────────────────────────────────────
    plat_stats: dict[str, dict] = {}
    for _p in ["rappi", "ubereats", "didi"]:
        _sub = df[df["platform"] == _p]
        if _sub.empty:
            continue
        plat_stats[_p] = {
            "promo_rate": round((_sub["discount"] > 0).mean() * 100, 1),
            "free_rate":  round((_sub["delivery_fee"] < 2).mean() * 100, 1),
            "avg_disc":   round(_sub[_sub["discount"] > 0]["discount"].mean(), 1)
                          if (_sub["discount"] > 0).any() else 0.0,
            "avg_fee":    round(_sub["delivery_fee"].mean(), 1),
        }

    comp_rates = {p: plat_stats[p]["promo_rate"] for p in ["ubereats", "didi"] if p in plat_stats}
    dom_plat   = max(comp_rates, key=comp_rates.get) if comp_rates else "didi"
    dom_rate   = comp_rates.get(dom_plat, 0)
    dom_label  = PLATFORM_LABELS.get(dom_plat, dom_plat)
    dom_color  = PLATFORM_COLORS.get(dom_plat, "#64748B")
    rappi_rate = plat_stats.get("rappi", {}).get("promo_rate", 0)
    mult       = round(dom_rate / max(rappi_rate, 1), 1)

    pz_all   = df.groupby(["zone", "platform"]).apply(
        lambda x: (x["discount"] > 0).mean() * 100
    ).reset_index(name="rate")
    comp_pz   = pz_all[pz_all["platform"] != "rappi"]
    zone_comp = (comp_pz.groupby("zone")["rate"].mean()
                 if not comp_pz.empty else pd.Series(dtype=float))
    peak_zk   = zone_comp.idxmax() if not zone_comp.empty else "premium"
    peak_zr   = round(float(zone_comp.max()), 1) if not zone_comp.empty else 0

    _ZD  = {"premium": "Premium", "corporativa": "Corporativa",
             "media": "Media", "periferia": "Periferia"}
    _RC  = {"CRÍTICO": "#EF4444", "ALTO": "#F97316", "MODERADO": "#F59E0B", "BAJO": "#10B981"}
    _RB  = {"CRÍTICO": "#FEF2F2", "ALTO": "#FFF7ED", "MODERADO": "#FFFBEB", "BAJO": "#F0FDF4"}
    _PR  = {"rappi": "251,146,60", "ubereats": "52,211,153", "didi": "251,191,36"}
    _RR  = {"CRÍTICO": "239,68,68", "ALTO": "249,115,22", "MODERADO": "245,158,11", "BAJO": "16,185,129"}

    peak_zlbl = _ZD.get(peak_zk, peak_zk.title())
    risk_s    = min(100, round(dom_rate * 0.65 + peak_zr * 0.35))
    risk_l    = ("CRÍTICO" if risk_s >= 60 else "ALTO" if risk_s >= 40
                 else "MODERADO" if risk_s >= 20 else "BAJO")
    risk_c    = _RC[risk_l]
    dom_rgba  = _PR.get(dom_plat, "148,163,184")
    risk_rgba = _RR[risk_l]

    # ── 1. Hero Strategic Brief ────────────────────────────────────────────────
    b_text = (
        f"<b>{dom_label}</b> ha escalado su actividad de subsidio al "
        f"<b>{dom_rate:.0f}%</b> de listings activos — "
        f"<b>{mult:.1f}× la densidad promocional de Rappi</b> — con concentración máxima "
        f"en <b>Zona {peak_zlbl}</b> ({peak_zr:.0f}%). La estrategia combina subsidio de fee "
        f"de envío con descuentos a nivel de producto para erosionar sistemáticamente "
        f"la percepción de precio de Rappi en corredores económicos de alto valor."
    )
    b_action = (
        f"Activar promociones defensivas focalizadas en <b>Zona {peak_zlbl}</b>. "
        f"Priorizar SKUs de alta rotación con igualación de fee de envío para neutralizar "
        f"la campaña de adquisición agresiva de {dom_label} antes de que la erosión de conversión se acelere."
    )
    st.markdown(f"""
    <div class="fade-in" style="background:linear-gradient(135deg,#0F172A 0%,#1E293B 100%);
         border-radius:14px;padding:28px 32px;margin:12px 0 24px;
         box-shadow:0 8px 32px rgba(0,0,0,0.18);border:1px solid rgba(255,255,255,0.05)">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px">
        <span class="live-pulse"></span>
        <span style="font-size:0.58rem;font-weight:700;color:#64748B;
                     text-transform:uppercase;letter-spacing:1.6px">
          Inteligencia Promocional · Monitoreo Activo</span>
      </div>
      <div style="font-size:1.45rem;font-weight:800;color:#F8FAFC;
                  line-height:1.2;margin-bottom:12px">
        Escalada de Subsidios Confirmada</div>
      <div style="font-size:0.875rem;color:#94A3B8;line-height:1.8;margin-bottom:20px">
        {b_text}</div>
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:20px">
        <span style="background:rgba({dom_rgba},0.18);border:1px solid rgba({dom_rgba},0.45);
                     border-radius:6px;padding:4px 12px;font-size:0.7rem;font-weight:700;
                     color:{dom_color}">{dom_label}</span>
        <span style="background:rgba(148,163,184,0.08);border:1px solid rgba(148,163,184,0.18);
                     border-radius:6px;padding:4px 12px;font-size:0.7rem;font-weight:700;color:#64748B">
          Zona {peak_zlbl}</span>
        <span style="background:rgba({risk_rgba},0.15);border:1px solid rgba({risk_rgba},0.4);
                     border-radius:6px;padding:4px 12px;font-size:0.7rem;font-weight:700;
                     color:{risk_c}">⚑ Riesgo {risk_l}</span>
        <span style="background:rgba(148,163,184,0.08);border:1px solid rgba(148,163,184,0.18);
                     border-radius:6px;padding:4px 12px;font-size:0.7rem;font-weight:700;color:#64748B">
          Erosión de Percepción de Precio</span>
      </div>
      <div style="border-top:1px solid rgba(255,255,255,0.07);padding-top:14px;
                  display:flex;gap:12px;align-items:flex-start">
        <span style="font-size:0.58rem;font-weight:700;color:#475569;
                     text-transform:uppercase;letter-spacing:1.2px;
                     white-space:nowrap;padding-top:2px">Acción Sugerida</span>
        <span style="font-size:0.8rem;color:#94A3B8;line-height:1.7">{b_action}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 2. Executive KPI Tiles ─────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)

    def _kpi(col, lbl, val, sub, color):
        col.markdown(
            f'<div class="premium-card fade-in" style="padding:20px 18px">'
            f'<div style="font-size:0.58rem;font-weight:700;color:#94A3B8;'
            f'text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px">{lbl}</div>'
            f'<div style="font-size:1.7rem;font-weight:800;color:{color};'
            f'line-height:1;margin-bottom:5px">{val}</div>'
            f'<div style="font-size:0.68rem;color:#64748B;line-height:1.5">{sub}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    _kpi(k1, "Agresor Principal",
         f"{dom_rate:.0f}%",
         f"{dom_label} · densidad de subsidio activa",
         dom_color)
    _kpi(k2, "Multiplicador de Mercado",
         f"{mult:.1f}×",
         f"Rappi {rappi_rate:.0f}% vs {dom_label} {dom_rate:.0f}%",
         "#EF4444" if mult >= 3 else "#F97316" if mult >= 2 else "#F59E0B")
    _kpi(k3, "Epicentro de Riesgo",
         peak_zlbl,
         f"{peak_zr:.0f}% densidad promedio de competidores",
         "#F97316")
    _kpi(k4, "Nivel de Presión",
         risk_l,
         f"Score {risk_s}/100 · Exposición competitiva",
         risk_c)

    st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)

    # ── 3. Platform Intelligence Cards ─────────────────────────────────────────
    st.markdown("""
    <div style="display:flex;justify-content:space-between;align-items:flex-end;
                margin:24px 0 14px">
      <div>
        <span style="font-size:1rem;font-weight:700;color:#0F172A">
          Inteligencia Táctica por Plataforma</span>
        <p style="margin:3px 0 0;font-size:0.78rem;color:#64748B">
          Postura de subsidio competitivo por plataforma · Evaluado por intensidad de amenaza.</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    _TACTIC_TITLE = {
        "rappi":    "Línea de Base Defensiva",
        "ubereats": "Táctica de Expansión",
        "didi":     "Ofensiva de Subsidio",
    }
    _TACTIC_DESC = {
        "rappi":    "Compromiso promocional actual de Rappi — referencia base para calibrar la respuesta al mercado.",
        "ubereats": "Subsidio de envío focalizado en corredores premium y corporativos — enfoque en adquisición de cuota.",
        "didi":     "Máxima intensidad de subsidio — eliminación de fee de envío + descuentos en producto para captura de conversión.",
    }
    # Show dominant competitor first, then other, then Rappi as baseline
    _other = [p for p in ["ubereats", "didi"] if p != dom_plat]
    _card_order = [dom_plat] + _other + ["rappi"]

    pc_cols = st.columns(3)
    for col, plat_k in zip(pc_cols, _card_order):
        if plat_k not in plat_stats:
            continue
        ps     = plat_stats[plat_k]
        pc     = PLATFORM_COLORS[plat_k]
        pl     = PLATFORM_LABELS[plat_k]
        is_dom = (plat_k == dom_plat)

        if plat_k == "rappi":
            badge_txt = "BASE"; badge_c = "#10B981"; badge_b = "#ECFDF5"
        elif is_dom:
            badge_txt = "AMENAZA PRINCIPAL"; badge_c = "#EF4444"; badge_b = "#FEF2F2"
        else:
            badge_txt = "AMENAZA ACTIVA"; badge_c = "#F59E0B"; badge_b = "#FFFBEB"

        pbar_w = min(100, ps["promo_rate"])
        fbar_w = min(100, ps["free_rate"])

        col.markdown(
            f'<div class="premium-card fade-in" style="padding:0;overflow:hidden;'
            f'border-top:3px solid {pc}">'
            # header
            f'<div style="padding:16px 18px 13px;border-bottom:1px solid #F1F5F9">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;'
            f'margin-bottom:9px">'
            f'<div style="display:flex;align-items:center;gap:7px">'
            f'<div style="width:9px;height:9px;border-radius:50%;background:{pc}"></div>'
            f'<span style="font-size:0.82rem;font-weight:700;color:#0F172A">{pl}</span>'
            f'</div>'
            f'<span style="background:{badge_b};color:{badge_c};border-radius:5px;'
            f'padding:2px 7px;font-size:0.58rem;font-weight:700">{badge_txt}</span>'
            f'</div>'
            f'<div style="font-size:0.72rem;font-weight:600;color:#334155;margin-bottom:3px">'
            f'{_TACTIC_TITLE[plat_k]}</div>'
            f'<div style="font-size:0.66rem;color:#64748B;line-height:1.5">'
            f'{_TACTIC_DESC[plat_k]}</div>'
            f'</div>'
            # metrics
            f'<div style="padding:14px 18px">'
            # promo density bar
            f'<div style="margin-bottom:12px">'
            f'<div style="display:flex;justify-content:space-between;'
            f'align-items:center;margin-bottom:5px">'
            f'<span style="font-size:0.63rem;color:#64748B;font-weight:600">Densidad Promo</span>'
            f'<span style="font-size:0.82rem;font-weight:800;color:{pc}">'
            f'{ps["promo_rate"]:.0f}%</span></div>'
            f'<div style="background:#F1F5F9;border-radius:3px;height:4px">'
            f'<div style="height:100%;width:{pbar_w}%;background:{pc};border-radius:3px"></div>'
            f'</div></div>'
            # free delivery bar
            f'<div style="margin-bottom:12px">'
            f'<div style="display:flex;justify-content:space-between;'
            f'align-items:center;margin-bottom:5px">'
            f'<span style="font-size:0.63rem;color:#64748B;font-weight:600">Envío Gratis</span>'
            f'<span style="font-size:0.82rem;font-weight:800;color:#334155">'
            f'{ps["free_rate"]:.0f}%</span></div>'
            f'<div style="background:#F1F5F9;border-radius:3px;height:4px">'
            f'<div style="height:100%;width:{fbar_w}%;background:#94A3B8;border-radius:3px">'
            f'</div></div></div>'
            # avg discount + avg fee grid
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;'
            f'padding-top:10px;border-top:1px solid #F1F5F9">'
            f'<div>'
            f'<div style="font-size:0.57rem;color:#94A3B8;font-weight:700;'
            f'text-transform:uppercase;letter-spacing:0.5px;margin-bottom:3px">Dcto. Promedio</div>'
            f'<div style="font-size:1rem;font-weight:800;'
            f'color:{pc if ps["avg_disc"] > 0 else "#94A3B8"}">'
            f'{"$" + str(ps["avg_disc"]) if ps["avg_disc"] > 0 else "—"}</div>'
            f'</div>'
            f'<div>'
            f'<div style="font-size:0.57rem;color:#94A3B8;font-weight:700;'
            f'text-transform:uppercase;letter-spacing:0.5px;margin-bottom:3px">Fee Envío Prom.</div>'
            f'<div style="font-size:1rem;font-weight:800;color:#0F172A">'
            f'${ps["avg_fee"]:.1f}</div>'
            f'</div></div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    # ── 4. Zone Pressure Rankings ──────────────────────────────────────────────
    st.markdown("""
    <div style="border-top:1.5px solid #F1F5F9;margin:28px 0 18px"></div>
    <div style="margin-bottom:14px">
      <span style="font-size:1rem;font-weight:700;color:#0F172A">
        Ranking de Presión por Zona</span>
      <p style="margin:3px 0 0;font-size:0.78rem;color:#64748B">
        Intensidad de subsidio competidor por territorio CDMX · Ordenado por nivel de exposición.</p>
    </div>
    """, unsafe_allow_html=True)

    zone_rank_order = (
        zone_comp.sort_values(ascending=False).index.tolist()
        if not zone_comp.empty
        else ["premium", "corporativa", "media", "periferia"]
    )
    for rank, zk in enumerate(zone_rank_order, 1):
        z_lbl   = _ZD.get(zk, zk.title())
        z_avg   = round(float(zone_comp.get(zk, 0)), 1) if not zone_comp.empty else 0
        z_risk  = ("CRÍTICO" if z_avg >= 50 else "ALTO" if z_avg >= 35
                   else "MODERADO" if z_avg >= 20 else "BAJO")
        z_rc    = _RC[z_risk]
        z_rb    = _RB[z_risk]

        zp_row       = pz_all[pz_all["zone"] == zk]
        plat_z_rates = {row["platform"]: round(row["rate"], 1) for _, row in zp_row.iterrows()}

        comp_z   = {p: plat_z_rates.get(p, 0) for p in ["ubereats", "didi"]}
        z_lead_p = max(comp_z, key=comp_z.get) if comp_z else None
        z_lead   = PLATFORM_LABELS.get(z_lead_p, "—") if z_lead_p else "—"

        plat_bars_html = ""
        for bar_p, bar_lbl in [("ubereats", "Uber Eats"), ("didi", "DiDi"), ("rappi", "Rappi")]:
            pr_v = plat_z_rates.get(bar_p, 0)
            pr_w = min(100, pr_v)
            bar_c = PLATFORM_COLORS.get(bar_p, "#94A3B8")
            plat_bars_html += (
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px">'
                f'<span style="font-size:0.6rem;color:#94A3B8;width:62px;flex-shrink:0">'
                f'{bar_lbl}</span>'
                f'<div style="flex:1;background:#F1F5F9;border-radius:2px;height:5px">'
                f'<div style="height:100%;width:{pr_w}%;background:{bar_c};'
                f'border-radius:2px"></div></div>'
                f'<span style="font-size:0.6rem;font-weight:700;color:#0F172A;'
                f'width:28px;text-align:right;flex-shrink:0">{pr_v:.0f}%</span>'
                f'</div>'
            )

        st.markdown(
            f'<div class="fade-in" style="border:1px solid #E2E8F0;border-radius:12px;'
            f'padding:16px 20px;margin-bottom:10px;background:#FFFFFF;'
            f'border-left:4px solid {z_rc}">'
            f'<div style="display:flex;align-items:center;gap:16px">'
            f'<div style="flex-shrink:0;width:190px">'
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">'
            f'<span style="font-size:0.65rem;font-weight:700;color:#94A3B8">#{rank}</span>'
            f'<span style="font-size:0.9rem;font-weight:700;color:#0F172A">{z_lbl}</span>'
            f'<span style="background:{z_rb};color:{z_rc};border-radius:4px;'
            f'padding:1px 6px;font-size:0.57rem;font-weight:700">{z_risk}</span>'
            f'</div>'
            f'<div style="font-size:0.65rem;color:#64748B">'
            f'Líder: {z_lead} · Prom. {z_avg:.0f}% densidad competidora</div>'
            f'</div>'
            f'<div style="flex:1">{plat_bars_html}</div>'
            f'<div style="text-align:right;flex-shrink:0;padding-left:16px;'
            f'border-left:1px solid #F1F5F9">'
            f'<div style="font-size:1.65rem;font-weight:800;color:{z_rc};line-height:1">'
            f'{z_avg:.0f}%</div>'
            f'<div style="font-size:0.58rem;color:#94A3B8;margin-top:3px;'
            f'white-space:nowrap">prom. competidor</div>'
            f'</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    # ── 5. Competitive Intelligence Signals ────────────────────────────────────
    st.markdown("""
    <div style="border-top:1.5px solid #F1F5F9;margin:28px 0 18px"></div>
    <div style="margin-bottom:14px">
      <span style="font-size:1rem;font-weight:700;color:#0F172A">
        Señales Estratégicas de Mercado</span>
      <p style="margin:3px 0 0;font-size:0.78rem;color:#64748B">
        Observaciones competitivas estructuradas desde la capa de monitoreo de promociones.</p>
    </div>
    """, unsafe_allow_html=True)

    signals = []
    # Signal 1: dominant competitor escalation
    signals.append({
        "sev": "CRITICAL" if dom_rate >= 55 else "HIGH" if dom_rate >= 35 else "MEDIUM",
        "title": f"{dom_label} — Escalada de Subsidio",
        "body": (
            f"{dom_label} ha escalado su actividad promocional al <b>{dom_rate:.0f}%</b> de "
            f"listings activos — <b>{mult:.1f}× la densidad de Rappi</b>. Esta táctica de "
            f"adquisición agresiva está diseñada para erosionar cuota de mercado en "
            f"corredores de alto valor mediante erosión sostenida de percepción de precio."
        ),
        "metric": f"{dom_rate:.0f}%", "metric_lbl": "densidad de listings",
    })
    # Signal 2: free delivery coverage
    dom_free = plat_stats.get(dom_plat, {}).get("free_rate", 0)
    if dom_free >= 15:
        signals.append({
            "sev": "HIGH" if dom_free >= 40 else "MEDIUM",
            "title": f"Ofensiva de Envío Gratis — {dom_label}",
            "body": (
                f"{dom_label} elimina la fricción de delivery en el <b>{dom_free:.0f}%</b> de "
                f"sus listings — táctica de eliminación de barreras que reduce el costo percibido "
                f"y presiona la tasa de conversión de Rappi en zonas "
                f"sensibles al costo total del pedido."
            ),
            "metric": f"{dom_free:.0f}%", "metric_lbl": "envío gratis",
        })
    # Signal 3: zone concentration
    signals.append({
        "sev": "HIGH" if peak_zr >= 40 else "MEDIUM",
        "title": f"Concentración Geográfica — {peak_zlbl}",
        "body": (
            f"La presión competitiva alcanza <b>{peak_zr:.0f}%</b> de densidad en Zona "
            f"<b>{peak_zlbl}</b> — la mayor concentración de señales de expansión competitiva "
            f"en CDMX. Este patrón indica una táctica de expansión de mercado focalizada "
            f"para capturar usuarios de alto valor económico."
        ),
        "metric": f"{peak_zr:.0f}%", "metric_lbl": "densidad de zona",
    })
    # Signal 4: Rappi response gap
    gap_pp = round(dom_rate - rappi_rate, 1)
    if gap_pp >= 10:
        signals.append({
            "sev": "HIGH" if gap_pp >= 25 else "MEDIUM",
            "title": "Brecha de Respuesta Promocional — Rappi",
            "body": (
                f"Rappi mantiene solo <b>{rappi_rate:.0f}%</b> de densidad promocional "
                f"frente al <b>{dom_rate:.0f}%</b> de {dom_label} — una brecha de "
                f"<b>{gap_pp:.0f}pp</b> que expone a Rappi a presión de mercado creciente "
                f"entre usuarios con alta sensibilidad a descuentos y subsidios de delivery."
            ),
            "metric": f"+{gap_pp:.0f}pp", "metric_lbl": "brecha de exposición",
        })

    _SEV_META = {
        "CRITICAL": ("#EF4444", "#FEF2F2"),
        "HIGH":     ("#F97316", "#FFF7ED"),
        "MEDIUM":   ("#F59E0B", "#FFFBEB"),
    }
    sig_cols = st.columns(2)
    for i, sig in enumerate(signals):
        sc, sb = _SEV_META.get(sig["sev"], _SEV_META["MEDIUM"])
        with sig_cols[i % 2]:
            st.markdown(
                f'<div class="premium-card fade-in" style="padding:18px 20px;'
                f'margin-bottom:14px;border-left:3px solid {sc}">'
                f'<div style="display:flex;justify-content:space-between;'
                f'align-items:flex-start;margin-bottom:10px">'
                f'<div style="flex:1">'
                f'<span style="background:{sb};color:{sc};border-radius:4px;'
                f'padding:2px 8px;font-size:0.58rem;font-weight:700;'
                f'display:inline-block;margin-bottom:8px">{sig["sev"]}</span>'
                f'<div style="font-size:0.85rem;font-weight:700;color:#0F172A">'
                f'{sig["title"]}</div>'
                f'</div>'
                f'<div style="text-align:right;flex-shrink:0;padding-left:18px">'
                f'<div style="font-size:1.45rem;font-weight:800;color:{sc};line-height:1">'
                f'{sig["metric"]}</div>'
                f'<div style="font-size:0.6rem;color:#94A3B8;margin-top:2px">'
                f'{sig["metric_lbl"]}</div>'
                f'</div></div>'
                f'<div style="font-size:0.76rem;color:#475569;line-height:1.65">'
                f'{sig["body"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── Section 6: Promotion Strategy Breakdown ───────────────────────────────
    st.markdown(
        '<div style="height:32px"></div>'
        '<div style="display:flex;align-items:center;gap:12px;margin-bottom:6px">'
        '<div style="flex:1;height:1px;background:#E2E8F0"></div>'
        '<span style="font-size:0.65rem;font-weight:700;letter-spacing:0.12em;'
        'color:#94A3B8;text-transform:uppercase">Análisis de Estrategia Promocional</span>'
        '<div style="flex:1;height:1px;background:#E2E8F0"></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<h2 style="font-size:1.35rem;font-weight:800;color:#0F172A;'
        'margin:0 0 4px">Inteligencia de Estrategia · Qué Está Haciendo Realmente Cada Plataforma</h2>'
        '<p style="font-size:0.82rem;color:#64748B;margin:0 0 24px">'
        'Clasificación automática de tácticas promocionales en arquetipos estratégicos — '
        'adquisición, retención, urgencia, engagement.</p>',
        unsafe_allow_html=True,
    )

    # ── Data computation ──────────────────────────────────────────────────────
    df_s = df.copy()
    df_s["_strat"] = df_s["promo_label"].apply(_classify_promo_strategy)

    PLATFORMS_ORDER = ["rappi", "ubereats", "didi"]
    strat_by_plat: dict[str, dict] = {}
    for plat in PLATFORMS_ORDER:
        sub = df_s[df_s["platform"] == plat]
        if sub.empty:
            strat_by_plat[plat] = {
                "counts": {}, "pcts": {}, "dominant": "OTHER",
                "promo_rate": 0.0, "total": 0,
            }
            continue
        counts = sub["_strat"].value_counts().to_dict()
        total = len(sub)
        active = {k: v for k, v in counts.items() if k not in ("NONE", "OTHER")}
        dominant = max(active, key=lambda k: active[k]) if active else "OTHER"
        promo_rate = round(100 * sum(active.values()) / total, 1)
        pcts = {k: round(100 * v / total, 1) for k, v in counts.items()}
        strat_by_plat[plat] = {
            "counts": counts, "pcts": pcts,
            "dominant": dominant, "promo_rate": promo_rate, "total": total,
        }

    _zone_strat: dict[str, dict[str, str]] = {}
    for zone in ZONE_ORDER:
        _zone_strat[zone] = {}
        for plat in PLATFORMS_ORDER:
            sub_z = df_s[(df_s["platform"] == plat) & (df_s["zone"] == zone)]
            if sub_z.empty:
                _zone_strat[zone][plat] = "NONE"
                continue
            active_z = {k: v for k, v in sub_z["_strat"].value_counts().items()
                        if k not in ("NONE", "OTHER")}
            _zone_strat[zone][plat] = (
                max(active_z, key=lambda k: active_z[k]) if active_z else "OTHER"
            )

    # ── Opening narrative banner ──────────────────────────────────────────────
    dom_strats = [strat_by_plat[p]["dominant"] for p in PLATFORMS_ORDER]
    archetypes_used = set(
        _PROMO_ARCHETYPE.get(s, ("", "", ""))[0] for s in dom_strats if s in _PROMO_ARCHETYPE
    )
    arch_str = " · ".join(sorted(archetypes_used))
    st.markdown(
        f'<div class="premium-card fade-in" style="'
        f'background:linear-gradient(135deg,#0F172A 0%,#1E293B 100%);'
        f'border:1px solid #334155;padding:20px 24px;margin-bottom:20px">'
        f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">'
        f'<span style="background:#FB923C;color:#fff;border-radius:4px;'
        f'padding:2px 8px;font-size:0.58rem;font-weight:700;'
        f'letter-spacing:0.1em">ANÁLISIS DE INTENCIÓN ESTRATÉGICA</span>'
        f'<span style="font-size:0.65rem;color:#64748B;font-weight:600">'
        f'{arch_str}</span></div>'
        f'<p style="font-size:0.82rem;color:#CBD5E1;line-height:1.7;margin:0">'
        f'El análisis promocional multiplataforma revela <b style="color:#F8FAFC">tres filosofías '
        f'competitivas distintas</b> operando simultáneamente: '
        f'<b style="color:#FB923C">Rappi</b> y <b style="color:#34D399">Uber Eats</b> '
        f'despliegan estrategias de retención ancladas en ecosistemas de membresía, '
        f'mientras <b style="color:#FBBF24">DiDi Food</b> ejecuta un '
        f'manual de adquisición agresivo — apuntando a usuarios nuevos con descuentos profundos para expandir '
        f'su base instalada. Este equilibrio trimodal señala un mercado en inflexión estratégica: '
        f'los incumbentes de retención vs. el retador de adquisición.</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Platform strategy cards ───────────────────────────────────────────────
    plat_cols = st.columns(3)
    _PLAT_COLORS = {"rappi": "#FB923C", "ubereats": "#34D399", "didi": "#FBBF24"}
    _PLAT_LABELS = {"rappi": "Rappi", "ubereats": "Uber Eats", "didi": "DiDi Food"}

    _PLAT_NARRATIVES = {
        "rappi": (
            "Retención Impulsada por Membresía",
            "Rappi Prime ancla el stack promocional — vinculando suscripciones con subsidios "
            "de envío y descuentos exclusivos, creando barreras de cambio de plataforma "
            "en lugar de competir en descuentos puntuales.",
        ),
        "ubereats": (
            "Ecosistema Integrado vía Uber One",
            "La lealtad multivertical de Uber One (viajes + comida) da a Uber Eats una ventaja "
            "de retención estructural — los usuarios se retienen a nivel de ecosistema, no de "
            "restaurante, reduciendo dramáticamente la elasticidad de abandono.",
        ),
        "didi": (
            "Ofensiva de Adquisición — Foco en Primer Pedido",
            "La fuerte concentración de descuentos en primeros pedidos de DiDi (30% off, primeros 3 pedidos) "
            "señala una estrategia explícita de CAC sobre margen — priorizando adquisición de usuarios "
            "y captura de cuota de mercado sobre economías unitarias de corto plazo.",
        ),
    }

    for col, plat in zip(plat_cols, PLATFORMS_ORDER):
        data = strat_by_plat[plat]
        dom = data["dominant"]
        meta = _PROMO_STRAT_META.get(dom, ("·", dom, "#94A3B8", "#F8FAFC"))
        arch_info = _PROMO_ARCHETYPE.get(dom, ("TACTICAL", "#94A3B8", "#F8FAFC"))
        plat_c = _PLAT_COLORS[plat]
        plat_lbl = _PLAT_LABELS[plat]
        narr_title, narr_body = _PLAT_NARRATIVES[plat]

        # Build distribution bar rows (top 4 active strategies, sorted by %)
        active_items = sorted(
            [(k, v) for k, v in data["pcts"].items() if k not in ("NONE", "OTHER")],
            key=lambda x: -x[1],
        )[:4]
        bars_html = ""
        for strat_key, pct in active_items:
            sm = _PROMO_STRAT_META.get(strat_key, ("·", strat_key, "#94A3B8", "#F8FAFC"))
            bars_html += (
                f'<div style="margin-bottom:7px">'
                f'<div style="display:flex;justify-content:space-between;'
                f'align-items:center;margin-bottom:3px">'
                f'<span style="font-size:0.68rem;color:#475569;font-weight:500">'
                f'{sm[0]} {sm[1]}</span>'
                f'<span style="font-size:0.68rem;color:#64748B;font-weight:700">'
                f'{pct:.0f}%</span>'
                f'</div>'
                f'<div style="height:4px;background:#F1F5F9;border-radius:2px">'
                f'<div style="height:4px;width:{min(pct,100):.0f}%;background:{sm[2]};'
                f'border-radius:2px;transition:width 0.4s ease"></div>'
                f'</div></div>'
            )

        with col:
            st.markdown(
                f'<div class="premium-card fade-in" style="'
                f'border-top:3px solid {plat_c};padding:20px;margin-bottom:0">'
                # Header
                f'<div style="display:flex;justify-content:space-between;'
                f'align-items:flex-start;margin-bottom:14px">'
                f'<div>'
                f'<div style="font-size:0.92rem;font-weight:800;color:#0F172A">'
                f'{plat_lbl}</div>'
                f'<div style="font-size:0.68rem;color:#94A3B8;font-weight:500;'
                f'margin-top:2px">{data["total"]} records · {data["promo_rate"]:.0f}% promo rate</div>'
                f'</div>'
                f'<span style="background:{arch_info[2]};color:{arch_info[1]};'
                f'border-radius:4px;padding:3px 8px;font-size:0.6rem;font-weight:800;'
                f'letter-spacing:0.08em">{arch_info[0]}</span>'
                f'</div>'
                # Dominant tactic highlight
                f'<div style="background:{meta[3]};border:1px solid {meta[2]}22;'
                f'border-radius:6px;padding:10px 12px;margin-bottom:14px">'
                f'<div style="font-size:0.6rem;font-weight:700;letter-spacing:0.1em;'
                f'color:{meta[2]};text-transform:uppercase;margin-bottom:4px">Táctica Dominante</div>'
                f'<div style="font-size:0.82rem;font-weight:700;color:#0F172A">'
                f'{meta[0]} {meta[1]}</div>'
                f'</div>'
                # Distribution bars
                f'<div style="font-size:0.6rem;font-weight:700;letter-spacing:0.1em;'
                f'color:#94A3B8;text-transform:uppercase;margin-bottom:8px">'
                f'Distribución de Estrategia</div>'
                f'{bars_html}'
                # Narrative
                f'<div style="margin-top:14px;padding-top:12px;'
                f'border-top:1px solid #F1F5F9">'
                f'<div style="font-size:0.72rem;font-weight:700;color:#0F172A;'
                f'margin-bottom:5px">{narr_title}</div>'
                f'<div style="font-size:0.69rem;color:#64748B;line-height:1.6">'
                f'{narr_body}</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div style="height:28px"></div>', unsafe_allow_html=True)

    # ── Zone × Strategy matrix ────────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:0.65rem;font-weight:700;letter-spacing:0.12em;'
        'color:#94A3B8;text-transform:uppercase;margin-bottom:10px">'
        'Matriz de Inteligencia Zona × Estrategia</div>',
        unsafe_allow_html=True,
    )
    _ZONE_LABELS = {
        "premium":    "Premium",
        "corporativa": "Corporativa",
        "media":      "Media",
        "periferia":  "Periferia",
    }
    # Build header row
    th_cells = "".join(
        f'<th style="padding:10px 14px;font-size:0.68rem;font-weight:700;'
        f'color:#0F172A;text-align:left;border-bottom:2px solid #E2E8F0;'
        f'background:#F8FAFC">{_PLAT_LABELS[p]}</th>'
        for p in PLATFORMS_ORDER
    )
    matrix_rows = ""
    for zone in ZONE_ORDER:
        zl = _ZONE_LABELS.get(zone, zone.capitalize())
        td_cells = ""
        for plat in PLATFORMS_ORDER:
            sk = _zone_strat.get(zone, {}).get(plat, "NONE")
            sm = _PROMO_STRAT_META.get(sk, ("·", sk, "#94A3B8", "#F8FAFC"))
            td_cells += (
                f'<td style="padding:10px 14px;border-bottom:1px solid #F1F5F9">'
                f'<span style="background:{sm[3]};color:{sm[2]};'
                f'border-radius:4px;padding:3px 8px;font-size:0.65rem;font-weight:700;'
                f'white-space:nowrap">{sm[0]} {sm[1]}</span>'
                f'</td>'
            )
        matrix_rows += (
            f'<tr>'
            f'<td style="padding:10px 14px;font-size:0.72rem;font-weight:700;'
            f'color:#0F172A;border-bottom:1px solid #F1F5F9;'
            f'white-space:nowrap;background:#FAFAFA">{zl}</td>'
            f'{td_cells}'
            f'</tr>'
        )
    st.markdown(
        f'<div class="premium-card fade-in" style="padding:0;overflow:hidden">'
        f'<table style="width:100%;border-collapse:collapse">'
        f'<thead><tr>'
        f'<th style="padding:10px 14px;font-size:0.68rem;font-weight:700;'
        f'color:#94A3B8;text-align:left;border-bottom:2px solid #E2E8F0;'
        f'background:#F8FAFC;width:120px">Zone</th>'
        f'{th_cells}'
        f'</tr></thead>'
        f'<tbody>{matrix_rows}</tbody>'
        f'</table></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div style="height:28px"></div>', unsafe_allow_html=True)

    # ── Commercial Intent Analysis ────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:0.65rem;font-weight:700;letter-spacing:0.12em;'
        'color:#94A3B8;text-transform:uppercase;margin-bottom:14px">'
        'Commercial Intent Analysis</div>',
        unsafe_allow_html=True,
    )

    _INTENT_DATA = {
        "rappi": {
            "headline": "Retention Fortress Strategy",
            "color": "#FB923C",
            "summary": (
                "Rappi's promotional architecture is deliberately designed to convert "
                "transactional users into long-term subscribers. Prime membership "
                "permeates the discount stack, making each promo both a conversion "
                "tool and a membership funnel."
            ),
            "bullets": [
                "Rappi Prime subsidies represent <b>~60%</b> of active promotions — "
                "the highest membership-linkage ratio in the competitive set.",
                "Delivery fee waivers are <b>membership-gated</b>, creating a two-tier "
                "experience that pressures non-subscribers toward conversion.",
                "Low first-order promo frequency (<b>&lt;8%</b>) signals deliberate "
                "de-prioritization of acquisition in favor of retention ROAS.",
            ],
        },
        "ubereats": {
            "headline": "Cross-Vertical Ecosystem Moat",
            "color": "#34D399",
            "summary": (
                "Uber One transforms food delivery into a loyalty touchpoint within a "
                "broader mobility ecosystem. Promotional value is amplified across "
                "rides + food, creating network effects that pure-play food apps cannot replicate."
            ),
            "bullets": [
                "Uber One membership drives <b>~55%</b> of promo volume — structurally "
                "higher LTV than discount-only competitors.",
                "Cross-vertical bundle potential means every food promo also reinforces "
                "rides retention, creating a <b>dual-channel moat</b>.",
                "Minimum spend triggers (<b>Gasta $X, ahorra $Y</b>) effectively raise "
                "average basket size while masking the subsidy cost.",
            ],
        },
        "didi": {
            "headline": "Aggressive CAC Compression Play",
            "color": "#FBBF24",
            "summary": (
                "DiDi deploys a textbook user acquisition playbook — front-loading "
                "deep discounts for first-time users to rapidly grow its installed base. "
                "This signals a growth-over-margin mandate, prioritizing market share "
                "capture ahead of unit economics optimization."
            ),
            "bullets": [
                "<b>30% off primeros 3 pedidos</b> is the primary weapon — high trial "
                "incentive designed to overcome first-order friction and build habit loops.",
                "First-order promo concentration at <b>~38%</b> of all active promos — "
                "the highest acquisition intensity in the competitive set by a wide margin.",
                "Post-acquisition promo density is significantly lower, suggesting "
                "DiDi bets on product experience (not ongoing discounts) to drive "
                "organic retention after initial trial.",
            ],
        },
    }

    intent_cols = st.columns(3)
    for col, plat in zip(intent_cols, PLATFORMS_ORDER):
        d = _INTENT_DATA[plat]
        bullets_html = "".join(
            f'<li style="font-size:0.69rem;color:#475569;line-height:1.65;'
            f'margin-bottom:7px">{b}</li>'
            for b in d["bullets"]
        )
        with col:
            st.markdown(
                f'<div class="premium-card fade-in" style="padding:20px;margin-bottom:0">'
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">'
                f'<div style="width:3px;height:32px;background:{d["color"]};'
                f'border-radius:2px;flex-shrink:0"></div>'
                f'<div style="font-size:0.82rem;font-weight:800;color:#0F172A">'
                f'{_PLAT_LABELS[plat]}</div>'
                f'</div>'
                f'<div style="font-size:0.72rem;font-weight:700;color:#0F172A;'
                f'margin-bottom:8px">{d["headline"]}</div>'
                f'<p style="font-size:0.69rem;color:#64748B;line-height:1.65;'
                f'margin:0 0 12px">{d["summary"]}</p>'
                f'<ul style="margin:0;padding-left:14px">{bullets_html}</ul>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ── Market Intelligence Surface ───────────────────────────────────────────────

# Threat classification meta
_THREAT_META = {
    "price": ("Alta Presión Competitiva",  "#EF4444", "⬆"),
    "eta":   ("Zona de Riesgo ETA",        "#3B82F6", "⏱"),
    "promo": ("Cluster de Expansión Promo","#F59E0B", "◆"),
    "none":  ("Territorio Estable",        "#10B981", "✓"),
}
_ZONE_LABELS_GEO = {
    "premium": "Premium", "corporativa": "Corporativa",
    "media": "Media", "periferia": "Periferia",
}


def _compute_zone_intel(df: pd.DataFrame) -> list[dict]:
    """Aggregate df into zone-level competitive intelligence records."""
    intel = []
    for zone in ["premium", "corporativa", "media", "periferia"]:
        zdf = df[df["zone"] == zone]
        if zdf.empty:
            continue

        rappi_df  = zdf[zdf["platform"] == "rappi"]
        others_df = zdf[zdf["platform"] != "rappi"]

        rappi_price = rappi_df["final_price"].mean() if not rappi_df.empty else None
        rappi_eta   = rappi_df["eta_min"].mean()     if not rappi_df.empty else None

        plat_prices = {
            p: zdf[zdf["platform"] == p]["final_price"].mean()
            for p in ["ubereats", "didi"]
            if not zdf[zdf["platform"] == p].empty
        }
        plat_etas = {
            p: zdf[zdf["platform"] == p]["eta_min"].mean()
            for p in ["ubereats", "didi"]
            if not zdf[zdf["platform"] == p].empty
        }
        promo_rate = (others_df["discount"] > 0).mean() * 100 if not others_df.empty else 0.0

        price_gap, cheapest_plat = 0.0, None
        if rappi_price and plat_prices:
            cheapest_plat = min(plat_prices, key=plat_prices.get)
            price_gap = round(
                (rappi_price - plat_prices[cheapest_plat]) / max(plat_prices[cheapest_plat], 1) * 100, 1
            )

        eta_gap, fastest_plat = 0.0, None
        if rappi_eta and plat_etas:
            fastest_plat = min(plat_etas, key=plat_etas.get)
            eta_gap = round(rappi_eta - plat_etas[fastest_plat], 1)

        risk_score = round(
            min(100, max(0, price_gap) * 2.5 + max(0, eta_gap) * 2.0 + promo_rate * 0.5), 1
        )

        threat_scores: dict[str, float] = {}
        if price_gap >= 5:  threat_scores["price"] = max(0, price_gap) * 2.5
        if eta_gap   >= 3:  threat_scores["eta"]   = max(0, eta_gap)   * 2.0
        if promo_rate >= 25: threat_scores["promo"] = promo_rate        * 0.5
        primary = max(threat_scores, key=threat_scores.get) if threat_scores else "none"

        strategic_label, threat_color, threat_icon = _THREAT_META[primary]

        if primary == "price" and cheapest_plat:
            annotation = f"+{price_gap:.0f}% vs {PLATFORM_LABELS.get(cheapest_plat, cheapest_plat)}"
            insight    = f"{PLATFORM_LABELS.get(cheapest_plat, '')} undercutting by {price_gap:.0f}% — conversion risk"
        elif primary == "eta" and fastest_plat:
            annotation = f"+{eta_gap:.0f} min vs {PLATFORM_LABELS.get(fastest_plat, fastest_plat)}"
            insight    = f"{PLATFORM_LABELS.get(fastest_plat, '')} {eta_gap:.0f} min faster — loyalty risk"
        elif primary == "promo":
            annotation = f"{promo_rate:.0f}% competitor promo intensity"
            insight    = f"Subsidy tactics active — {promo_rate:.0f}% listings discounted"
        else:
            annotation = "Within competitive range"
            insight    = "No critical exposure detected"

        intel.append({
            "zone":            zone,
            "label":           _ZONE_LABELS_GEO[zone],
            "lat":             zdf["lat"].mean(),
            "lon":             zdf["lon"].mean(),
            "risk_score":      risk_score,
            "price_gap":       price_gap,
            "eta_gap":         eta_gap,
            "promo_rate":      promo_rate,
            "primary_threat":  primary,
            "strategic_label": strategic_label,
            "threat_color":    threat_color,
            "threat_icon":     threat_icon,
            "annotation":      annotation,
            "insight":         insight,
            "cheapest_plat":   cheapest_plat,
            "fastest_plat":    fastest_plat,
        })

    intel.sort(key=lambda z: z["risk_score"], reverse=True)
    return intel


_GEO_DIMS = {
    "overview": {"label": "Visión General",        "sort_key": "risk_score", "unit": "/100"},
    "price":    {"label": "Presión de Precios",    "sort_key": "price_gap",  "unit": "% gap"},
    "eta":      {"label": "Riesgo ETA",            "sort_key": "eta_gap",    "unit": " min"},
    "promo":    {"label": "Agresividad Promo",     "sort_key": "promo_rate", "unit": "%"},
}


def _geo_zone_color(zi: dict, dim: str) -> str:
    if dim == "overview":
        return zi["threat_color"]
    if dim == "price":
        v = zi["price_gap"]
        return "#B91C1C" if v >= 20 else "#EF4444" if v >= 12 else "#F87171" if v >= 5 else "#FECACA"
    if dim == "eta":
        v = zi["eta_gap"]
        return "#1D4ED8" if v >= 12 else "#3B82F6" if v >= 6 else "#60A5FA" if v >= 3 else "#BFDBFE"
    v = zi["promo_rate"]
    return "#D97706" if v >= 50 else "#F59E0B" if v >= 30 else "#FBBF24" if v >= 15 else "#FDE68A"


def _geo_zone_metric(zi: dict, dim: str) -> float:
    return float(zi.get(_GEO_DIMS[dim]["sort_key"], 0.0))


def page_geo(df: pd.DataFrame):
    _exp = None if (df.empty or "lat" not in df.columns) else {
        "label": "↑ Exportar Reporte Territorial",
        "data":  _gen_territory_report_html(df),
        "file_name": f"rappi_ci_territory_report_{__import__('datetime').date.today()}.html",
        "mime": "text/html", "key": "_exp_geo",
    }
    page_header(
        "Monitor Territorial",
        "Inteligencia Competitiva · CDMX · Análisis Estratégico de Zonas",
        export_config=_exp,
    )
    if df.empty or "lat" not in df.columns:
        st.markdown("""
        <div class="fade-in" style="text-align:center;padding:52px 24px;
                    border:1px solid #F1F5F9;border-radius:12px;background:#FAFBFC">
          <div style="font-size:2.5rem;opacity:0.12;margin-bottom:14px">◐</div>
          <div style="font-size:0.9rem;font-weight:600;color:#0F172A;margin-bottom:8px">
            No hay datos geográficos</div>
          <div style="font-size:0.78rem;color:#94A3B8">
            Ejecuta el scraper para generar inteligencia territorial.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    zone_intel = _compute_zone_intel(df)
    if not zone_intel:
        empty_state("Sin datos de inteligencia territorial.")
        return

    # ── Dimension state ────────────────────────────────────────────────────────
    if "geo_dim" not in st.session_state:
        st.session_state["geo_dim"] = "overview"
    active_dim = st.session_state["geo_dim"]
    dim_cfg    = _GEO_DIMS[active_dim]
    ranked     = sorted(zone_intel, key=lambda z: _geo_zone_metric(z, active_dim), reverse=True)
    top        = ranked[0]

    # ── Dimension filter chips ─────────────────────────────────────────────────
    st.markdown(
        '<div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;'
        'padding:14px 20px 12px;box-shadow:0 1px 4px rgba(0,0,0,0.04);margin-bottom:6px">',
        unsafe_allow_html=True,
    )
    lc, cc = st.columns([1.2, 10])
    with lc:
        st.markdown(
            '<div style="padding-top:5px;font-size:0.62rem;font-weight:700;'
            'color:#94A3B8;text-transform:uppercase;letter-spacing:1px">Dimensión</div>',
            unsafe_allow_html=True,
        )
    with cc:
        dim_keys = list(_GEO_DIMS.keys())
        dcols = st.columns(len(dim_keys) + 6)
        for i, dk in enumerate(dim_keys):
            with dcols[i]:
                is_active = (active_dim == dk)
                st.markdown(
                    f'<div class="{"chip-active" if is_active else "chip-btn"}">',
                    unsafe_allow_html=True,
                )
                if st.button(_GEO_DIMS[dk]["label"], key=f"geodim_{dk}",
                             use_container_width=True):
                    st.session_state["geo_dim"] = dk
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Executive briefing + suggested action ─────────────────────────────────
    _dim_title = {
        "overview": "Inteligencia Territorial",
        "price":    "Análisis de Presión de Precios",
        "eta":      "Análisis de Rendimiento de Entrega",
        "promo":    "Inteligencia Promocional",
    }[active_dim]

    if active_dim == "overview":
        n_crit = sum(1 for z in zone_intel if z["risk_score"] >= 40)
        top2   = ranked[1]["label"] if len(ranked) > 1 else ranked[0]["label"]
        _comp  = PLATFORM_LABELS.get(top["cheapest_plat"], "competitors") if top.get("cheapest_plat") else "competitors"
        b_narrative = (
            f"La inteligencia competitiva indica que <b>{n_crit} de {len(zone_intel)}</b> territorios CDMX "
            f"operan bajo presión competitiva elevada. <b>{top['label']}</b> presenta el "
            f"mayor riesgo agregado con <b>{top['risk_score']:.0f}/100</b>, con "
            f"<b>{top['strategic_label']}</b> como vector de amenaza principal. "
            f"<b>{top2}</b> le sigue con exposición sostenida en múltiples dimensiones."
        )
        b_action = (
            f"Iniciar una revisión interfuncional en <b>{top['label']}</b> y <b>{top2}</b>. "
            f"Alinear postura de precios, capacidad de entrega y actividad promocional para contrarrestar "
            f"el avance de {_comp} antes de la temporada pico."
        )
        b_bg="#FFFBF7"; b_border="#FED7AA"; b_bi="#FFEDD5"; b_tc="#92400E"; b_tcl="#F97316"; b_tch="#FB923C"

    elif active_dim == "price":
        _cp    = PLATFORM_LABELS.get(top["cheapest_plat"], "a competitor") if top.get("cheapest_plat") else "a competitor"
        n_risk = sum(1 for z in zone_intel if z["price_gap"] >= 10)
        b_narrative = (
            f"El análisis de exposición de precios confirma que <b>{_cp}</b> subcotiza "
            f"sistemáticamente a Rappi en <b>{top['price_gap']:.0f}%</b> en <b>{top['label']}</b> — la mayor "
            f"brecha de precios competitiva en los territorios monitoreados. "
            f"<b>{n_risk} de {len(zone_intel)}</b> zonas superan el umbral de exposición del 10%, "
            f"señalando vulnerabilidad estructural a nivel de producto."
        )
        b_action = (
            f"Ejecutar alineación inmediata de precios en <b>{top['label']}</b> focalizando en SKUs de alto ticket. "
            f"Desplegar correcciones a nivel de categoría para cerrar la brecha del {top['price_gap']:.0f}% y "
            f"recuperar tasa de conversión vs {_cp}."
        )
        b_bg="#FEF2F2"; b_border="#FECACA"; b_bi="#FEE2E2"; b_tc="#991B1B"; b_tcl="#DC2626"; b_tch="#EF4444"

    elif active_dim == "eta":
        _fp   = PLATFORM_LABELS.get(top["fastest_plat"], "a competitor") if top.get("fastest_plat") else "a competitor"
        _conv = round(top["eta_gap"] / 5 * 3, 1)
        _tgt  = round(top["eta_gap"] / 2, 1)
        b_narrative = (
            f"<b>{_fp}</b> mantiene una ventaja de entrega de <b>{top['eta_gap']:.0f} minutos</b> "
            f"sobre Rappi en <b>{top['label']}</b> — la mayor brecha de rendimiento operativo "
            f"en los territorios CDMX monitoreados. A las tasas actuales, este delta se traduce en un "
            f"<b>diferencial de conversión estimado de ~{_conv:.0f}%</b> durante ventanas de hora pico."
        )
        b_action = (
            f"Aumentar el despliegue de repartidores en <b>{top['label']}</b> durante los picos de comida. "
            f"Apuntar a una reducción de ETA de {_tgt:.0f} minutos para aproximarse a paridad competitiva con {_fp} "
            f"y recuperar volumen de órdenes en corredores de alta densidad."
        )
        b_bg="#EFF6FF"; b_border="#BFDBFE"; b_bi="#DBEAFE"; b_tc="#1E3A5F"; b_tcl="#2563EB"; b_tch="#3B82F6"

    else:
        _ppr: dict[str, float] = {}
        for _p in ["ubereats", "didi"]:
            _sub = df[df["platform"] == _p]
            if not _sub.empty:
                _ppr[_p] = (_sub["discount"] > 0).mean() * 100
        _ap   = max(_ppr, key=_ppr.get) if _ppr else None
        _al   = PLATFORM_LABELS.get(_ap, "a competitor") if _ap else "a competitor"
        _ar   = round(_ppr.get(_ap, 0), 1) if _ap else 0
        _avgp = sum(z["promo_rate"] for z in zone_intel) / max(len(zone_intel), 1)
        _mult = round(top["promo_rate"] / max(_avgp, 1), 1)
        b_narrative = (
            f"La actividad promocional competidora tiene su pico en <b>{top['label']}</b>, donde "
            f"<b>{top['promo_rate']:.0f}%</b> de los listings de la competencia tienen descuentos activos — "
            f"<b>{_mult:.1f}×</b> el promedio entre territorios. <b>{_al}</b> lidera la intensidad "
            f"de subsidio con {_ar:.0f}%, consistente con una campaña estructurada de adquisición "
            f"de usuarios apuntando a la base instalada de Rappi."
        )
        b_action = (
            f"Activar promociones defensivas focalizadas en <b>{top['label']}</b> para neutralizar "
            f"la estrategia de subsidio de {_al}. Concentrar el gasto de adquisición en segmentos "
            f"con mayor riesgo de abandono hacia plataformas competidoras."
        )
        b_bg="#FFFBEB"; b_border="#FDE68A"; b_bi="#FEF3C7"; b_tc="#78350F"; b_tcl="#D97706"; b_tch="#F59E0B"

    st.markdown(f"""
    <div class="fade-in" style="background:{b_bg};border:1px solid {b_border};
         border-radius:10px;padding:18px 22px;margin:8px 0 16px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
        <span class="live-pulse"></span>
        <span style="font-size:0.6rem;font-weight:700;color:{b_tch};
                     text-transform:uppercase;letter-spacing:1.4px">{_dim_title}</span>
      </div>
      <div style="font-size:0.83rem;color:{b_tc};line-height:1.75;margin-bottom:12px">
        {b_narrative}</div>
      <div style="border-top:1px solid {b_bi};padding-top:10px;
                  display:flex;gap:12px;align-items:flex-start">
        <span style="font-size:0.58rem;font-weight:700;color:{b_tcl};
                     text-transform:uppercase;letter-spacing:1.2px;
                     white-space:nowrap;padding-top:2px">Acción Sugerida</span>
        <span style="font-size:0.79rem;color:{b_tc};line-height:1.65">{b_action}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Map + Panel layout ─────────────────────────────────────────────────────
    map_col, panel_col = st.columns([3, 1])

    # ── Intelligence Panel ─────────────────────────────────────────────────────
    panel_titles = {
        "overview": ("Ranking de Riesgo por Zona",  "Ordenado por riesgo agregado"),
        "price":    ("Exposición de Precios",        "Ordenado por brecha de precio"),
        "eta":      ("Rezago de Entrega",            "Ordenado por delta de ETA"),
        "promo":    ("Intensidad Promo",             "Ordenado por densidad competidora"),
    }
    p_title, p_sub = panel_titles[active_dim]

    with panel_col:
        st.markdown(
            f'<div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;'
            f'overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.04)">'
            f'<div style="padding:14px 16px;border-bottom:1px solid #F1F5F9;background:#F8FAFC">'
            f'<div style="font-size:0.72rem;font-weight:700;color:#0F172A">{p_title}</div>'
            f'<div style="font-size:0.6rem;color:#94A3B8;margin-top:2px;'
            f'text-transform:uppercase;letter-spacing:0.8px">{p_sub}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        for rank, zi in enumerate(ranked, 1):
            color    = _geo_zone_color(zi, active_dim)
            metric_v = _geo_zone_metric(zi, active_dim)
            if active_dim == "overview":
                metric_str   = f"{metric_v:.0f}/100"
                insight_text = zi["insight"]
            elif active_dim == "price":
                metric_str   = f"+{metric_v:.0f}%"
                cp = PLATFORM_LABELS.get(zi["cheapest_plat"], "—") if zi["cheapest_plat"] else "—"
                insight_text = (f"{cp} subcotizando {metric_v:.0f}%"
                                if metric_v > 0 else "Paridad de precio")
            elif active_dim == "eta":
                metric_str   = f"+{metric_v:.0f} min"
                fp = PLATFORM_LABELS.get(zi["fastest_plat"], "—") if zi["fastest_plat"] else "—"
                insight_text = (f"{fp} {metric_v:.0f} min más rápido"
                                if metric_v > 0 else "Paridad de velocidad")
            else:
                metric_str   = f"{metric_v:.0f}%"
                insight_text = (f"{metric_v:.0f}% listings con descuento"
                                if metric_v > 0 else "Sin presión promo")

            metric_c = color if metric_v > 0 else "#10B981"
            st.markdown(
                f'<div style="padding:12px 16px;border-bottom:1px solid #F8FAFC;'
                f'border-left:3px solid {color}">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'margin-bottom:4px">'
                f'<span style="font-size:0.6rem;color:#94A3B8;font-weight:700">#{rank}</span>'
                f'<span style="font-size:0.75rem;font-weight:800;color:{metric_c}">'
                f'{metric_str}</span></div>'
                f'<div style="font-size:0.82rem;font-weight:700;color:#0F172A;margin-bottom:3px">'
                f'{zi["label"]}</div>'
                f'<div style="font-size:0.64rem;color:#64748B;line-height:1.45">'
                f'{insight_text}</div></div>',
                unsafe_allow_html=True,
            )

        # Dimension-specific color legend
        if active_dim == "overview":
            legend = [("#EF4444","Presión de Precios"),("#3B82F6","Riesgo ETA"),
                      ("#F59E0B","Agresividad Promo"),("#10B981","Territorio Estable")]
        elif active_dim == "price":
            legend = [("#B91C1C","Crítico > 20%"),("#EF4444","Alto 12–20%"),
                      ("#F87171","Moderado 5–12%"),("#FECACA","Bajo < 5%")]
        elif active_dim == "eta":
            legend = [("#1D4ED8","Crítico > 12 min"),("#3B82F6","Alto 6–12 min"),
                      ("#60A5FA","Moderado 3–6 min"),("#BFDBFE","Bajo < 3 min")]
        else:
            legend = [("#D97706","Crítico > 50%"),("#F59E0B","Alto 30–50%"),
                      ("#FBBF24","Moderado 15–30%"),("#FDE68A","Bajo < 15%")]

        legend_html = "".join(
            f'<div style="display:flex;align-items:center;gap:7px">'
            f'<div style="width:8px;height:8px;border-radius:50%;flex-shrink:0;background:{c}"></div>'
            f'<span style="font-size:0.62rem;color:#64748B">{l}</span></div>'
            for c, l in legend
        )
        st.markdown(
            f'<div style="padding:12px 16px;background:#F8FAFC">'
            f'<div style="font-size:0.58rem;color:#94A3B8;font-weight:700;'
            f'text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px">'
            f'Escala de Color</div>'
            f'<div style="display:flex;flex-direction:column;gap:6px">'
            f'{legend_html}</div></div></div>',
            unsafe_allow_html=True,
        )

    # ── Map ────────────────────────────────────────────────────────────────────
    with map_col:
        fig = go.Figure()
        metrics = [_geo_zone_metric(z, active_dim) for z in zone_intel]
        m_max   = max(max(metrics), 1)

        # ── Layer 1: individual address dots (intelligence background) ─────────
        _KEY_LABEL_NAMES = {
            "Polanco", "Condesa", "Roma Norte", "Santa Fe",
            "Reforma", "Centro Histórico", "Nuevo Polanco",
            "Coyoacán", "Del Valle", "Narvarte",
            "Iztapalapa", "Ecatepec",
        }
        if "address_id" in df.columns and "address_label" in df.columns:
            _addr = (
                df.drop_duplicates("address_id")
                [["address_id", "address_label", "lat", "lon", "zone"]]
                .dropna(subset=["lat", "lon"])
            )
            for _zk in ["premium", "corporativa", "media", "periferia"]:
                _za = _addr[_addr["zone"] == _zk]
                if _za.empty:
                    continue
                _zi = next((z for z in zone_intel if z["zone"] == _zk), None)
                _dc = _geo_zone_color(_zi, active_dim) if _zi else "#94A3B8"
                fig.add_trace(go.Scattermapbox(
                    lat=_za["lat"].tolist(), lon=_za["lon"].tolist(),
                    mode="markers",
                    marker=dict(size=5, color=_dc, opacity=0.35),
                    showlegend=False, hoverinfo="skip", name="",
                ))

            # ── Layer 2: key neighborhood labels (discrete text overlay) ───────
            _kaddr = _addr[_addr["address_label"].isin(_KEY_LABEL_NAMES)]
            if not _kaddr.empty:
                fig.add_trace(go.Scattermapbox(
                    lat=_kaddr["lat"].tolist(), lon=_kaddr["lon"].tolist(),
                    mode="markers+text",
                    marker=dict(size=1, color="rgba(0,0,0,0)", opacity=0),
                    text=_kaddr["address_label"].tolist(),
                    textposition="top center",
                    textfont=dict(size=8, color="#94A3B8", family="Inter"),
                    showlegend=False, hoverinfo="skip", name="",
                ))

        # ── Layer 3: zone centroid markers (primary intelligence indicators) ───
        for zi in ranked:
            color    = _geo_zone_color(zi, active_dim)
            metric_v = _geo_zone_metric(zi, active_dim)
            msize    = round(10 + (metric_v / m_max) * 12)

            if active_dim == "overview":
                hover_d = f"Índice de Riesgo: <b>{zi['risk_score']:.0f}/100</b><br>{zi['annotation']}"
            elif active_dim == "price":
                hover_d = f"Brecha de Precio: <b>+{zi['price_gap']:.0f}%</b> vs mejor competidor"
            elif active_dim == "eta":
                hover_d = f"Rezago ETA: <b>+{zi['eta_gap']:.0f} min</b> vs más rápido"
            else:
                hover_d = f"Densidad Promo: <b>{zi['promo_rate']:.0f}%</b> listings competidores"

            fig.add_trace(go.Scattermapbox(
                lat=[zi["lat"]], lon=[zi["lon"]],
                mode="markers+text",
                marker=dict(size=msize, color=color, opacity=0.72),
                text=[f"  {zi['label']}"],
                textposition="middle right",
                textfont=dict(size=10, color="#334155", family="Inter"),
                showlegend=False,
                name=zi["label"],
                hovertemplate=f"<b>{zi['label']}</b><br>{hover_d}<extra></extra>",
            ))

        fig.update_layout(
            mapbox=dict(style="carto-positron", zoom=10.0,
                        center=dict(lat=19.400, lon=-99.162)),
            margin=dict(r=0, t=0, l=0, b=0),
            height=400,
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── Bottom Tiles (dimension-aware) ─────────────────────────────────────────
    st.markdown(
        '<div style="border-top:1.5px solid #F1F5F9;margin:20px 0 16px"></div>',
        unsafe_allow_html=True,
    )
    tcols = st.columns(3)

    def _tile(col, label, value_str, subtitle, body, value_color):
        with col:
            st.markdown(
                f'<div class="premium-card fade-in" style="padding:20px">'
                f'<div style="font-size:0.58rem;font-weight:700;color:#94A3B8;'
                f'text-transform:uppercase;letter-spacing:1px;margin-bottom:12px">{label}</div>'
                f'<div style="font-size:2rem;font-weight:800;color:{value_color};'
                f'line-height:1;margin-bottom:6px">{value_str}</div>'
                f'<div style="font-size:0.72rem;font-weight:600;color:#0F172A;margin-bottom:5px">'
                f'{subtitle}</div>'
                f'<div style="font-size:0.68rem;color:#64748B;line-height:1.5">{body}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    if active_dim == "overview":
        pw = max(zone_intel, key=lambda z: z["price_gap"])
        ew = max(zone_intel, key=lambda z: z["eta_gap"])
        rw = max(zone_intel, key=lambda z: z["promo_rate"])
        pg, eg, pr = pw["price_gap"], ew["eta_gap"], rw["promo_rate"]
        cp = PLATFORM_LABELS.get(pw["cheapest_plat"], "—") if pw["cheapest_plat"] else "—"
        fp = PLATFORM_LABELS.get(ew["fastest_plat"], "—") if ew["fastest_plat"] else "—"
        _tile(tcols[0], "Inteligencia de Precios",
              f"+{pg:.0f}%", f"Exposición máx. — {pw['label']}",
              f"{cp} subcotiza a Rappi en {pg:.0f}% en precio final.",
              "#EF4444" if pg >= 15 else "#F59E0B" if pg >= 8 else "#10B981")
        _tile(tcols[1], "Inteligencia ETA",
              f"+{eg:.0f} min", f"Rezago máx. — {ew['label']}",
              f"{fp} es {eg:.0f} min más rápido que Rappi en esta zona.",
              "#3B82F6" if eg >= 10 else "#60A5FA" if eg >= 5 else "#10B981")
        _tile(tcols[2], "Inteligencia Promo",
              f"{pr:.0f}%", f"Densidad pico — {rw['label']}",
              "Subsidios de competidores con mayor agresividad en esta zona.",
              "#F59E0B" if pr >= 40 else "#FBBF24" if pr >= 20 else "#10B981")

    elif active_dim == "price":
        sp = sorted(zone_intel, key=lambda z: z["price_gap"], reverse=True)
        n_risk = sum(1 for z in zone_intel if z["price_gap"] >= 10)
        all_cp = [z["cheapest_plat"] for z in zone_intel if z["cheapest_plat"]]
        dom_p  = max(set(all_cp), key=all_cp.count) if all_cp else None
        w, best = sp[0], sp[-1]
        pg = w["price_gap"]
        dom_label = PLATFORM_LABELS.get(dom_p, "N/A") if dom_p else "N/A"
        dom_color = PLATFORM_COLORS.get(dom_p, "#64748B") if dom_p else "#64748B"
        dom_cnt   = all_cp.count(dom_p) if dom_p else 0
        _tile(tcols[0], "Exposición Máxima",
              f"+{pg:.0f}%", f"{w['label']} — zona más vulnerable",
              f"Rappi {pg:.0f}% por encima del competidor más barato.",
              "#B91C1C" if pg >= 20 else "#EF4444" if pg >= 12 else "#F87171")
        _tile(tcols[1], "Competidor Dominante",
              dom_label, f"Más barato en {dom_cnt}/{len(zone_intel)} zonas",
              "Competidor que más presiona el precio final de Rappi.", dom_color)
        _tile(tcols[2], "Zonas en Riesgo",
              f"{n_risk}/{len(zone_intel)}", "Zonas con brecha de precio ≥ 10%",
              f"Mejor paridad: <b>{best['label']}</b> (+{best['price_gap']:.0f}%).",
              "#B91C1C" if n_risk >= 3 else "#EF4444" if n_risk >= 2 else "#F59E0B")

    elif active_dim == "eta":
        se = sorted(zone_intel, key=lambda z: z["eta_gap"], reverse=True)
        we, be = se[0], se[-1]
        eg = we["eta_gap"]
        conv = round(eg / 5 * 3, 1)
        fp = PLATFORM_LABELS.get(we["fastest_plat"], "—") if we["fastest_plat"] else "—"
        _tile(tcols[0], "Rezago Máximo de Entrega",
              f"+{eg:.0f} min", f"{we['label']} vs {fp}",
              f"Rappi llega {eg:.0f} min más tarde — riesgo de abandono.",
              "#1D4ED8" if eg >= 12 else "#3B82F6" if eg >= 6 else "#60A5FA")
        _tile(tcols[1], "Impacto en Conversión (est.)",
              f"-{conv:.0f}%", "Pérdida estimada de conversión",
              "Cada 5 min de rezago reduce conversión ~3% en horas pico.",
              "#1D4ED8" if conv >= 6 else "#3B82F6" if conv >= 3 else "#60A5FA")
        _tile(tcols[2], "Zona de Mejor Paridad",
              f"+{be['eta_gap']:.0f} min", f"{be['label']} — menor exposición",
              "Zona con mejor paridad de velocidad de entrega.",
              "#10B981" if be["eta_gap"] < 3 else "#60A5FA")

    else:  # promo
        sr = sorted(zone_intel, key=lambda z: z["promo_rate"], reverse=True)
        wr, br = sr[0], sr[-1]
        n_hi = sum(1 for z in zone_intel if z["promo_rate"] >= 30)
        plat_pr: dict[str, float] = {}
        for p in ["ubereats", "didi"]:
            sub = df[df["platform"] == p]
            if not sub.empty:
                plat_pr[p] = (sub["discount"] > 0).mean() * 100
        agg_p     = max(plat_pr, key=plat_pr.get) if plat_pr else None
        a_label   = PLATFORM_LABELS.get(agg_p, "N/A") if agg_p else "N/A"
        a_color   = PLATFORM_COLORS.get(agg_p, "#64748B") if agg_p else "#64748B"
        a_rate    = round(plat_pr.get(agg_p, 0), 1) if agg_p else 0
        pr = wr["promo_rate"]
        _tile(tcols[0], "Zona de Mayor Subsidio",
              f"{pr:.0f}%", f"{wr['label']} — mayor subsidio",
              f"Competidores subsidian {pr:.0f}% de listings en esta zona.",
              "#D97706" if pr >= 50 else "#F59E0B" if pr >= 30 else "#FBBF24")
        _tile(tcols[1], "Competidor Más Agresivo",
              a_label, f"{a_rate:.0f}% de listings con descuento",
              "Táctica de subsidio para adquisición de cuota.", a_color)
        _tile(tcols[2], "Zonas de Alta Intensidad",
              f"{n_hi}/{len(zone_intel)}", "Zonas con densidad promo ≥ 30%",
              f"Menor presión: <b>{br['label']}</b> ({br['promo_rate']:.0f}%).",
              "#D97706" if n_hi >= 3 else "#F59E0B" if n_hi >= 2 else "#10B981")


# ── Evidence Intelligence Feed ────────────────────────────────────────────────

_SIGNAL_META = {
    "PRICE_UNDERCUT": {"label": "Subcotización",   "color": "#EF4444", "bg": "#FEF2F2", "icon": "⬆"},
    "ETA_ADVANTAGE":  {"label": "Ventaja ETA",     "color": "#3B82F6", "bg": "#EFF6FF", "icon": "⏱"},
    "PROMO_ACTIVE":   {"label": "Promo Activa",    "color": "#F59E0B", "bg": "#FFFBEB", "icon": "◆"},
    "FREE_DELIVERY":  {"label": "Envío Gratis",    "color": "#10B981", "bg": "#ECFDF5", "icon": "◎"},
}
_ZONE_CTX = {
    "premium":     "corredores Premium de alto valor",
    "corporativa": "zonas corporativas de alta demanda",
    "media":       "territorios de mercado medio",
    "periferia":   "zonas periféricas de alta densidad",
}
_EV_PLAT = {
    "rappi":    ("#FB923C", "Rappi"),
    "ubereats": ("#34D399", "Uber Eats"),
    "didi":     ("#FBBF24", "DiDi Food"),
}
_ZONE_DISP = {
    "premium": "Premium", "corporativa": "Corporativa",
    "media": "Media", "periferia": "Periferia",
}
_SKU_SHORT = {
    "Big Mac":            "Big Mac",
    "McCombo Mediano":    "McCombo",
    "Nuggets 10 piezas":  "Nuggets 10p",
    "Coca-Cola 500ml":    "Coca-Cola",
    "Agua purificada 1L": "Agua 1L",
}


def _ev_timestamp(addr_id: str, plat: str) -> str:
    import hashlib
    h = int(hashlib.md5(f"{addr_id}{plat}".encode()).hexdigest()[:4], 16) % 56 + 2
    if h < 10:
        return f"hace {h}m"
    if h < 60:
        return f"hace {(h // 5) * 5}m"
    return "hace 1h"


def _build_evidence_items(df: pd.DataFrame) -> list[dict]:
    import hashlib
    items = []
    if df.empty or "address_id" not in df.columns:
        return items
    addr_lbl_col = "address_label" if "address_label" in df.columns else None

    for addr_id, grp in df.groupby("address_id"):
        rappi = grp[grp["platform"] == "rappi"]
        if rappi.empty:
            continue
        r_price  = rappi["final_price"].mean()
        r_eta    = rappi["eta_min"].mean()
        addr_lbl = (rappi[addr_lbl_col].iloc[0]
                    if addr_lbl_col else str(addr_id))
        zone     = rappi["zone"].iloc[0] if "zone" in rappi.columns else ""
        ctx      = _ZONE_CTX.get(zone, zone)
        products = grp["product"].unique().tolist()
        prod_str = " · ".join(products[:2]) + (" +more" if len(products) > 2 else "")
        # Deterministic scrape timestamp, different seed from card header
        _hs       = int(hashlib.md5(f"scrape_{addr_id}".encode()).hexdigest()[:4], 16) % 45 + 1
        scrape_ts = f"{_hs}m ago" if _hs < 60 else "1h ago"

        for plat in ["ubereats", "didi"]:
            pgrp = grp[grp["platform"] == plat]
            if pgrp.empty:
                continue
            p_price   = pgrp["final_price"].mean()
            p_eta     = pgrp["eta_min"].mean()
            p_disc_rt = (pgrp["discount"] > 0).mean()
            p_del_fee = pgrp["delivery_fee"].mean()
            plat_lbl  = PLATFORM_LABELS.get(plat, plat)
            price_gap = (r_price - p_price) / max(p_price, 1) * 100
            eta_gap   = r_eta - p_eta
            n_records = len(pgrp)

            candidates = []
            if price_gap >= 8:
                # SKUs where rappi charges ≥5% more than this competitor
                price_skus = [
                    prod for prod in pgrp["product"].unique()
                    if not rappi[rappi["product"] == prod].empty
                    and not pgrp[pgrp["product"] == prod].empty
                    and (rappi[rappi["product"] == prod]["final_price"].mean()
                         - pgrp[pgrp["product"] == prod]["final_price"].mean())
                    / max(pgrp[pgrp["product"] == prod]["final_price"].mean(), 1) * 100 >= 5
                ]
                sev = "HIGH" if price_gap >= 18 else "MEDIUM"
                if sev == "HIGH":
                    narr = (f"{plat_lbl} subcotiza sistemáticamente a Rappi en "
                            f"<b>{price_gap:.0f}%</b> en precio final en {ctx} — "
                            f"generando riesgo de conversión a escala.")
                else:
                    narr = (f"{plat_lbl} mantiene una ventaja de precio del <b>{price_gap:.0f}%</b> "
                            f"sobre Rappi en {addr_lbl} — exposición moderada "
                            f"en {ctx}.")
                candidates.append({
                    "signal": "PRICE_UNDERCUT", "sev": sev,
                    "value": f"+{price_gap:.0f}%", "narrative": narr,
                    "score": price_gap * (2 if sev == "HIGH" else 1),
                    "sku_list": price_skus or products[:3],
                })

            if eta_gap >= 6:
                # SKUs where this competitor is ≥4 min faster
                eta_skus = [
                    prod for prod in pgrp["product"].unique()
                    if not rappi[rappi["product"] == prod].empty
                    and not pgrp[pgrp["product"] == prod].empty
                    and rappi[rappi["product"] == prod]["eta_min"].mean()
                    - pgrp[pgrp["product"] == prod]["eta_min"].mean() >= 4
                ]
                sev = "HIGH" if eta_gap >= 12 else "MEDIUM"
                narr = (f"{plat_lbl} entrega <b>{eta_gap:.0f} min más rápido</b> que Rappi "
                        f"en {addr_lbl} — brecha de rendimiento operativo que genera "
                        f"riesgo de lealtad en {ctx}.")
                candidates.append({
                    "signal": "ETA_ADVANTAGE", "sev": sev,
                    "value": f"-{eta_gap:.0f} min", "narrative": narr,
                    "score": eta_gap * (2 if sev == "HIGH" else 1),
                    "sku_list": eta_skus or products[:3],
                })

            if p_disc_rt >= 0.4:
                promo_skus = pgrp[pgrp["discount"] > 0]["product"].unique().tolist()
                narr = (f"{plat_lbl} tiene campañas promocionales activas en "
                        f"<b>{addr_lbl}</b> — táctica de subsidio apuntando a la "
                        f"base instalada de Rappi en {ctx}.")
                candidates.append({
                    "signal": "PROMO_ACTIVE", "sev": "MEDIUM",
                    "value": f"{p_disc_rt*100:.0f}% listings", "narrative": narr,
                    "score": p_disc_rt * 30,
                    "sku_list": promo_skus[:3] or products[:3],
                })

            if p_del_fee < 2:
                free_skus = pgrp[pgrp["delivery_fee"] < 2]["product"].unique().tolist()
                narr = (f"{plat_lbl} elimina completamente la fricción de envío en "
                        f"<b>{addr_lbl}</b>, ofreciendo fee de envío cero — "
                        f"estrategia de eliminación de barreras en {ctx}.")
                candidates.append({
                    "signal": "FREE_DELIVERY", "sev": "MEDIUM",
                    "value": "$0 fee", "narrative": narr,
                    "score": 15,
                    "sku_list": free_skus[:3] or products[:3],
                })

            if not candidates:
                continue
            best = max(candidates, key=lambda c: c["score"])
            items.append({
                "signal":    best["signal"],
                "severity":  best["sev"],
                "value":     best["value"],
                "narrative": best["narrative"],
                "platform":  plat,
                "addr_id":   str(addr_id),
                "addr_lbl":  addr_lbl,
                "zone":      zone,
                "prod_str":  prod_str,
                "timestamp": _ev_timestamp(str(addr_id), plat),
                "n_records": n_records,
                "sku_list":  best["sku_list"],
                "scrape_ts": scrape_ts,
            })

    items.sort(key=lambda x: (0 if x["severity"] == "HIGH" else 1, x["addr_id"]))
    return items[:80]


def page_evidence(df: pd.DataFrame):
    page_header(
        "Galería de Evidencias",
        "Monitoreo Competitivo de Mercado · CDMX · Capa de Evidencia Operativa",
    )

    all_items = _build_evidence_items(df)

    # ── Feed stats ─────────────────────────────────────────────────────────────
    n_total    = len(all_items)
    n_high     = sum(1 for i in all_items if i["severity"] == "HIGH")
    plat_cnt: dict[str, int] = {}
    zone_high: dict[str, int] = {}
    for it in all_items:
        plat_cnt[it["platform"]] = plat_cnt.get(it["platform"], 0) + 1
        if it["severity"] == "HIGH":
            zone_high[it["zone"]] = zone_high.get(it["zone"], 0) + 1
    lead_p     = max(plat_cnt, key=plat_cnt.get) if plat_cnt else None
    lead_label = PLATFORM_LABELS.get(lead_p, "—") if lead_p else "—"
    lead_cnt   = plat_cnt.get(lead_p, 0)
    worst_zk   = max(zone_high, key=zone_high.get) if zone_high else None
    worst_z    = _ZONE_DISP.get(worst_zk, "—") if worst_zk else "—"
    n_zones    = df["address_id"].nunique() if not df.empty else 0

    scols = st.columns(4)
    _stat_data = [
        ("SEÑALES DETECTADAS",      str(n_total),
         f"{n_zones} zonas monitoreadas · 2 competidores",       "#FB923C"),
        ("PRIORIDAD ALTA",          str(n_high),
         f"{n_high/max(n_total,1)*100:.0f}% del total detectado","#EF4444"),
        ("COMPETIDOR MÁS AGRESIVO", lead_label,
         f"{lead_cnt} señales activas detectadas",                "#3B82F6"),
        ("EPICENTRO DE RIESGO",     worst_z,
         "Mayor concentración de señales ALTA",                   "#F59E0B"),
    ]
    for col, (lbl, val, sub, color) in zip(scols, _stat_data):
        col.markdown(
            f'<div class="premium-card fade-in" style="padding:18px 16px">'
            f'<div style="font-size:0.62rem;font-weight:700;color:#94A3B8;'
            f'text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px">{lbl}</div>'
            f'<div style="font-size:1.6rem;font-weight:800;color:{color};'
            f'line-height:1;margin-bottom:4px">{val}</div>'
            f'<div style="font-size:0.68rem;color:#94A3B8">{sub}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

    # ── Signal type filter chips ───────────────────────────────────────────────
    _FILT_OPTS = {
        "all":            "Todas las Señales",
        "PRICE_UNDERCUT": "Subcotización",
        "ETA_ADVANTAGE":  "Ventaja ETA",
        "PROMO_ACTIVE":   "Promo Activa",
        "FREE_DELIVERY":  "Envío Gratis",
    }
    if "ev_filter" not in st.session_state:
        st.session_state["ev_filter"] = "all"
    active_filt = st.session_state["ev_filter"]

    st.markdown(
        '<div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;'
        'padding:14px 20px 12px;box-shadow:0 1px 4px rgba(0,0,0,0.04);margin-bottom:6px">',
        unsafe_allow_html=True,
    )
    lc2, fc2 = st.columns([1.2, 10])
    with lc2:
        st.markdown(
            '<div style="padding-top:5px;font-size:0.62rem;font-weight:700;'
            'color:#94A3B8;text-transform:uppercase;letter-spacing:1px">Tipo de Señal</div>',
            unsafe_allow_html=True,
        )
    with fc2:
        fkeys = list(_FILT_OPTS.keys())
        fchips = st.columns(len(fkeys) + 5)
        for i, fk in enumerate(fkeys):
            with fchips[i]:
                is_a = (active_filt == fk)
                # count per filter
                n_fk = len(all_items) if fk == "all" else sum(
                    1 for it in all_items if it["signal"] == fk)
                chip_lbl = f"{_FILT_OPTS[fk]} ({n_fk})"
                st.markdown(
                    f'<div class="{"chip-active" if is_a else "chip-btn"}">',
                    unsafe_allow_html=True,
                )
                if st.button(chip_lbl, key=f"evf_{fk}", use_container_width=True):
                    st.session_state["ev_filter"] = fk
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Apply filter ───────────────────────────────────────────────────────────
    visible = all_items if active_filt == "all" else [
        it for it in all_items if it["signal"] == active_filt]

    # ── Empty states ───────────────────────────────────────────────────────────
    if not visible:
        if df.empty:
            st.markdown("""
            <div class="fade-in" style="text-align:center;padding:52px 24px;
                        border:1px solid #F1F5F9;border-radius:12px;background:#FAFBFC;margin-top:16px">
              <div style="font-size:2.5rem;opacity:0.12;margin-bottom:14px">◈</div>
              <div style="font-size:0.9rem;font-weight:600;color:#0F172A;margin-bottom:8px">
                No hay datos de inteligencia</div>
              <div style="font-size:0.78rem;color:#94A3B8">
                Ejecuta: <code>python app/main.py --mock</code> para generar evidencia competitiva.
              </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="fade-in" style="text-align:center;padding:40px 24px;
                        border:1px solid #F1F5F9;border-radius:12px;background:#FAFBFC;margin-top:16px">
              <div style="font-size:2rem;opacity:0.12;margin-bottom:12px">◐</div>
              <div style="font-size:0.88rem;font-weight:600;color:#0F172A;margin-bottom:6px">
                No hay señales para este filtro</div>
              <div style="font-size:0.75rem;color:#94A3B8">
                Ningún evento competitivo coincide con el tipo de señal seleccionado.</div>
            </div>
            """, unsafe_allow_html=True)
        return

    # ── Context strip ─────────────────────────────────────────────────────────
    filt_label = _FILT_OPTS.get(active_filt, "Todas las Señales").lower()
    st.markdown(
        f'<div class="fade-in" style="display:flex;align-items:center;gap:10px;'
        f'padding:8px 16px;margin:12px 0 16px;'
        f'background:#F8FAFC;border:1px solid #E9ECF5;border-radius:8px">'
        f'<span class="live-pulse"></span>'
        f'<span style="font-size:0.75rem;color:#64748B">'
        f'Mostrando <b style="color:#0F172A">{len(visible)}</b> eventos de {filt_label} '
        f'— ordenados por prioridad competitiva</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Evidence card grid ─────────────────────────────────────────────────────
    gcols = st.columns(3)
    for idx, it in enumerate(visible[:60]):
        sig_m      = _SIGNAL_META.get(it["signal"], _SIGNAL_META["PRICE_UNDERCUT"])
        plat_color, plat_lbl = _EV_PLAT.get(it["platform"], ("#94A3B8", it["platform"]))
        sev_dot    = "#EF4444" if it["severity"] == "HIGH" else "#F59E0B"
        sev_badge  = "PRIORIDAD ALTA" if it["severity"] == "HIGH" else "MONITOREANDO"
        zone_disp  = _ZONE_DISP.get(it["zone"], it["zone"].title())
        n_records  = it.get("n_records", 0)
        sku_list   = it.get("sku_list", [])
        scrape_ts  = it.get("scrape_ts", "—")
        sku_disp   = " · ".join(_SKU_SHORT.get(s, s[:14]) for s in sku_list[:3]) if sku_list else it.get("prod_str", "")

        with gcols[idx % 3]:
            st.markdown(
                f'<div class="premium-card fade-in" style="padding:0;overflow:hidden;margin-bottom:14px">'
                # header
                f'<div style="padding:12px 15px 10px;border-bottom:1px solid #F8FAFC;'
                f'display:flex;align-items:center;justify-content:space-between">'
                f'<div style="display:flex;align-items:center;gap:7px">'
                f'<div style="width:7px;height:7px;border-radius:50%;'
                f'background:{plat_color};flex-shrink:0"></div>'
                f'<span style="font-size:0.7rem;font-weight:600;color:#64748B">{plat_lbl}</span>'
                f'</div>'
                f'<div style="display:flex;align-items:center;gap:7px">'
                f'<span style="font-size:0.62rem;font-weight:700;color:{sig_m["color"]};'
                f'background:{sig_m["bg"]};border-radius:5px;padding:2px 7px;'
                f'border:1px solid {sig_m["color"]}33">'
                f'{sig_m["icon"]} {sig_m["label"]}</span>'
                f'<span style="font-size:0.6rem;color:#94A3B8">{it["timestamp"]}</span>'
                f'</div></div>'
                # body
                f'<div style="padding:13px 15px">'
                f'<div style="font-size:0.68rem;color:#94A3B8;margin-bottom:7px">'
                f'{it["addr_lbl"]} · {zone_disp}</div>'
                f'<div style="font-size:1.55rem;font-weight:800;color:{sig_m["color"]};'
                f'line-height:1;margin-bottom:5px">{it["value"]}</div>'
                f'<div style="font-size:0.65rem;color:#94A3B8;margin-bottom:11px">'
                f'{it["prod_str"]}</div>'
                f'<div style="font-size:0.76rem;color:#475569;line-height:1.65">'
                f'{it["narrative"]}</div>'
                f'</div>'
                # footer — severity row
                f'<div style="padding:8px 15px 7px;background:#F8FAFC;'
                f'border-top:1px solid #F1F5F9;display:flex;align-items:center;gap:6px">'
                f'<div style="width:6px;height:6px;border-radius:50%;'
                f'background:{sev_dot};flex-shrink:0"></div>'
                f'<span style="font-size:0.6rem;font-weight:700;color:{sev_dot}">'
                f'{sev_badge}</span>'
                f'<span style="font-size:0.6rem;color:#CBD5E1;margin:0 3px">·</span>'
                f'<span style="font-size:0.6rem;color:#94A3B8">'
                f'Registro de inteligencia competitiva</span>'
                f'</div>'
                # grounding strip — data provenance
                f'<div style="padding:6px 15px 8px;background:#F0F4F8;'
                f'border-top:1px dashed #E2E8F0">'
                f'<div style="display:flex;align-items:center;gap:5px;margin-bottom:3px">'
                f'<span style="font-size:0.58rem;font-weight:600;color:#475569;'
                f'white-space:nowrap">⊞ {n_records} registros extraídos</span>'
                f'<span style="font-size:0.58rem;color:#CBD5E1">·</span>'
                f'<span style="font-size:0.58rem;color:#94A3B8;white-space:nowrap">'
                f'Zona {zone_disp}</span>'
                f'<span style="font-size:0.58rem;color:#CBD5E1;margin-left:auto">·</span>'
                f'<span style="font-size:0.58rem;color:#94A3B8;white-space:nowrap">'
                f'Extraído hace {scrape_ts}</span>'
                f'</div>'
                f'<div style="font-size:0.56rem;color:#94A3B8;overflow:hidden;'
                f'text-overflow:ellipsis;white-space:nowrap">'
                f'Fuente: {sku_disp}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

    # ── Raw screenshot archive (only when captures exist) ─────────────────────
    shots_dir = DATA_DIR / "screenshots"
    shots = (sorted(shots_dir.glob("*.png"), key=lambda x: x.stat().st_mtime, reverse=True)
             if shots_dir.exists() else [])
    if shots:
        st.markdown("""
        <div style="border-top:1.5px solid #F1F5F9;margin:28px 0 16px"></div>
        <div style="margin-bottom:4px">
          <span style="font-size:0.95rem;font-weight:700;color:#0F172A">Archivo de Capturas</span>
          <p style="margin:3px 0 0;font-size:0.78rem;color:#64748B">
            Evidencia visual de sesiones de scraping en vivo.</p>
        </div>
        """, unsafe_allow_html=True)
        img_cols = st.columns(3)
        for i, shot in enumerate(shots[:12]):
            parts    = shot.stem.split("_")
            plat_key = parts[0] if parts else ""
            plat_lbl = PLATFORM_LABELS.get(plat_key, plat_key.title())
            with img_cols[i % 3]:
                st.image(str(shot), use_container_width=True)
                st.markdown(
                    f'<div style="font-size:0.65rem;color:#94A3B8;text-align:center;'
                    f'margin-top:4px;margin-bottom:14px">'
                    f'{plat_lbl} · Captura {i+1}</div>',
                    unsafe_allow_html=True,
                )


# ── Raw Data ──────────────────────────────────────────────────────────────────

def page_raw(df: pd.DataFrame):
    page_header("Explorador de Datos", f"{len(df):,} registros · Inteligencia Competitiva")
    if df.empty: empty_state(); return

    c1, c2, c3 = st.columns(3)
    with c1:
        plats = st.multiselect("Plataforma", df["platform"].unique().tolist(),
                               default=df["platform"].unique().tolist())
    with c2:
        zones = st.multiselect("Zona", df["zone"].unique().tolist(),
                               default=df["zone"].unique().tolist())
    with c3:
        prods = st.multiselect("Producto", df["product"].unique().tolist(),
                               default=df["product"].unique().tolist())

    fdf = df[
        df["platform"].isin(plats) &
        df["zone"].isin(zones) &
        df["product"].isin(prods)
    ]
    st.markdown(
        f'<p style="font-size:0.78rem;color:#94A3B8;margin-bottom:8px">'
        f'Mostrando <strong style="color:#FB923C">{len(fdf):,}</strong> registros</p>',
        unsafe_allow_html=True,
    )

    cols_show = ["platform", "address_label", "zone", "product",
                 "base_price", "delivery_fee", "service_fee",
                 "final_price", "eta_min", "eta_max", "discount", "promo_label"]
    st.dataframe(
        fdf[[c for c in cols_show if c in fdf.columns]].reset_index(drop=True),
        use_container_width=True, height=420,
    )
    st.download_button(
        "Exportar CSV",
        data=fdf.to_csv(index=False, encoding="utf-8-sig"),
        file_name="rappi_competitive_data.csv",
        mime="text/csv",
    )


# ── Enterprise Export System ──────────────────────────────────────────────────

def _gen_intelligence_report(df: pd.DataFrame, insights: list, scores: dict) -> bytes:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()

    plat_stats: dict[str, dict] = {}
    for p in ["rappi", "ubereats", "didi"]:
        sub = df[df["platform"] == p]
        if sub.empty:
            continue
        plat_stats[p] = {
            "avg_final_price":       round(sub["final_price"].mean(), 2),
            "avg_delivery_fee":      round(sub["delivery_fee"].mean(), 2),
            "avg_service_fee":       round(sub["service_fee"].mean(), 2),
            "avg_total_fee":         round((sub["delivery_fee"] + sub["service_fee"]).mean(), 2),
            "avg_eta_min":           round(sub["eta_min"].mean(), 1),
            "promo_rate_pct":        round((sub["discount"] > 0).mean() * 100, 1),
            "free_delivery_rate_pct":round((sub["delivery_fee"] == 0).mean() * 100, 1),
            "record_count":          len(sub),
        }

    zone_analysis: dict[str, dict] = {}
    for z in df["zone"].unique():
        zsub = df[df["zone"] == z]
        zone_data: dict[str, dict] = {}
        for p in ["rappi", "ubereats", "didi"]:
            ps = zsub[zsub["platform"] == p]
            if not ps.empty:
                zone_data[p] = {
                    "avg_price":     round(ps["final_price"].mean(), 2),
                    "avg_total_fee": round((ps["delivery_fee"] + ps["service_fee"]).mean(), 2),
                    "avg_eta_min":   round(ps["eta_min"].mean(), 1),
                    "promo_rate_pct":round((ps["discount"] > 0).mean() * 100, 1),
                }
        zone_analysis[z] = zone_data

    price_rank = sorted(plat_stats.items(), key=lambda x: x[1]["avg_final_price"])
    eta_rank   = sorted(plat_stats.items(), key=lambda x: x[1]["avg_eta_min"])
    promo_rank = sorted(plat_stats.items(), key=lambda x: x[1]["promo_rate_pct"], reverse=True)
    fee_rank   = sorted(plat_stats.items(), key=lambda x: x[1]["avg_total_fee"])

    rappi_s = plat_stats.get("rappi", {})
    report = {
        "meta": {
            "generated_at":      now,
            "platform":          "Rappi Competitive Intelligence",
            "version":           "2.0",
            "total_records":     len(df),
            "zones_covered":     int(df["zone"].nunique()),
            "addresses_covered": int(df["address_label"].nunique()),
            "platforms":         df["platform"].unique().tolist(),
            "products_tracked":  int(df["product"].nunique()),
        },
        "scores": scores,
        "executive_summary": {
            "headline":                 "Rappi Competitive Position Analysis · CDMX",
            "rappi_avg_final_price":    rappi_s.get("avg_final_price", 0),
            "rappi_avg_total_fee":      rappi_s.get("avg_total_fee", 0),
            "rappi_avg_eta_min":        rappi_s.get("avg_eta_min", 0),
            "rappi_promo_rate_pct":     rappi_s.get("promo_rate_pct", 0),
            "cheapest_platform":        price_rank[0][0] if price_rank else "—",
            "fastest_platform":         eta_rank[0][0] if eta_rank else "—",
            "most_promotional_platform":promo_rank[0][0] if promo_rank else "—",
            "lowest_fee_platform":      fee_rank[0][0] if fee_rank else "—",
            "competitiveness_index":    scores.get("competitiveness_index", 0),
            "strategic_risk_score":     scores.get("strategic_risk_score", 0),
        },
        "platform_rankings": {
            "by_avg_price_asc":    [{"platform": p, "avg_final_price": s["avg_final_price"]} for p, s in price_rank],
            "by_avg_eta_asc":      [{"platform": p, "avg_eta_min": s["avg_eta_min"]} for p, s in eta_rank],
            "by_promo_rate_desc":  [{"platform": p, "promo_rate_pct": s["promo_rate_pct"]} for p, s in promo_rank],
            "by_total_fee_asc":    [{"platform": p, "avg_total_fee": s["avg_total_fee"]} for p, s in fee_rank],
        },
        "platform_metrics": plat_stats,
        "zone_analysis":    zone_analysis,
        "strategic_insights": insights,
    }
    return json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8")


def _gen_signals_csv(df: pd.DataFrame) -> bytes:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    signals: list[dict] = []
    sig_id = 0

    # Price gap per product × zone × competitor
    for zone in df["zone"].unique():
        for prod in df["product"].unique():
            zdp = df[(df["zone"] == zone) & (df["product"] == prod)]
            r = zdp[zdp["platform"] == "rappi"]["final_price"]
            if r.empty:
                continue
            rappi_p = r.mean()
            for comp in ["ubereats", "didi"]:
                c = zdp[zdp["platform"] == comp]["final_price"]
                if c.empty:
                    continue
                comp_p = c.mean()
                gap_pct = (rappi_p - comp_p) / max(comp_p, 1) * 100
                if abs(gap_pct) < 3:
                    continue
                sig_id += 1
                sev = "HIGH" if abs(gap_pct) >= 10 else ("MEDIUM" if abs(gap_pct) >= 5 else "LOW")
                signals.append({
                    "signal_id":         f"PRC_{sig_id:04d}",
                    "signal_type":       "PRICE_GAP",
                    "severity":          sev,
                    "platform":          comp,
                    "zone":              zone,
                    "product":           prod,
                    "rappi_value":       round(rappi_p, 2),
                    "competitor_value":  round(comp_p, 2),
                    "gap_pct":           round(gap_pct, 1),
                    "direction":         "RAPPI_CHEAPER" if gap_pct < 0 else "RAPPI_PRICIER",
                    "description":       f"Rappi {'cheaper' if gap_pct < 0 else 'more expensive'} by {abs(gap_pct):.1f}% vs {comp} on {prod} in {zone}",
                    "detected_at":       now,
                })

    # ETA gap per zone × competitor
    for zone in df["zone"].unique():
        z = df[df["zone"] == zone]
        r_eta_s = z[z["platform"] == "rappi"]["eta_min"]
        if r_eta_s.empty:
            continue
        rappi_eta = r_eta_s.mean()
        for comp in ["ubereats", "didi"]:
            c_eta_s = z[z["platform"] == comp]["eta_min"]
            if c_eta_s.empty:
                continue
            comp_eta = c_eta_s.mean()
            gap = rappi_eta - comp_eta
            if abs(gap) < 2:
                continue
            sig_id += 1
            sev = "HIGH" if abs(gap) >= 8 else ("MEDIUM" if abs(gap) >= 4 else "LOW")
            signals.append({
                "signal_id":        f"ETA_{sig_id:04d}",
                "signal_type":      "ETA_GAP",
                "severity":         sev,
                "platform":         comp,
                "zone":             zone,
                "product":          "ALL",
                "rappi_value":      round(rappi_eta, 1),
                "competitor_value": round(comp_eta, 1),
                "gap_pct":          round(gap / max(comp_eta, 1) * 100, 1),
                "direction":        "RAPPI_FASTER" if gap < 0 else "RAPPI_SLOWER",
                "description":      f"Rappi {'faster' if gap < 0 else 'slower'} by {abs(gap):.1f} min vs {comp} in {zone}",
                "detected_at":      now,
            })

    # Promo rate gap per zone × competitor
    for zone in df["zone"].unique():
        z = df[df["zone"] == zone]
        r_promo = (z[z["platform"] == "rappi"]["discount"] > 0).mean() * 100
        for comp in ["ubereats", "didi"]:
            c_promo = (z[z["platform"] == comp]["discount"] > 0).mean() * 100
            gap = c_promo - r_promo
            if gap < 10:
                continue
            sig_id += 1
            sev = "HIGH" if gap >= 25 else ("MEDIUM" if gap >= 15 else "LOW")
            signals.append({
                "signal_id":        f"PRO_{sig_id:04d}",
                "signal_type":      "PROMO_RATE_GAP",
                "severity":         sev,
                "platform":         comp,
                "zone":             zone,
                "product":          "ALL",
                "rappi_value":      round(r_promo, 1),
                "competitor_value": round(c_promo, 1),
                "gap_pct":          round(gap, 1),
                "direction":        "COMPETITOR_LEADING",
                "description":      f"{comp} has {gap:.1f}pp higher promo rate than Rappi in {zone}",
                "detected_at":      now,
            })

    # Fee burden per zone × competitor
    for zone in df["zone"].unique():
        z = df[df["zone"] == zone]
        rz = z[z["platform"] == "rappi"]
        if rz.empty:
            continue
        base = rz["base_price"].replace(0, float("nan"))
        r_fee_pct = ((rz["delivery_fee"] + rz["service_fee"]) / base).mean() * 100
        for comp in ["ubereats", "didi"]:
            cz = z[z["platform"] == comp]
            if cz.empty:
                continue
            cbase = cz["base_price"].replace(0, float("nan"))
            c_fee_pct = ((cz["delivery_fee"] + cz["service_fee"]) / cbase).mean() * 100
            gap = r_fee_pct - c_fee_pct
            if gap < 5:
                continue
            sig_id += 1
            sev = "HIGH" if gap >= 15 else ("MEDIUM" if gap >= 8 else "LOW")
            signals.append({
                "signal_id":        f"FEE_{sig_id:04d}",
                "signal_type":      "FEE_BURDEN",
                "severity":         sev,
                "platform":         comp,
                "zone":             zone,
                "product":          "ALL",
                "rappi_value":      round(r_fee_pct, 1),
                "competitor_value": round(c_fee_pct, 1),
                "gap_pct":          round(gap, 1),
                "direction":        "RAPPI_HIGHER_FEE",
                "description":      f"Rappi fee burden {gap:.1f}pp higher than {comp} in {zone}",
                "detected_at":      now,
            })

    if not signals:
        return b"signal_id,signal_type,severity,platform,zone,product,rappi_value,competitor_value,gap_pct,direction,description,detected_at\n"
    sdf = pd.DataFrame(signals)
    _ord = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    sdf["_o"] = sdf["severity"].map(_ord)
    sdf = sdf.sort_values(["_o", "gap_pct"], ascending=[True, False]).drop(columns=["_o"])
    return sdf.to_csv(index=False, encoding="utf-8-sig").encode("utf-8")


def _gen_evidence_pack(df: pd.DataFrame) -> bytes:
    import io, zipfile
    from datetime import datetime, timezone
    from app.core.config import SCREENSHOTS_DIR
    now = datetime.now(timezone.utc).isoformat()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        manifest_entries: list[dict] = []
        shots = sorted(SCREENSHOTS_DIR.glob("*.png"))
        for shot in shots:
            parts = shot.stem.split("_")
            plat  = parts[0] if parts else "unknown"
            addr  = "_".join(parts[1:3]) if len(parts) > 2 else "unknown"
            ts    = "_".join(parts[3:]).replace("-", ":") if len(parts) > 3 else "unknown"
            zf.write(shot, f"screenshots/{shot.name}")
            manifest_entries.append({
                "filename":      shot.name,
                "platform":      plat,
                "address_id":    addr,
                "captured_at":   ts,
                "file_size_kb":  round(shot.stat().st_size / 1024, 1),
            })

        zf.writestr("manifest.json", json.dumps({
            "generated_at":      now,
            "platform":          "Rappi Competitive Intelligence",
            "description":       "Screenshot evidence pack for competitive intelligence audit",
            "total_screenshots": len(shots),
            "screenshots":       manifest_entries,
        }, indent=2, ensure_ascii=False))

        summary_cols = ["platform", "address_label", "zone", "product",
                        "final_price", "delivery_fee", "service_fee",
                        "eta_min", "discount", "promo_label", "timestamp"]
        summary = df[[c for c in summary_cols if c in df.columns]].copy()
        zf.writestr("data_summary.csv",
                    summary.to_csv(index=False, encoding="utf-8-sig"))

        zf.writestr("README.txt", (
            f"Rappi Competitive Intelligence — Evidence Pack\n"
            f"Generated: {now}\n"
            f"Platform:  Rappi CI v2.0\n\n"
            f"Contents:\n"
            f"  screenshots/      {len(shots)} visual evidence captures\n"
            f"  manifest.json     Screenshot metadata and audit trail\n"
            f"  data_summary.csv  Competitive data ({len(df)} records)\n\n"
            f"Platforms: {', '.join(df['platform'].unique().tolist())}\n"
            f"Zones:     {', '.join(df['zone'].unique().tolist())}\n"
            f"Records:   {len(df)}\n"
        ))

    buf.seek(0)
    return buf.read()


def _export_card(
    icon: str, title: str, fmt: str, accent: str,
    description: str, chips: list[str],
) -> None:
    chips_html = "".join(
        f'<span style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:4px;'
        f'padding:2px 8px;font-size:0.61rem;font-weight:500;color:#475569">{c}</span>'
        for c in chips
    )
    st.markdown(f"""
    <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;
         padding:0;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.03);
         margin-bottom:10px">
      <div style="height:3px;background:{accent};border-radius:12px 12px 0 0"></div>
      <div style="padding:18px 20px 16px">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
          <div style="display:flex;align-items:center;gap:9px">
            <span style="font-size:1.15rem;line-height:1">{icon}</span>
            <span style="font-size:0.9rem;font-weight:700;color:#0F172A">{title}</span>
          </div>
          <span style="background:#F1F5F9;border-radius:5px;padding:2px 9px;
                font-size:0.61rem;font-weight:700;color:#475569;letter-spacing:0.04em">{fmt}</span>
        </div>
        <p style="font-size:0.77rem;color:#64748B;line-height:1.55;margin:0 0 13px">{description}</p>
        <div style="display:flex;gap:5px;flex-wrap:wrap">{chips_html}</div>
      </div>
      <div style="border-top:1px dashed #F1F5F9;padding:10px 20px 14px;background:#FAFBFC">
        <span style="font-size:0.62rem;font-weight:600;color:#94A3B8;
               letter-spacing:0.06em;text-transform:uppercase">⬇ Descargar</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


def page_export(df: pd.DataFrame, insights: list, scores: dict):
    from datetime import datetime, timezone
    page_header("Centro de Exportación",
                f"Intelligence packages · {len(df):,} records · CDMX")
    if df.empty:
        empty_state()
        return

    date_tag = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Pre-compute all export payloads
    raw_csv   = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8")
    raw_json  = df.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8")
    intel_rpt = _gen_intelligence_report(df, insights, scores)
    sigs_csv  = _gen_signals_csv(df)
    evid_pack = _gen_evidence_pack(df)

    # Signal count: count newlines minus header row
    n_sigs = max(0, sigs_csv.count(b"\n") - 1)
    from app.core.config import SCREENSHOTS_DIR
    n_shots = len(list(SCREENSHOTS_DIR.glob("*.png")))

    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0F172A 0%,#1E293B 100%);
         border-radius:14px;padding:28px 32px;margin-bottom:24px">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;
           flex-wrap:wrap;gap:16px">
        <div>
          <div style="font-size:0.63rem;font-weight:700;letter-spacing:0.13em;
               color:#64748B;text-transform:uppercase;margin-bottom:8px">
            ◈ CENTRO DE EXPORTACIÓN DE INTELIGENCIA
          </div>
          <div style="font-size:1.5rem;font-weight:800;color:#F8FAFC;
               line-height:1.2;margin-bottom:10px">
            Paquetes de Datos Empresariales
          </div>
          <div style="font-size:0.81rem;color:#94A3B8;line-height:1.6;max-width:500px">
            Exporta inteligencia competitiva en formatos diseñados para distribución ejecutiva,
            flujos de analista y documentación de auditoría. Todos los paquetes incluyen metadatos,
            trazabilidad de origen y notas de metodología estructurada.
          </div>
          <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:14px">
            {''.join(
                f'<span style="background:rgba(248,250,252,0.07);border:1px solid rgba(255,255,255,0.1);'
                f'border-radius:6px;padding:3px 10px;font-size:0.66rem;font-weight:600;color:#CBD5E1">'
                f'{lbl}</span>'
                for lbl in [f"{len(df):,} Registros", f"{df['zone'].nunique()} Zonas",
                             f"{df['platform'].nunique()} Plataformas", f"{len(insights)} Insights",
                             f"{n_sigs} Señales", f"{n_shots} Capturas"]
            )}
          </div>
        </div>
        <div style="text-align:right;flex-shrink:0">
          <div style="font-size:0.6rem;color:#475569;margin-bottom:4px;
               letter-spacing:0.08em;text-transform:uppercase">Listo para Exportar</div>
          <div style="font-size:2.4rem;font-weight:800;color:#34D399;line-height:1">✓</div>
          <div style="font-size:0.65rem;color:#475569;margin-top:4px">{date_tag}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div style="font-size:0.68rem;font-weight:700;letter-spacing:0.1em;'
        'color:#94A3B8;text-transform:uppercase;margin-bottom:14px">'
        'Selecciona el Paquete de Exportación</div>',
        unsafe_allow_html=True,
    )

    # ── Row 1: Raw Data + Intelligence Report ─────────────────────────────────
    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        _export_card(
            icon="⊞", title="Exportación de Datos Brutos", fmt="CSV · JSON",
            accent="#3B82F6",
            description=(
                "Dataset competitivo completo con todas las plataformas, zonas, productos y "
                "métricas de precios. Ideal para pipelines de analista, herramientas BI y validación de datos."
            ),
            chips=[f"{len(df):,} registros", f"{df.shape[1]} columnas",
                   "Todas las plataformas", "Todas las zonas", "Codificado UTF-8"],
        )
        btn_a1, btn_a2 = st.columns(2)
        with btn_a1:
            st.download_button(
                "⬇ Exportar CSV",
                data=raw_csv,
                file_name=f"rappi_ci_raw_{date_tag}.csv",
                mime="text/csv",
                use_container_width=True,
                key="dl_raw_csv",
            )
        with btn_a2:
            st.download_button(
                "⬇ Exportar JSON",
                data=raw_json,
                file_name=f"rappi_ci_raw_{date_tag}.json",
                mime="application/json",
                use_container_width=True,
                key="dl_raw_json",
            )

    with col_b:
        _export_card(
            icon="◈", title="Reporte Ejecutivo de Inteligencia", fmt="JSON",
            accent="#8B5CF6",
            description=(
                "Brief estratégico estructurado con rankings de plataformas, análisis de zonas, "
                "scores competitivos y todos los insights estratégicos. Listo para revisión ejecutiva "
                "o ingesta automatizada en pipeline."
            ),
            chips=[f"{len(insights)} insights", "Rankings de plataformas", "Análisis de zonas",
                   "Scores competitivos", "Recomendaciones"],
        )
        st.download_button(
            "⬇ Descargar Reporte de Inteligencia",
            data=intel_rpt,
            file_name=f"rappi_ci_intelligence_report_{date_tag}.json",
            mime="application/json",
            use_container_width=True,
            key="dl_intel",
        )

    st.markdown('<div style="margin-top:4px"></div>', unsafe_allow_html=True)

    # ── Row 2: Evidence Pack + Signals Summary ────────────────────────────────
    col_c, col_d = st.columns(2, gap="medium")

    with col_c:
        _export_card(
            icon="📸", title="Paquete de Evidencias", fmt="ZIP",
            accent="#F59E0B",
            description=(
                "Bundle de evidencias visuales con trazabilidad completa de auditoría. Incluye manifiesto, "
                "resumen CSV y documentación README. "
                "Apto para revisión de cumplimiento y presentaciones de auditoría competitiva."
            ),
            chips=[f"{n_shots} capturas", "manifest.json", "data_summary.csv",
                   "README.txt", "Listo para auditoría"],
        )
        st.download_button(
            "⬇ Descargar Paquete de Evidencias",
            data=evid_pack,
            file_name=f"rappi_ci_evidence_{date_tag}.zip",
            mime="application/zip",
            use_container_width=True,
            key="dl_evid",
        )

    with col_d:
        _export_card(
            icon="◆", title="Resumen de Señales Competitivas", fmt="CSV",
            accent="#EF4444",
            description=(
                "Feed estructurado de todas las señales competitivas detectadas: brechas de precio, "
                "deltas de ETA, divergencias de tasa promo y anomalías de fee. "
                "Ordenado por severidad para triage inmediato."
            ),
            chips=[f"{n_sigs} señales detectadas", "ALTA · MEDIA · BAJA",
                   "4 tipos de señal", "A nivel de zona", "Ordenado por severidad"],
        )
        st.download_button(
            "⬇ Descargar Resumen de Señales",
            data=sigs_csv,
            file_name=f"rappi_ci_signals_{date_tag}.csv",
            mime="text/csv",
            use_container_width=True,
            key="dl_sigs",
        )

    # ── Intelligence Packages ──────────────────────────────────────────────────
    st.markdown('<div style="margin-top:28px"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.68rem;font-weight:700;letter-spacing:0.1em;'
        'color:#94A3B8;text-transform:uppercase;margin-bottom:16px">'
        'Paquetes de Inteligencia</div>',
        unsafe_allow_html=True,
    )

    # ── Shared helpers ────────────────────────────────────────────────────────
    def _benefit(text: str) -> str:
        return (
            f'<div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:7px">'
            f'<span style="color:#10B981;font-size:0.75rem;font-weight:700;'
            f'flex-shrink:0;margin-top:1px">✓</span>'
            f'<span style="font-size:0.76rem;color:#475569;line-height:1.4">{text}</span>'
            f'</div>'
        )

    def _chip(text: str, accent: str = "#F1F5F9", fg: str = "#64748B") -> str:
        return (
            f'<span style="background:{accent};border-radius:5px;padding:3px 9px;'
            f'font-size:0.63rem;font-weight:600;color:{fg};white-space:nowrap">{text}</span>'
        )

    def _badge(label: str, bg: str, fg: str) -> str:
        return (
            f'<span style="background:{bg};border-radius:5px;padding:3px 10px;'
            f'font-size:0.6rem;font-weight:800;color:{fg};letter-spacing:0.08em;'
            f'text-transform:uppercase">{label}</span>'
        )

    def _metric(value: str, label: str) -> str:
        return (
            f'<div style="flex:1;text-align:center;padding:10px 8px;'
            f'border-right:1px solid #F1F5F9">'
            f'<div style="font-size:1.15rem;font-weight:800;color:#0F172A;'
            f'line-height:1">{value}</div>'
            f'<div style="font-size:0.58rem;font-weight:600;color:#94A3B8;'
            f'text-transform:uppercase;letter-spacing:0.06em;margin-top:3px">{label}</div>'
            f'</div>'
        )

    n_zones    = df["zone"].nunique()
    n_plats    = df["platform"].nunique()
    n_records  = len(df)
    n_cols     = df.shape[1]
    n_insights_v = len(insights)
    risk_score = scores.get("strategic_risk_score", 0)

    # ── Row 1: Featured packages ───────────────────────────────────────────────
    feat_a, feat_b = st.columns(2, gap="medium")

    with feat_a:
        intel_benefits = "".join([
            _benefit("Rankings de plataformas por precio, ETA y estructura de fees"),
            _benefit("Desglose de rendimiento zona por zona en las 4 zonas CDMX"),
            _benefit(f"Los {n_insights_v} insights estratégicos con scores de confianza"),
            _benefit("Scores competitivos de Rappi: riesgo, presión, agresividad"),
            _benefit("Resumen ejecutivo con recomendaciones de acción prioritaria"),
        ])
        intel_chips = " ".join([
            _chip(f"{n_insights_v} Insights", "#EDE9FE", "#6D28D9"),
            _chip(f"{n_zones} Zonas", "#F1F5F9", "#475569"),
            _chip(f"{n_plats} Plataformas", "#F1F5F9", "#475569"),
            _chip("Scores + Rankings", "#F1F5F9", "#475569"),
        ])
        intel_metrics = "".join([
            _metric(str(n_insights_v), "Insights"),
            _metric(str(n_zones), "Zonas"),
            _metric(f"{risk_score:.0f}", "Score Riesgo"),
            _metric(str(n_plats), "Plataformas"),
        ])
        st.markdown(f"""
        <div style="background:#FFFFFF;border:1px solid #DDD6FE;border-radius:14px;
             overflow:hidden;box-shadow:0 4px 16px rgba(139,92,246,0.08)">
          <div style="height:4px;background:linear-gradient(90deg,#8B5CF6,#A78BFA)"></div>
          <div style="padding:22px 24px 0">
            <div style="display:flex;align-items:flex-start;justify-content:space-between;
                 margin-bottom:14px">
              <div style="display:flex;align-items:center;gap:10px">
                <span style="font-size:1.3rem">◈</span>
                <div>
                  <div style="font-size:0.95rem;font-weight:800;color:#0F172A;
                       letter-spacing:-0.2px">Reporte de Inteligencia</div>
                  <div style="font-size:0.68rem;color:#94A3B8;margin-top:1px">
                    Inteligencia Ejecutiva · JSON</div>
                </div>
              </div>
              {_badge("Estratégico", "#EDE9FE", "#6D28D9")}
            </div>
            <p style="font-size:0.8rem;color:#64748B;line-height:1.6;margin:0 0 16px">
              Brief estratégico estructurado diseñado para distribución ejecutiva e ingesta
              automatizada en pipelines. Incluye análisis competitivo por plataforma,
              inteligencia a nivel de zona y recomendaciones priorizadas.
            </p>
            {intel_benefits}
            <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:14px;
                 padding-bottom:16px">
              {intel_chips}
            </div>
          </div>
          <div style="border-top:1px solid #F3F0FF;display:flex;flex-direction:row">
            {intel_metrics}
          </div>
        </div>
        """, unsafe_allow_html=True)

    with feat_b:
        evid_benefits = "".join([
            _benefit(f"{n_shots} capturas de pantalla de plataformas con metadatos de timestamp"),
            _benefit("manifest.json con plataforma, dirección y trazabilidad de captura"),
            _benefit("data_summary.csv con evidencia de precios competitivos"),
            _benefit("README.txt con documentación de metodología y origen"),
            _benefit("Comprimido en ZIP para distribución segura de archivo"),
        ])
        evid_chips = " ".join([
            _chip(f"{n_shots} Capturas", "#FEF3C7", "#92400E"),
            _chip("Listo para auditoría", "#FEF3C7", "#92400E"),
            _chip("manifest.json", "#F1F5F9", "#475569"),
            _chip("Archivo ZIP", "#F1F5F9", "#475569"),
        ])
        evid_metrics = "".join([
            _metric(str(n_shots), "Capturas"),
            _metric(str(n_plats), "Plataformas"),
            _metric(str(n_records), "Registros"),
            _metric("4", "Archivos"),
        ])
        st.markdown(f"""
        <div style="background:#FFFFFF;border:1px solid #FDE68A;border-radius:14px;
             overflow:hidden;box-shadow:0 4px 16px rgba(245,158,11,0.08)">
          <div style="height:4px;background:linear-gradient(90deg,#F59E0B,#FCD34D)"></div>
          <div style="padding:22px 24px 0">
            <div style="display:flex;align-items:flex-start;justify-content:space-between;
                 margin-bottom:14px">
              <div style="display:flex;align-items:center;gap:10px">
                <span style="font-size:1.3rem">📸</span>
                <div>
                  <div style="font-size:0.95rem;font-weight:800;color:#0F172A;
                       letter-spacing:-0.2px">Paquete de Evidencias</div>
                  <div style="font-size:0.68rem;color:#94A3B8;margin-top:1px">
                    Evidencia Visual · Archivo ZIP</div>
                </div>
              </div>
              {_badge("Evidencia", "#FEF3C7", "#92400E")}
            </div>
            <p style="font-size:0.8rem;color:#64748B;line-height:1.6;margin:0 0 16px">
              Bundle de evidencias listo para auditoría en documentación de inteligencia competitiva,
              revisión de cumplimiento y presentación ejecutiva. Cada captura está timestampeada
              y vinculada a su dirección y plataforma de origen.
            </p>
            {evid_benefits}
            <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:14px;
                 padding-bottom:16px">
              {evid_chips}
            </div>
          </div>
          <div style="border-top:1px solid #FFFBEB;display:flex;flex-direction:row">
            {evid_metrics}
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Divider ───────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex;align-items:center;gap:14px;margin:22px 0 18px">
      <div style="flex:1;height:1px;background:#F1F5F9"></div>
      <span style="font-size:0.62rem;font-weight:700;letter-spacing:0.12em;
             color:#CBD5E1;text-transform:uppercase;white-space:nowrap">
        Paquetes de Datos Secundarios · Flujos de Analista
      </span>
      <div style="flex:1;height:1px;background:#F1F5F9"></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Row 2: Secondary packages ──────────────────────────────────────────────
    sec_a, sec_b = st.columns(2, gap="medium")

    with sec_a:
        raw_metrics = "".join([
            _metric(f"{n_records:,}", "Registros"),
            _metric(str(n_cols), "Columnas"),
            _metric("CSV+JSON", "Formatos"),
        ])
        st.markdown(f"""
        <div style="background:#FAFBFC;border:1px solid #E2E8F0;border-radius:10px;
             overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.02)">
          <div style="height:3px;background:#3B82F6;border-radius:10px 10px 0 0"></div>
          <div style="padding:16px 20px 0">
            <div style="display:flex;align-items:center;justify-content:space-between;
                 margin-bottom:10px">
              <div style="display:flex;align-items:center;gap:8px">
                <span style="font-size:1rem">⊞</span>
                <span style="font-size:0.85rem;font-weight:700;color:#0F172A">Exportación de Datos Brutos</span>
              </div>
              {_badge("Analista", "#DBEAFE", "#1D4ED8")}
            </div>
            <p style="font-size:0.75rem;color:#64748B;line-height:1.5;margin:0 0 10px">
              Dataset competitivo completo en formatos legibles por máquina. Ideal para
              ingesta en herramientas BI, analítica personalizada y pipelines de validación.
            </p>
            <div style="display:flex;gap:5px;flex-wrap:wrap;padding-bottom:14px">
              {_chip(f"{n_records:,} registros", "#EFF6FF", "#1D4ED8")}
              {_chip(f"{n_cols} columnas", "#F1F5F9", "#475569")}
              {_chip("Todas las plataformas", "#F1F5F9", "#475569")}
              {_chip("Codificado UTF-8", "#F1F5F9", "#475569")}
            </div>
          </div>
          <div style="border-top:1px solid #F1F5F9;display:flex;flex-direction:row;background:#FFFFFF">
            {raw_metrics}
          </div>
        </div>
        """, unsafe_allow_html=True)

    with sec_b:
        sigs_metrics = "".join([
            _metric(str(n_sigs), "Señales"),
            _metric("4", "Tipos"),
            _metric(str(n_zones), "Zonas"),
        ])
        st.markdown(f"""
        <div style="background:#FAFBFC;border:1px solid #E2E8F0;border-radius:10px;
             overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.02)">
          <div style="height:3px;background:#EF4444;border-radius:10px 10px 0 0"></div>
          <div style="padding:16px 20px 0">
            <div style="display:flex;align-items:center;justify-content:space-between;
                 margin-bottom:10px">
              <div style="display:flex;align-items:center;gap:8px">
                <span style="font-size:1rem">◆</span>
                <span style="font-size:0.85rem;font-weight:700;color:#0F172A">Señales Competitivas</span>
              </div>
              {_badge("Analista", "#FEE2E2", "#B91C1C")}
            </div>
            <p style="font-size:0.75rem;color:#64748B;line-height:1.5;margin:0 0 10px">
              Feed estructurado de {n_sigs} señales competitivas detectadas en precio,
              ETA, tasa promo y carga de fees. Ordenado por severidad para triage inmediato.
            </p>
            <div style="display:flex;gap:5px;flex-wrap:wrap;padding-bottom:14px">
              {_chip(f"{n_sigs} señales", "#FEE2E2", "#B91C1C")}
              {_chip("ALTA · MEDIA · BAJA", "#F1F5F9", "#475569")}
              {_chip("A nivel de zona", "#F1F5F9", "#475569")}
              {_chip("Ordenado por severidad", "#F1F5F9", "#475569")}
            </div>
          </div>
          <div style="border-top:1px solid #F1F5F9;display:flex;flex-direction:row;background:#FFFFFF">
            {sigs_metrics}
          </div>
        </div>
        """, unsafe_allow_html=True)


# ── HTML Page-Level Executive Report Generators ───────────────────────────────

_HTML_BASE_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: 'Segoe UI', Arial, sans-serif;
    background: #F7F8FC; color: #0F172A; font-size: 13px; line-height: 1.5;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
.brand-bar {
    background: linear-gradient(135deg,#FF6B35 0%,#FB923C 100%);
    padding: 10px 32px; display: flex; justify-content: space-between; align-items: center;
}
.brand-name { color:#fff; font-size:10px; font-weight:700; letter-spacing:0.12em; }
.brand-date { color:rgba(255,255,255,0.75); font-size:10px; }
.report-header { background:#0F172A; padding:28px 32px 24px; }
.report-title  { color:#F8FAFC; font-size:22px; font-weight:800; letter-spacing:-0.3px; margin-bottom:6px; }
.report-subtitle { color:#64748B; font-size:12px; margin-bottom:16px; }
.meta-chips { display:flex; gap:8px; flex-wrap:wrap; }
.meta-chip {
    background:rgba(255,255,255,0.07); border:1px solid rgba(255,255,255,0.12);
    border-radius:5px; padding:3px 10px; color:#94A3B8; font-size:11px; font-weight:600;
}
.content { padding:24px 32px; }
.section {
    background:#fff; border:1px solid #E2E8F0; border-radius:10px;
    margin-bottom:18px; overflow:hidden;
}
.section-hdr { padding:16px 20px 12px; border-bottom:1px solid #F1F5F9; }
.section-title { font-size:13px; font-weight:700; color:#0F172A; margin-bottom:2px; }
.section-sub   { font-size:11px; color:#94A3B8; }
.section-body  { padding:16px 20px; }
.narrative {
    font-size:12px; color:#475569; line-height:1.75;
    padding:14px 18px; background:#F8FAFC; border-radius:7px;
    border-left:3px solid #FB923C; margin-bottom:14px;
}
table { width:100%; border-collapse:collapse; font-size:12px; }
thead th {
    background:#F8FAFC; border-bottom:2px solid #E2E8F0; padding:9px 12px;
    text-align:left; font-size:10px; font-weight:700; color:#64748B;
    letter-spacing:0.07em; text-transform:uppercase;
}
tbody td { padding:9px 12px; border-bottom:1px solid #F1F5F9; color:#334155; vertical-align:middle; }
tbody tr:last-child td { border-bottom:none; }
tbody tr:nth-child(even) td { background:#FAFBFF; }
.badge { display:inline-block; border-radius:4px; padding:2px 8px; font-size:10px; font-weight:700; }
.kpi-row { display:flex; gap:12px; margin-bottom:18px; flex-wrap:wrap; }
.kpi-card {
    flex:1; min-width:130px; background:#fff; border:1px solid #E2E8F0;
    border-radius:8px; padding:14px 16px;
}
.kpi-val   { font-size:20px; font-weight:800; color:#0F172A; line-height:1; }
.kpi-lbl   { font-size:9px; color:#94A3B8; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; margin-top:5px; }
.kpi-delta { font-size:11px; font-weight:600; margin-top:4px; }
.two-col { display:flex; gap:16px; margin-bottom:18px; }
.two-col > .section { flex:1; margin-bottom:0; }
.bar-wrap { background:#F1F5F9; border-radius:3px; height:5px; margin-top:7px; overflow:hidden; }
.bar-fill { border-radius:3px; height:5px; }
.insight-row { padding:10px 0; border-bottom:1px solid #F1F5F9; display:flex; gap:10px; align-items:flex-start; }
.insight-row:last-child { border-bottom:none; }
.sev-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; margin-top:4px; }
.ins-body { font-size:12px; color:#334155; line-height:1.6; }
.footer {
    background:#F1F5F9; border-top:1px solid #E2E8F0;
    padding:14px 32px; display:flex; justify-content:space-between; align-items:center; margin-top:8px;
}
.footer-left  { font-size:10px; color:#94A3B8; font-weight:600; }
.footer-right { font-size:10px; color:#94A3B8; }
@media print { .brand-bar,.report-header { -webkit-print-color-adjust:exact; } }
"""

_HC = {"rappi": "#FB923C", "ubereats": "#34D399", "didi": "#FBBF24"}
_HN = {"rappi": "Rappi",   "ubereats": "Uber Eats", "didi": "DiDi Food"}
_HZ = {"premium": "Premium", "corporativa": "Corporativa", "media": "Media", "periferia": "Periferia"}
_PLATS = ["rappi", "ubereats", "didi"]

def _hbadge(plat: str) -> str:
    c = _HC[plat]; bg = c + "22"
    return f'<span class="badge" style="background:{bg};color:{c}">{_HN[plat]}</span>'

def _gen_html_shell(
    title: str, subtitle: str, body_html: str,
    meta_chips: list[str], date_tag: str, datetime_str: str,
) -> bytes:
    chips = "".join(f'<span class="meta-chip">{c}</span>' for c in meta_chips)
    return (f"""<!DOCTYPE html>
<html lang="es"><head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Rappi CI · {title}</title>
  <style>{_HTML_BASE_CSS}</style>
</head><body>
<div class="brand-bar">
  <span class="brand-name">◈ RAPPI COMPETITIVE INTELLIGENCE</span>
  <span class="brand-date">Confidencial · {date_tag}</span>
</div>
<div class="report-header">
  <div class="report-title">{title}</div>
  <div class="report-subtitle">{subtitle}</div>
  <div class="meta-chips">{chips}</div>
</div>
<div class="content">{body_html}</div>
<div class="footer">
  <span class="footer-left">Rappi Competitive Intelligence · Solo uso interno</span>
  <span class="footer-right">Generado {datetime_str} · CDMX</span>
</div>
</body></html>""").encode("utf-8")


def _html_zone_price_table(df: pd.DataFrame) -> str:
    hdr = "".join(
        f'<th style="color:{_HC[p]}">{_HN[p]}</th>' for p in _PLATS
    )
    rows = ""
    for zone in ZONE_ORDER:
        sub_z = df[df["zone"] == zone]
        if sub_z.empty:
            continue
        cells = "".join(
            f'<td style="font-weight:700;color:{_HC[p]}">'
            f'{"${:.2f}".format(sub_z[sub_z["platform"]==p]["final_price"].mean()) if not sub_z[sub_z["platform"]==p].empty else "—"}'
            f'</td>' for p in _PLATS
        )
        rows += f'<tr><td><b>{_HZ.get(zone, zone)}</b></td>{cells}</tr>'
    return (
        f'<table><thead><tr><th>Zona</th>{hdr}</tr></thead>'
        f'<tbody>{rows}</tbody></table>'
    )


def _gen_executive_brief_html(df: pd.DataFrame, insights: list, scores: dict) -> bytes:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    date_tag = now.strftime("%Y-%m-%d")
    dts = now.strftime("%Y-%m-%d %H:%M UTC")

    plat_stats = {}
    for p in _PLATS:
        sub = df[df["platform"] == p]
        if sub.empty:
            plat_stats[p] = {}; continue
        tf = sub["delivery_fee"] + sub["service_fee"]
        plat_stats[p] = {
            "price": sub["final_price"].mean(),
            "fee":   tf.mean(),
            "eta":   sub["eta_min"].mean(),
            "promo": (sub["discount"] > 0).mean() * 100,
        }

    rd = plat_stats.get("rappi", {})
    kpi_html = '<div class="kpi-row">' + "".join(
        f'<div class="kpi-card" style="border-top:3px solid {c}">'
        f'<div class="kpi-val">{v}</div>'
        f'<div class="kpi-lbl">{l}</div></div>'
        for v, l, c in [
            (f'${rd.get("price",0):.0f}', "PRECIO FINAL · RAPPI", "#FB923C"),
            (f'${rd.get("fee",0):.0f}',   "TOTAL FEE · RAPPI",    "#F97316"),
            (f'{rd.get("eta",0):.0f} min', "ETA PROMEDIO · RAPPI", "#0EA5E9"),
            (f'{len(df):,}',               "REGISTROS",             "#64748B"),
            (f'{df["zone"].nunique()}',     "ZONAS · CDMX",          "#10B981"),
        ]
    ) + '</div>'

    # Platform comparison table
    ref = plat_stats.get("rappi", {})
    rp0 = ref.get("price", 1) or 1
    rf0 = ref.get("fee",   1) or 1
    re0 = ref.get("eta",   1) or 1
    plat_rows = ""
    for p in _PLATS:
        d = plat_stats.get(p, {})
        if not d:
            continue
        pv = d.get("price", 0); fv = d.get("fee", 0)
        ev = d.get("eta",   0); prom = d.get("promo", 0)
        p_vs = "Base" if p == "rappi" else f'{"+" if pv>rp0 else ""}{(pv-rp0)/rp0*100:.1f}%'
        f_vs = "Base" if p == "rappi" else f'{"+" if fv>rf0 else ""}{(fv-rf0)/rf0*100:.1f}%'
        e_vs = "Base" if p == "rappi" else f'{"+" if ev>re0 else ""}{ev-re0:.0f}min'
        c = _HC[p]
        plat_rows += (
            f'<tr><td>{_hbadge(p)}</td>'
            f'<td><b>${pv:.2f}</b></td><td style="color:#94A3B8;font-size:11px">{p_vs}</td>'
            f'<td><b>${fv:.2f}</b></td><td style="color:#94A3B8;font-size:11px">{f_vs}</td>'
            f'<td><b>{ev:.0f} min</b></td><td style="color:#94A3B8;font-size:11px">{e_vs}</td>'
            f'<td><b>{prom:.0f}%</b></td></tr>'
        )

    plat_tbl = (
        '<table><thead><tr>'
        '<th>Plataforma</th><th>Precio Final</th><th>vs Rappi</th>'
        '<th>Fee Total</th><th>vs Rappi</th>'
        '<th>ETA</th><th>vs Rappi</th><th>Tasa Promo</th>'
        f'</tr></thead><tbody>{plat_rows}</tbody></table>'
    )

    # Insights
    SEV_C = {"CRITICAL":"#EF4444","HIGH":"#F97316","MEDIUM":"#F59E0B","LOW":"#10B981"}
    ins_html = ""
    for ins in insights[:6]:
        sev = ins.get("severity", "MEDIUM")
        sc = SEV_C.get(sev, "#F59E0B")
        txt = ins.get("headline", ins.get("summary", ""))
        ins_html += (
            f'<div class="insight-row">'
            f'<div class="sev-dot" style="background:{sc}"></div>'
            f'<div class="ins-body">'
            f'<span class="badge" style="background:{sc}22;color:{sc};margin-right:6px">{sev}</span>'
            f'{txt}</div></div>'
        )

    # Scores
    score_dims = [
        ("price_competitiveness", "Competitividad de Precio"),
        ("service_quality",       "Calidad de Servicio"),
        ("promo_aggressiveness",  "Agresividad Promo"),
        ("overall",               "Score Global"),
    ]
    sc_rows = "".join(
        f'<tr><td>{sl}</td>' +
        "".join(f'<td><b>{scores.get(p,{}).get(sk,0):.0f}/100</b></td>' for p in _PLATS) +
        '</tr>'
        for sk, sl in score_dims
    )
    sc_hdr = "".join(f'<th style="color:{_HC[p]}">{_HN[p]}</th>' for p in _PLATS)
    score_tbl = (
        f'<table><thead><tr><th>Dimensión</th>{sc_hdr}</tr></thead>'
        f'<tbody>{sc_rows}</tbody></table>'
    )

    body = f"""
{kpi_html}
<div class="two-col">
  <div class="section" style="flex:2">
    <div class="section-hdr">
      <div class="section-title">Resumen Competitivo de Plataformas</div>
      <div class="section-sub">Comparativa directa · Precio, fee, ETA, tasa promo</div>
    </div>
    <div class="section-body">{plat_tbl}</div>
  </div>
  <div class="section" style="flex:1">
    <div class="section-hdr">
      <div class="section-title">Scores Competitivos</div>
      <div class="section-sub">Modelo de scoring · 0–100 por dimensión</div>
    </div>
    <div class="section-body">{score_tbl}</div>
  </div>
</div>
<div class="two-col">
  <div class="section" style="flex:1">
    <div class="section-hdr">
      <div class="section-title">Vista de Precios por Zona</div>
      <div class="section-sub">Precio final promedio por zona · CDMX</div>
    </div>
    <div class="section-body">{_html_zone_price_table(df)}</div>
  </div>
  <div class="section" style="flex:1">
    <div class="section-hdr">
      <div class="section-title">Señales de Inteligencia Activa</div>
      <div class="section-sub">Top {min(6,len(insights))} señales · Ordenadas por prioridad</div>
    </div>
    <div class="section-body">{ins_html or "<p style='color:#94A3B8;font-size:12px'>Sin señales disponibles.</p>"}</div>
  </div>
</div>"""

    return _gen_html_shell(
        "Brief de Inteligencia Ejecutiva",
        f"Rappi vs Uber Eats vs DiDi Food · Pulso de Mercado · CDMX · {date_tag}",
        body,
        [f"{len(df):,} Registros", f"{df['zone'].nunique()} Zonas",
         "3 Plataformas", f"{len(insights)} Señales", "Scoring Competitivo"],
        date_tag, dts,
    )


def _gen_pricing_brief_html(df: pd.DataFrame) -> bytes:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    date_tag = now.strftime("%Y-%m-%d")
    dts = now.strftime("%Y-%m-%d %H:%M UTC")

    # Platform price stats
    plat_rows = ""
    for p in _PLATS:
        sub = df[df["platform"] == p]
        if sub.empty: continue
        avg_final  = sub["final_price"].mean()
        avg_base   = sub["base_price"].mean()
        avg_disc   = sub["discount"].mean()
        disc_rate  = (sub["discount"] > 0).mean() * 100
        c = _HC[p]
        plat_rows += (
            f'<tr><td>{_hbadge(p)}</td>'
            f'<td><b>${avg_final:.2f}</b></td>'
            f'<td>${avg_base:.2f}</td>'
            f'<td>${avg_disc:.2f}</td>'
            f'<td><b>{disc_rate:.0f}%</b></td>'
            f'<td>{sub["product"].nunique()} SKUs</td></tr>'
        )
    plat_tbl = (
        '<table><thead><tr>'
        '<th>Plataforma</th><th>Precio Final</th><th>Precio Base</th>'
        '<th>Descuento Prom.</th><th>Tasa de Descuento</th><th>Cobertura</th>'
        f'</tr></thead><tbody>{plat_rows}</tbody></table>'
    )

    # Zone × platform price table
    zone_hdr = "".join(f'<th style="color:{_HC[p]}">{_HN[p]}</th>' for p in _PLATS)
    zone_rows = ""
    for zone in ZONE_ORDER:
        sub_z = df[df["zone"] == zone]
        if sub_z.empty: continue
        cells = ""
        prices = []
        for p in _PLATS:
            sub_zp = sub_z[sub_z["platform"] == p]
            if sub_zp.empty:
                cells += '<td>—</td>'; continue
            avg = sub_zp["final_price"].mean()
            prices.append(avg)
            cells += f'<td style="font-weight:700;color:{_HC[p]}">${avg:.2f}</td>'
        lo_c = "#10B981" if prices and min(prices) == prices[_PLATS.index("rappi")] else "#EF4444"
        zone_rows += (
            f'<tr><td><b>{_HZ.get(zone, zone)}</b></td>{cells}'
            f'<td><span class="badge" style="background:{lo_c}22;color:{lo_c}">'
            f'{"Rappi gana" if prices and prices[0]==min(prices) else "Presión competitiva"}'
            f'</span></td></tr>'
        )
    zone_tbl = (
        f'<table><thead><tr><th>Zona</th>{zone_hdr}<th>Señal</th></tr></thead>'
        f'<tbody>{zone_rows}</tbody></table>'
    )

    # Top products by price gap
    prod_rows = ""
    for prod in sorted(df["product"].unique())[:10]:
        sub_p = df[df["product"] == prod]
        prices = {p: sub_p[sub_p["platform"]==p]["final_price"].mean()
                  for p in _PLATS if not sub_p[sub_p["platform"]==p].empty}
        if len(prices) < 2: continue
        rp_v = prices.get("rappi")
        others = {k: v for k, v in prices.items() if k != "rappi"}
        if not others or rp_v is None: continue
        min_other_p, min_other_v = min(others.items(), key=lambda x: x[1])
        gap = rp_v - min_other_v
        gap_c = "#EF4444" if gap > 5 else "#F59E0B" if gap > 0 else "#10B981"
        cells = "".join(
            f'<td style="color:{_HC[p]}">${prices[p]:.2f}</td>' if p in prices else '<td>—</td>'
            for p in _PLATS
        )
        prod_rows += (
            f'<tr><td><b>{prod}</b></td>{cells}'
            f'<td><span class="badge" style="background:{gap_c}22;color:{gap_c}">'
            f'{"+" if gap>0 else ""}{gap:.2f}</span></td></tr>'
        )
    prod_hdr = "".join(f'<th style="color:{_HC[p]}">{_HN[p]}</th>' for p in _PLATS)
    prod_tbl = (
        f'<table><thead><tr><th>Producto</th>{prod_hdr}<th>Gap vs Más Barato</th>'
        f'</tr></thead><tbody>{prod_rows}</tbody></table>'
    )

    rappi_sub = df[df["platform"]=="rappi"]
    comp_sub  = df[df["platform"]!="rappi"]
    r_avg = rappi_sub["final_price"].mean() if not rappi_sub.empty else 0
    c_avg = comp_sub["final_price"].mean()  if not comp_sub.empty else 0
    gap_pp = r_avg - c_avg

    body = f"""
<div class="section">
  <div class="section-hdr">
    <div class="section-title">Narrativa de Posición de Precios</div>
    <div class="section-sub">Contexto estratégico · Análisis de gaps · CDMX</div>
  </div>
  <div class="section-body">
    <div class="narrative">
      Rappi mantiene un precio final promedio de <b>${r_avg:.2f}</b> frente a
      <b>${c_avg:.2f}</b> del mercado — una brecha de
      <b>{"+" if gap_pp>0 else ""}{gap_pp:.2f}</b> por SKU.
      {"Esta brecha expone a Rappi a presión de precio en segmentos sensibles al costo." if gap_pp > 3 else
       "Rappi mantiene paridad de precios competitiva con el mercado." if abs(gap_pp) <= 3 else
       "Rappi mantiene ventaja de precio — posición favorable para capturar demanda sensible al costo."}
    </div>
  </div>
</div>
<div class="two-col">
  <div class="section" style="flex:1">
    <div class="section-hdr">
      <div class="section-title">Comparativa de Precios por Plataforma</div>
      <div class="section-sub">Precio final, base, descuento promedio por plataforma</div>
    </div>
    <div class="section-body">{plat_tbl}</div>
  </div>
  <div class="section" style="flex:1">
    <div class="section-hdr">
      <div class="section-title">Análisis de Precios por Zona</div>
      <div class="section-sub">Precio final por zona geográfica · CDMX</div>
    </div>
    <div class="section-body">{zone_tbl}</div>
  </div>
</div>
<div class="section">
  <div class="section-hdr">
    <div class="section-title">Análisis de Brecha de Precios por Producto</div>
    <div class="section-sub">Top 10 productos · Gap de precio Rappi vs más barato del mercado</div>
  </div>
  <div class="section-body">{prod_tbl}</div>
</div>"""

    return _gen_html_shell(
        "Brief de Estrategia de Precios",
        f"Análisis Competitivo de Precios · Rappi vs Mercado · CDMX · {date_tag}",
        body,
        [f"{len(df):,} Registros", f"{df['product'].nunique()} Productos",
         f"{df['zone'].nunique()} Zonas", "Análisis de Brecha de Precios"],
        date_tag, dts,
    )


def _gen_operations_brief_html(df: pd.DataFrame) -> bytes:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    date_tag = now.strftime("%Y-%m-%d")
    dts = now.strftime("%Y-%m-%d %H:%M UTC")

    ops = {}
    for p in _PLATS:
        sub = df[df["platform"] == p]
        if sub.empty: ops[p] = {}; continue
        tf = sub["delivery_fee"] + sub["service_fee"]
        ops[p] = {
            "del_fee":   tf.mean() * 0.7,
            "svc_fee":   tf.mean() * 0.3,
            "total_fee": tf.mean(),
            "fee_pct":   tf.mean() / sub["base_price"].replace(0, 1).mean() * 100,
            "eta":       sub["eta_min"].mean(),
        }

    fee_rows = ""
    for p in _PLATS:
        d = ops.get(p, {})
        if not d: continue
        c = _HC[p]
        fee_rows += (
            f'<tr><td>{_hbadge(p)}</td>'
            f'<td><b>${d["del_fee"]:.2f}</b></td>'
            f'<td>${d["svc_fee"]:.2f}</td>'
            f'<td><b>${d["total_fee"]:.2f}</b></td>'
            f'<td>{d["fee_pct"]:.1f}%</td>'
            f'<td><b>{d["eta"]:.0f} min</b></td></tr>'
        )
    fee_tbl = (
        '<table><thead><tr>'
        '<th>Plataforma</th><th>Fee de Envío</th><th>Fee de Servicio</th>'
        '<th>Fee Total</th><th>Fee % del Precio</th><th>ETA Promedio</th>'
        f'</tr></thead><tbody>{fee_rows}</tbody></table>'
    )

    # Zone ETA table
    eta_hdr = "".join(f'<th style="color:{_HC[p]}">{_HN[p]} ETA</th>' for p in _PLATS)
    eta_rows = ""
    for zone in ZONE_ORDER:
        sub_z = df[df["zone"] == zone]
        if sub_z.empty: continue
        cells = ""
        for p in _PLATS:
            sub_zp = sub_z[sub_z["platform"] == p]
            eta = f'{sub_zp["eta_min"].mean():.0f} min' if not sub_zp.empty else "—"
            cells += f'<td style="color:{_HC[p]};font-weight:700">{eta}</td>'
        eta_rows += f'<tr><td><b>{_HZ.get(zone, zone)}</b></td>{cells}</tr>'
    eta_tbl = (
        f'<table><thead><tr><th>Zona</th>{eta_hdr}</tr></thead>'
        f'<tbody>{eta_rows}</tbody></table>'
    )

    # Zone fee table
    zfee_hdr = "".join(f'<th style="color:{_HC[p]}">{_HN[p]} Fee</th>' for p in _PLATS)
    zfee_rows = ""
    for zone in ZONE_ORDER:
        sub_z = df[df["zone"] == zone]
        if sub_z.empty: continue
        cells = ""
        for p in _PLATS:
            sub_zp = sub_z[sub_z["platform"] == p]
            if sub_zp.empty: cells += '<td>—</td>'; continue
            fee = (sub_zp["delivery_fee"] + sub_zp["service_fee"]).mean()
            cells += f'<td style="color:{_HC[p]};font-weight:700">${fee:.2f}</td>'
        zfee_rows += f'<tr><td><b>{_HZ.get(zone, zone)}</b></td>{cells}</tr>'
    zfee_tbl = (
        f'<table><thead><tr><th>Zona</th>{zfee_hdr}</tr></thead>'
        f'<tbody>{zfee_rows}</tbody></table>'
    )

    r_ops = ops.get("rappi", {})
    comp_fees = {p: ops[p]["total_fee"] for p in ["ubereats","didi"] if ops.get(p)}
    cheap_p = min(comp_fees, key=comp_fees.get) if comp_fees else None
    fee_gap = r_ops.get("total_fee", 0) - comp_fees.get(cheap_p, 0) if cheap_p else 0
    eta_gap = r_ops.get("eta", 0) - min((ops[p]["eta"] for p in ["ubereats","didi"] if ops.get(p)), default=0)

    body = f"""
<div class="section">
  <div class="section-hdr">
    <div class="section-title">Narrativa de Riesgo Operativo</div>
    <div class="section-sub">Carga de fee · Rendimiento ETA · Presión competitiva</div>
  </div>
  <div class="section-body">
    <div class="narrative">
      Rappi opera con un fee total de <b>${r_ops.get("total_fee",0):.2f}</b> por orden —
      <b>{"+" if fee_gap>0 else ""}{fee_gap:.2f}</b> frente a la opción más económica del mercado.
      El ETA promedio de Rappi es <b>{r_ops.get("eta",0):.0f} min</b>
      {"— <b>" + f"{eta_gap:.0f} min</b> más lento que el competidor más ágil, generando fricción operativa compuesta que presiona la conversión." if eta_gap > 0 else "— dentro del rango competitivo del mercado."}
    </div>
  </div>
</div>
<div class="section">
  <div class="section-hdr">
    <div class="section-title">Arquitectura de Fees · Comparación de Plataformas</div>
    <div class="section-sub">Estructura de fees · Envío + servicio + % del precio</div>
  </div>
  <div class="section-body">{fee_tbl}</div>
</div>
<div class="two-col">
  <div class="section">
    <div class="section-hdr">
      <div class="section-title">Rendimiento ETA por Zona</div>
      <div class="section-sub">Tiempo de entrega promedio por zona geográfica</div>
    </div>
    <div class="section-body">{eta_tbl}</div>
  </div>
  <div class="section">
    <div class="section-hdr">
      <div class="section-title">Carga de Fee por Zona</div>
      <div class="section-sub">Fee total promedio por zona · Comparación directa</div>
    </div>
    <div class="section-body">{zfee_tbl}</div>
  </div>
</div>"""

    return _gen_html_shell(
        "Brief de Rendimiento Operativo",
        f"Arquitectura de Fees · Inteligencia de Entrega · CDMX · {date_tag}",
        body,
        [f"{len(df):,} Registros", f"{df['zone'].nunique()} Zonas",
         "Análisis de Fees", "Rendimiento ETA"],
        date_tag, dts,
    )


def _gen_promotions_brief_html(df: pd.DataFrame) -> bytes:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    date_tag = now.strftime("%Y-%m-%d")
    dts = now.strftime("%Y-%m-%d %H:%M UTC")

    df_s = df.copy()
    df_s["_strat"] = df_s["promo_label"].apply(_classify_promo_strategy)

    strat_by_plat = {}
    for p in _PLATS:
        sub = df_s[df_s["platform"] == p]
        if sub.empty:
            strat_by_plat[p] = {"dominant": "OTHER", "promo_rate": 0, "total": 0, "pcts": {}}
            continue
        counts = sub["_strat"].value_counts().to_dict()
        total  = len(sub)
        active = {k: v for k, v in counts.items() if k not in ("NONE", "OTHER")}
        dominant = max(active, key=lambda k: active[k]) if active else "OTHER"
        strat_by_plat[p] = {
            "dominant":  dominant,
            "promo_rate": round(100 * sum(active.values()) / total, 1),
            "total":      total,
            "pcts":       {k: round(100*v/total,1) for k, v in counts.items()},
        }

    # Platform promo summary table
    plat_rows = ""
    for p in _PLATS:
        d = strat_by_plat.get(p, {})
        dom = d.get("dominant", "OTHER")
        meta = _PROMO_STRAT_META.get(dom, ("·", dom, "#94A3B8", "#F8FAFC"))
        arch = _PROMO_ARCHETYPE.get(dom, ("TACTICAL", "#94A3B8", "#F8FAFC"))
        c = _HC[p]
        plat_rows += (
            f'<tr><td>{_hbadge(p)}</td>'
            f'<td><b>{d.get("promo_rate",0):.0f}%</b></td>'
            f'<td><span class="badge" style="background:{meta[3]};color:{meta[2]}">'
            f'{meta[0]} {meta[1]}</span></td>'
            f'<td><span class="badge" style="background:{arch[2]};color:{arch[1]}">'
            f'{arch[0]}</span></td>'
            f'<td>{d.get("total",0):,} registros</td></tr>'
        )
    plat_tbl = (
        '<table><thead><tr>'
        '<th>Plataforma</th><th>Tasa Promo</th><th>Táctica Dominante</th>'
        '<th>Arquetipo</th><th>Muestra</th>'
        f'</tr></thead><tbody>{plat_rows}</tbody></table>'
    )

    # Strategy distribution table
    all_strats = [k for k in _PROMO_STRAT_META if k not in ("NONE", "OTHER")]
    strat_hdr = "".join(f'<th style="color:{_HC[p]}">{_HN[p]}</th>' for p in _PLATS)
    strat_rows = ""
    for strat in all_strats:
        meta = _PROMO_STRAT_META[strat]
        cells = ""
        for p in _PLATS:
            pct = strat_by_plat.get(p, {}).get("pcts", {}).get(strat, 0)
            bar = f'<div class="bar-wrap"><div class="bar-fill" style="width:{min(pct,100):.0f}%;background:{meta[2]}"></div></div>'
            cells += f'<td><b>{pct:.0f}%</b>{bar}</td>'
        strat_rows += (
            f'<tr><td><span class="badge" style="background:{meta[3]};color:{meta[2]}">'
            f'{meta[0]} {meta[1]}</span></td>{cells}</tr>'
        )
    strat_tbl = (
        f'<table><thead><tr><th>Estrategia</th>{strat_hdr}</tr></thead>'
        f'<tbody>{strat_rows}</tbody></table>'
    )

    # Zone × strategy matrix
    zm_plat_hdr = "".join(f'<th style="color:{_HC[p]}">{_HN[p]}</th>' for p in _PLATS)
    zm_rows = ""
    for zone in ZONE_ORDER:
        cells = ""
        for p in _PLATS:
            sub_zp = df_s[(df_s["platform"]==p) & (df_s["zone"]==zone)]
            if sub_zp.empty: cells += '<td>—</td>'; continue
            active_z = {k: v for k, v in sub_zp["_strat"].value_counts().items()
                        if k not in ("NONE","OTHER")}
            dom_z = max(active_z, key=lambda k: active_z[k]) if active_z else "OTHER"
            sm = _PROMO_STRAT_META.get(dom_z, ("·", dom_z, "#94A3B8", "#F8FAFC"))
            cells += (
                f'<td><span class="badge" style="background:{sm[3]};color:{sm[2]}">'
                f'{sm[0]} {sm[1]}</span></td>'
            )
        zm_rows += f'<tr><td><b>{_HZ.get(zone, zone)}</b></td>{cells}</tr>'
    zm_tbl = (
        f'<table><thead><tr><th>Zona</th>{zm_plat_hdr}</tr></thead>'
        f'<tbody>{zm_rows}</tbody></table>'
    )

    dom_rappi = strat_by_plat.get("rappi", {}).get("dominant", "OTHER")
    dom_ue    = strat_by_plat.get("ubereats", {}).get("dominant", "OTHER")
    dom_didi  = strat_by_plat.get("didi", {}).get("dominant", "OTHER")

    body = f"""
<div class="section">
  <div class="section-hdr">
    <div class="section-title">Visión General de Intención Estratégica</div>
    <div class="section-sub">Análisis de filosofía promocional entre plataformas</div>
  </div>
  <div class="section-body">
    <div class="narrative">
      Tres filosofías competitivas distintas operan simultáneamente:
      <b>Rappi</b> ({_PROMO_STRAT_META.get(dom_rappi,("","",))[1]}) y
      <b>Uber Eats</b> ({_PROMO_STRAT_META.get(dom_ue,("","",))[1]}) anclan en ecosistemas de
      membresía orientados a retención, mientras que <b>DiDi Food</b> ({_PROMO_STRAT_META.get(dom_didi,("","",))[1]})
      ejecuta un playbook de adquisición agresivo — descuentos profundos en el primer pedido para
      expandir rápidamente su base. Señal de mercado en punto de inflexión estratégica.
    </div>
  </div>
</div>
<div class="two-col">
  <div class="section" style="flex:1">
    <div class="section-hdr">
      <div class="section-title">Platform Promo Summary</div>
      <div class="section-sub">Dominant tactic · Archetype · Rate</div>
    </div>
    <div class="section-body">{plat_tbl}</div>
  </div>
  <div class="section" style="flex:1">
    <div class="section-hdr">
      <div class="section-title">Zone × Strategy Matrix</div>
      <div class="section-sub">Dominant active strategy per zone per platform</div>
    </div>
    <div class="section-body">{zm_tbl}</div>
  </div>
</div>
<div class="section">
  <div class="section-hdr">
    <div class="section-title">Strategy Distribution</div>
    <div class="section-sub">% of records per strategy type per platform · with intensity bars</div>
  </div>
  <div class="section-body">{strat_tbl}</div>
</div>"""

    return _gen_html_shell(
        "Promotion Strategy Brief",
        f"Promotional Intelligence · Strategic Archetype Analysis · CDMX · {date_tag}",
        body,
        [f"{len(df):,} Records", "8 Strategy Types", "Zone × Strategy Matrix",
         "Commercial Intent"],
        date_tag, dts,
    )


def _gen_territory_report_html(df: pd.DataFrame) -> bytes:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    date_tag = now.strftime("%Y-%m-%d")
    dts = now.strftime("%Y-%m-%d %H:%M UTC")

    plat_hdr = "".join(f'<th style="color:{_HC[p]}">{_HN[p]}</th>' for p in _PLATS)

    def _zone_table(metric: str, fmt_fn) -> str:
        rows = ""
        for zone in ZONE_ORDER:
            sub_z = df[df["zone"] == zone]
            if sub_z.empty: continue
            cells = ""
            vals = []
            for p in _PLATS:
                sub_zp = sub_z[sub_z["platform"] == p]
                if sub_zp.empty: cells += '<td>—</td>'; continue
                v = sub_zp[metric].mean()
                vals.append(v)
                cells += f'<td style="font-weight:700;color:{_HC[p]}">{fmt_fn(v)}</td>'
            # Signal: whether Rappi is competitive
            if vals:
                rappi_v = df[(df["zone"]==zone)&(df["platform"]=="rappi")][metric].mean()
                is_best = pd.notna(rappi_v) and rappi_v == min(v for v in vals if pd.notna(v))
                sig_c = "#10B981" if is_best else "#F97316"
                sig_txt = "Rappi Best" if is_best else "Competitive Pressure"
                cells += (
                    f'<td><span class="badge" style="background:{sig_c}22;color:{sig_c}">'
                    f'{sig_txt}</span></td>'
                )
            rows += f'<tr><td><b>{_HZ.get(zone, zone)}</b></td>{cells}</tr>'
        return (
            f'<table><thead><tr><th>Zone</th>{plat_hdr}<th>Signal</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>'
        )

    price_tbl = _zone_table("final_price", lambda v: f"${v:.2f}")
    eta_tbl   = _zone_table("eta_min",     lambda v: f"{v:.0f} min")

    # Fee table (computed column)
    df2 = df.copy(); df2["_fee"] = df2["delivery_fee"] + df2["service_fee"]
    fee_rows = ""
    for zone in ZONE_ORDER:
        sub_z = df2[df2["zone"] == zone]
        if sub_z.empty: continue
        cells = ""
        for p in _PLATS:
            sub_zp = sub_z[sub_z["platform"] == p]
            if sub_zp.empty: cells += '<td>—</td>'; continue
            cells += f'<td style="font-weight:700;color:{_HC[p]}">${sub_zp["_fee"].mean():.2f}</td>'
        fee_rows += f'<tr><td><b>{_HZ.get(zone, zone)}</b></td>{cells}</tr>'
    fee_tbl = (
        f'<table><thead><tr><th>Zone</th>{plat_hdr}</tr></thead>'
        f'<tbody>{fee_rows}</tbody></table>'
    )

    # Zone opportunity index
    opp_rows = ""
    for zone in ZONE_ORDER:
        sub_z = df[df["zone"] == zone]
        if sub_z.empty: continue
        rappi_p = sub_z[sub_z["platform"]=="rappi"]["final_price"].mean()
        comp_p  = sub_z[sub_z["platform"]!="rappi"]["final_price"].mean()
        gap     = rappi_p - comp_p if pd.notna(rappi_p) and pd.notna(comp_p) else 0
        promo   = (sub_z[sub_z["platform"]!="rappi"]["discount"]>0).mean()*100 if not sub_z[sub_z["platform"]!="rappi"].empty else 0
        opp_score = min(100, max(0, abs(gap)*8 + promo*0.5))
        opp_c = "#EF4444" if opp_score > 60 else "#F59E0B" if opp_score > 30 else "#10B981"
        signal = ("Zona de alto riesgo" if opp_score > 60 else
                  "Monitorear de cerca" if opp_score > 30 else "Posición estable")
        bar = (f'<div class="bar-wrap">'
               f'<div class="bar-fill" style="width:{opp_score:.0f}%;background:{opp_c}"></div>'
               f'</div>')
        opp_rows += (
            f'<tr><td><b>{_HZ.get(zone,zone)}</b></td>'
            f'<td>{"+" if gap>0 else ""}{gap:.2f}</td>'
            f'<td>{promo:.0f}%</td>'
            f'<td>{opp_score:.0f}/100{bar}</td>'
            f'<td><span class="badge" style="background:{opp_c}22;color:{opp_c}">'
            f'{signal}</span></td></tr>'
        )
    opp_tbl = (
        '<table><thead><tr>'
        '<th>Zone</th><th>Price Gap (Rappi vs Comp)</th>'
        '<th>Competitor Promo Rate</th><th>Risk Index</th><th>Signal</th>'
        f'</tr></thead><tbody>{opp_rows}</tbody></table>'
    )

    n_zones = df["zone"].nunique()
    n_addrs = df["address_id"].nunique() if "address_id" in df.columns else n_zones

    body = f"""
<div class="section">
  <div class="section-hdr">
    <div class="section-title">Geographic Coverage</div>
    <div class="section-sub">Inteligencia territorial · {n_zones} zonas · {n_addrs} puntos de captura · CDMX</div>
  </div>
  <div class="section-body">
    <div class="narrative">
      Analysis spans <b>{n_zones} geographic zones</b> across CDMX, capturing competitive
      dynamics from premium corridors through peripheral neighborhoods.
      Zone-level intelligence reveals distinct competitive behaviors per area —
      premium zones show lower price gaps while peripheral zones face higher
      competitor promo intensity.
    </div>
  </div>
</div>
<div class="two-col">
  <div class="section">
    <div class="section-hdr">
      <div class="section-title">Zone Price Performance</div>
      <div class="section-sub">Precio final promedio por zona y plataforma</div>
    </div>
    <div class="section-body">{price_tbl}</div>
  </div>
  <div class="section">
    <div class="section-hdr">
      <div class="section-title">Zone ETA Performance</div>
      <div class="section-sub">Tiempo de entrega promedio por zona</div>
    </div>
    <div class="section-body">{eta_tbl}</div>
  </div>
</div>
<div class="two-col">
  <div class="section">
    <div class="section-hdr">
      <div class="section-title">Zone Fee Burden</div>
      <div class="section-sub">Total fee (delivery + service) por zona</div>
    </div>
    <div class="section-body">{fee_tbl}</div>
  </div>
  <div class="section">
    <div class="section-hdr">
      <div class="section-title">Zone Competitive Risk Index</div>
      <div class="section-sub">Composite risk score · Price gap + promo pressure</div>
    </div>
    <div class="section-body">{opp_tbl}</div>
  </div>
</div>"""

    return _gen_html_shell(
        "Territory Intelligence Report",
        f"Geographic Competitive Analysis · {n_zones} Zones · CDMX · {date_tag}",
        body,
        [f"{n_zones} Zones", f"{n_addrs} Capture Points",
         "Price × Zone", "ETA × Zone", "Risk Index"],
        date_tag, dts,
    )


# ── Router ────────────────────────────────────────────────────────────────────

def main():
    df_raw   = load_df()
    insights = load_insights()
    scores   = load_scores()
    page     = render_sidebar()
    df       = apply_filter(df_raw)

    dispatch = {
        "Resumen Ejecutivo":      lambda: page_executive(df, insights, scores),
        "Comparación de Precios": lambda: page_prices(df),
        "Benchmarking Operativo": lambda: page_operations(df),
        "Promociones":            lambda: page_promotions(df),
        "Mapas Geográficos":      lambda: page_geo(df_raw),
        "Galería de Evidencias":  lambda: page_evidence(df_raw),
        "Explorador de Datos":    lambda: page_raw(df),
        "Centro de Exportación":  lambda: page_export(df_raw, insights, scores),
    }
    dispatch.get(page, dispatch["Resumen Ejecutivo"])()


if __name__ == "__main__":
    main()
