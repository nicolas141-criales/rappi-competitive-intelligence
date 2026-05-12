"""
components.py – Rappi CI premium components v3.
Fixes: sidebar active state, KPI cards, chart_card, insight strip.
"""
from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
from app.dashboard.theme import COLORS, PLATFORM_COLORS, PLATFORM_LABELS, NAV_ITEMS, get_layout


# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar() -> str:
    import time
    from datetime import datetime, date

    # ── Logo ──────────────────────────────────────────────────────────────────
    st.sidebar.markdown("""
    <div style="padding:22px 18px 14px;border-bottom:1px solid #F1F5F9;margin-bottom:2px">
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px">
        <span style="font-size:1.35rem;font-weight:800;
                     background:linear-gradient(135deg,#FF6B35,#FB923C);
                     -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                     letter-spacing:-0.5px">Rappi</span>
        <span style="font-size:0.95rem;font-weight:300;color:#CBD5E1;letter-spacing:2px">CI</span>
        <div style="margin-left:auto;display:flex;align-items:center;gap:5px;
                    background:#ECFDF5;border:1px solid #A7F3D0;border-radius:6px;
                    padding:3px 8px">
          <div style="width:6px;height:6px;border-radius:50%;
                      background:#10B981;box-shadow:0 0 5px #10B981;flex-shrink:0"></div>
          <span style="font-size:0.6rem;font-weight:700;color:#059669">LIVE</span>
        </div>
      </div>
      <div style="font-size:0.58rem;font-weight:700;color:#94A3B8;
                  letter-spacing:1.6px;text-transform:uppercase">Competitive Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Navigation label ──────────────────────────────────────────────────────
    st.sidebar.markdown("""
    <div style="padding:10px 18px 2px;font-size:0.56rem;font-weight:700;
                color:#CBD5E1;letter-spacing:1.6px;text-transform:uppercase">
      Navigation
    </div>""", unsafe_allow_html=True)

    # ── Radio nav — active state handled natively via CSS :has() ──────────────
    nav_labels = [f"{icon}  {label}" for label, icon in NAV_ITEMS]
    selected_str = st.sidebar.radio(
        "Navigation",
        nav_labels,
        label_visibility="collapsed",
        key="sidebar_nav",
    )
    active = NAV_ITEMS[0][0]
    for label, icon in NAV_ITEMS:
        if f"{icon}  {label}" == selected_str:
            active = label
            break

    # ── Live Monitoring ───────────────────────────────────────────────────────
    st.sidebar.markdown("""
    <div style="padding:14px 18px 8px;border-top:1px solid #F1F5F9;
                font-size:0.56rem;font-weight:700;color:#CBD5E1;
                letter-spacing:1.6px;text-transform:uppercase">
      Live Monitoring
    </div>""", unsafe_allow_html=True)

    run_scan = st.sidebar.button(
        "▶  Run Live Scan", use_container_width=True, key="btn_scan"
    )
    scan_status = st.sidebar.empty()

    if run_scan:
        stages = [
            ("◉", "Scanning Markets...",     "#F59E0B"),
            ("⟳", "Ingesting Data...",       "#3B82F6"),
            ("📸", "Collecting Evidence...", "#8B5CF6"),
            ("✓",  "Monitoring Live",         "#10B981"),
        ]
        for icon_s, msg, color in stages:
            scan_status.markdown(f"""
            <div style="margin:4px 10px 6px;background:#F8FAFC;border:1px solid #E2E8F0;
                 border-radius:8px;padding:7px 12px;display:flex;align-items:center;gap:8px">
              <div style="width:7px;height:7px;border-radius:50%;background:{color};
                   flex-shrink:0;box-shadow:0 0 6px {color}66"></div>
              <span style="font-size:0.71rem;font-weight:600;color:#0F172A">{msg}</span>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(0.55)
        st.cache_data.clear()
        st.session_state["last_scan_ts"] = datetime.now()
        scan_status.empty()
        st.rerun()

    last_ts = st.session_state.get("last_scan_ts")
    if last_ts:
        elapsed_min = int((datetime.now() - last_ts).total_seconds() / 60)
        elapsed_str = "Just now" if elapsed_min < 1 else f"{elapsed_min}m ago"
        scan_status.markdown(f"""
        <div style="margin:4px 10px 6px;background:#ECFDF5;border:1px solid #A7F3D0;
             border-radius:8px;padding:7px 12px;display:flex;align-items:center;gap:8px">
          <div style="width:7px;height:7px;border-radius:50%;background:#10B981;
               flex-shrink:0;animation:pulse 2s infinite"></div>
          <span style="font-size:0.7rem;font-weight:600;color:#065F46">
            Live · Scanned {elapsed_str}</span>
        </div>
        """, unsafe_allow_html=True)

    # ── Data Status ───────────────────────────────────────────────────────────
    st.sidebar.markdown("""
    <div style="padding:14px 18px 6px;border-top:1px solid #F1F5F9;
                font-size:0.56rem;font-weight:700;color:#CBD5E1;
                letter-spacing:1.6px;text-transform:uppercase">
      Data Status
    </div>""", unsafe_allow_html=True)

    today_str = date.today().strftime("%b %d, %Y")
    st.sidebar.markdown(f"""
    <div style="padding:0 14px 14px">
      <div style="background:#F8FAFC;border:1px solid #F1F5F9;border-radius:8px;
           padding:10px 12px">
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:5px">
          <div style="width:5px;height:5px;border-radius:50%;background:#10B981;
               flex-shrink:0"></div>
          <span style="font-size:0.7rem;font-weight:700;color:#0F172A">705 records active</span>
        </div>
        <div style="font-size:0.63rem;color:#64748B;line-height:1.7">
          50 zones · 3 platforms<br>
          5 products · CDMX<br>
          <span style="color:#94A3B8;font-size:0.6rem">Updated {today_str}</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Fixed footer ──────────────────────────────────────────────────────────
    st.sidebar.markdown("""
    <div style="position:fixed;bottom:0;left:0;width:230px;
                background:#FFFFFF;border-top:1px solid #F1F5F9;padding:12px 18px">
      <div style="display:flex;align-items:center;gap:8px">
        <div style="width:30px;height:30px;border-radius:50%;
                    background:linear-gradient(135deg,#0F172A,#1E293B);
                    display:flex;align-items:center;justify-content:center;
                    font-size:0.85rem">⚡</div>
        <div>
          <div style="font-size:0.72rem;font-weight:600;color:#0F172A">Sistema en vivo</div>
          <div style="font-size:0.62rem;color:#94A3B8">CDMX · 50 zonas activas</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    return active


# ── Page header ───────────────────────────────────────────────────────────────

def page_header(title: str, subtitle: str,
                export_config: dict | None = None) -> None:
    from datetime import date
    today = date.today().strftime("%d %b %Y")

    left_col, right_col = st.columns([3, 1], gap="small")

    with left_col:
        st.markdown(
            f'<div class="fade-in" style="padding:22px 0 14px">'
            f'<h1 style="margin:0;font-size:1.65rem;font-weight:700;color:#0F172A;'
            f'letter-spacing:-0.5px">{title}</h1>'
            f'<p style="margin:4px 0 0;font-size:0.83rem;color:#94A3B8">{subtitle}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with right_col:
        st.markdown(
            f'<div style="display:flex;flex-wrap:wrap;align-items:center;'
            f'justify-content:flex-end;gap:8px;padding-top:24px">'
            f'<span style="font-size:0.72rem;color:#94A3B8;background:#F8FAFC;'
            f'border:1px solid #E9ECF5;border-radius:8px;padding:5px 10px;white-space:nowrap">'
            f'01 May – {today}</span>'
            f'<div style="display:flex;align-items:center;gap:0;background:#ECFDF5;'
            f'border:1px solid #A7F3D0;border-radius:8px;padding:5px 10px">'
            f'<div class="live-pulse"></div>'
            f'<span style="font-size:0.72rem;font-weight:600;color:#10B981;'
            f'white-space:nowrap">Live</span></div></div>',
            unsafe_allow_html=True,
        )
        if export_config:
            st.markdown('<div class="hdr-export-btn">', unsafe_allow_html=True)
            st.download_button(
                label=export_config.get("label", "↑ Export"),
                data=export_config["data"],
                file_name=export_config["file_name"],
                mime=export_config.get("mime", "text/html"),
                use_container_width=True,
                key=export_config.get("key", "_pg_export"),
            )
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        '<div style="height:1px;background:#F1F5F9;margin:0 0 20px"></div>',
        unsafe_allow_html=True,
    )


# ── KPI Cards ─────────────────────────────────────────────────────────────────

_KPI_CONFIG = {
    "precio":    ("💳", "#FB923C", "#FFF7ED", "#FED7AA"),
    "fee":       ("🛵", "#F59E0B", "#FFFBEB", "#FDE68A"),
    "eta":       ("⏱",  "#0EA5E9", "#F0F9FF", "#BAE6FD"),
    "registros": ("⊞",  "#64748B", "#F8FAFC", "#E2E8F0"),
    "insights":  ("💡", "#10B981", "#ECFDF5", "#A7F3D0"),
}

def kpi_row(kpis: list[dict]) -> None:
    cols = st.columns(len(kpis), gap="small")
    for col, kpi in zip(cols, kpis):
        key  = kpi.get("icon_key", "precio")
        icon, color, bg, border_c = _KPI_CONFIG.get(key, _KPI_CONFIG["precio"])
        delta   = str(kpi.get("delta", ""))
        d_label = kpi.get("delta_label", "")
        positive = not delta.startswith("-") and bool(delta) and not delta.startswith("▼")
        d_color  = "#10B981" if positive else "#EF4444"

        col.markdown(f"""
        <div class="fade-in premium-card" style="padding:18px 16px; height:100%; display:flex; flex-direction:column; justify-content:space-between">
          <div style="display:flex;justify-content:space-between; align-items:flex-start;margin-bottom:12px">
            <span style="font-size:0.65rem;font-weight:700;color:#94A3B8; text-transform:uppercase;letter-spacing:0.8px; line-height:1.3">{kpi['label']}</span>
            <div style="width:28px;height:28px;border-radius:6px; background:{bg};border:1px solid {border_c}; display:flex;align-items:center; justify-content:center;font-size:0.85rem; flex-shrink:0">{icon}</div>
          </div>
          <div>
              <div style="font-size:1.6rem;font-weight:700;color:#0F172A; letter-spacing:-0.5px;margin-bottom:4px; line-height:1">{kpi['value']}</div>
              <div style="font-size:0.72rem;color:{d_color};font-weight:500">
                {delta} <span style="color:#94A3B8;font-weight:400">{d_label}</span>
              </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── Radial Gauge Chart ────────────────────────────────────────────────────────
def radial_gauge(value: float, title: str, color: str) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 13, 'color': '#64748B'}},
        number={'font': {'size': 32, 'color': '#0F172A', 'weight': 'bold'}, 'suffix': ''},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#E2E8F0", "tickfont": {"color": "#94A3B8", "size": 9}},
            'bar': {'color': color, 'thickness': 0.25},
            'bgcolor': "white",
            'borderwidth': 0,
            'bordercolor': "white",
            'steps': [
                {'range': [0, 100], 'color': '#F8FAFC'}
            ],
        }
    ))
    fig.update_layout(height=200, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

# ── Linear Progress Bar ───────────────────────────────────────────────────────
def progress_bar(label: str, value: float, max_val: float, color: str, prefix: str = "", suffix: str = "") -> str:
    pct = min(100, max(0, (value / max_val) * 100)) if max_val > 0 else 0
    return f"""
    <div style="margin-bottom: 12px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
            <span style="font-size:0.8rem; font-weight:600; color:#475569;">{label}</span>
            <span style="font-size:0.8rem; font-weight:700; color:#0F172A;">{prefix}{value}{suffix}</span>
        </div>
        <div style="width:100%; background:#F1F5F9; border-radius:4px; height:6px; overflow:hidden;">
            <div style="height:100%; width:{pct}%; background:{color}; border-radius:4px;"></div>
        </div>
    </div>
    """


# ── Section title ─────────────────────────────────────────────────────────────

def section_title(title: str, subtitle: str = "", link: str = "") -> None:
    link_html = (f'<a href="#" style="font-size:0.75rem;color:#FB923C;'
                 f'font-weight:500;text-decoration:none;white-space:nowrap">'
                 f'{link} →</a>') if link else ""
    sub_html = (f'<p style="margin:2px 0 0;font-size:0.73rem;color:#94A3B8">'
                f'{subtitle}</p>') if subtitle else ""
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;
                align-items:flex-end;margin:20px 0 10px">
      <div>
        <h3 style="margin:0;font-size:0.92rem;font-weight:600;
                   color:#0F172A;letter-spacing:-0.2px">{title}</h3>
        {sub_html}
      </div>
      {link_html}
    </div>
    """, unsafe_allow_html=True)


# ── Chart card – uses CSS to wrap plotly, no broken HTML wrapper ──────────────

def chart_card(fig: go.Figure, height: int = 300) -> None:
    """Render Plotly chart — border/card styles applied via CSS on stPlotlyChart."""
    fig.update_layout(height=height)
    st.plotly_chart(fig, use_container_width=True,
                    config={"displayModeBar": False, "responsive": True})


# ── Insight strip (horizontal) ────────────────────────────────────────────────

_INSIGHT_CATS  = ["Pricing", "Delivery", "Promociones", "Tiempos", "Geográfico"]
_INSIGHT_CLRS  = ["#FF4F87", "#D946EF", "#7C3AED", "#06B6D4", "#10B981"]

from app.dashboard.theme import SEVERITY_COLORS, SEVERITY_BG

def insight_strip(insights: list[dict]) -> None:
    if not insights:
        return
    visible = insights[:5]
    cols = st.columns(len(visible), gap="small")
    for i, (col, ins) in enumerate(zip(cols, visible)):
        c   = _INSIGHT_CLRS[i % len(_INSIGHT_CLRS)]
        cat = _INSIGHT_CATS[i % len(_INSIGHT_CATS)]
        sev = ins.get("severity", "MEDIUM")
        s_col = SEVERITY_COLORS.get(sev, SEVERITY_COLORS["MEDIUM"])
        text = ins.get("finding", ins.get("title", ""))[:110]
        if len(ins.get("finding", ins.get("title", ""))) > 110:
            text += "…"

        col.markdown(f"""
        <div class="fade-in premium-card" style="padding:16px; height:100%; display:flex; flex-direction:column">
          <div style="display:flex;align-items:center;gap:7px;margin-bottom:12px">
            <div style="width:6px;height:6px;border-radius:50%;background:{s_col};"></div>
            <span style="font-size:0.65rem;font-weight:700;color:{s_col}">SEÑAL {sev.replace('HIGH', 'ALTA').replace('MEDIUM', 'MEDIA').replace('CRITICAL', 'CRÍTICA')}</span>
          </div>
          <p style="margin:0 0 auto;font-size:0.85rem;color:#0F172A;
                    line-height:1.45;font-weight:500">{text}</p>
          <div style="display:flex;justify-content:space-between;align-items:center;
                      border-top:1px solid #F1F5F9;padding-top:10px; margin-top:14px">
            <span style="font-size:0.65rem;color:#94A3B8;font-weight:500">Confianza: {ins.get('confidence', 80)}%</span>
            <span style="font-size:0.65rem;font-weight:600;color:{c}">Insights →</span>
          </div>
        </div>
        """, unsafe_allow_html=True)


# ── AI Strategic Signal Card ──────────────────────────────────────────────────

def signal_card(ins: dict, index: int = 0) -> None:
    sev   = ins.get("severity", "MEDIUM")
    color = SEVERITY_COLORS.get(sev, SEVERITY_COLORS["MEDIUM"])
    bg    = SEVERITY_BG.get(sev, SEVERITY_BG["MEDIUM"])
    
    title   = ins.get("title", "")
    finding = ins.get("finding", "")
    rec     = ins.get("recommendation", "")
    impact  = ins.get("impact", "")
    ins_id  = ins.get("id", f"SIG_{index:03d}")
    conf    = ins.get("confidence", 80)
    zones   = ", ".join([z.title() for z in ins.get("affected_zones", ["Todas"])])

    st.markdown(f"""
    <div class="fade-in premium-card" style="padding:22px;">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px">
        <span style="font-size:0.65rem;font-weight:700;color:{color};
                     background:{bg};border-radius:6px;padding:4px 10px;
                     border:1px solid {color}22">SEÑAL {sev.replace('HIGH', 'ALTA').replace('MEDIUM', 'MEDIA').replace('CRITICAL', 'CRÍTICA')}</span>
        <span style="font-size:0.65rem;font-weight:600;color:#64748B;
                     background:#F1F5F9;border-radius:6px;padding:4px 10px;
                     border:1px solid #E2E8F0">Confianza: {conf}%</span>
        <span style="margin-left:auto;font-size:0.65rem;color:#94A3B8;
                     display:flex;align-items:center;gap:4px;font-weight:500">
          📍 {zones}</span>
      </div>
      <p style="margin:0 0 14px;font-size:1.05rem;font-weight:600;
                color:#0F172A;line-height:1.4;letter-spacing:-0.2px">{title}</p>
      
      <div style="margin-bottom:16px">
        <div style="font-size:0.85rem;color:#475569;line-height:1.6;margin-bottom:10px">{finding}</div>
        <div style="font-size:0.8rem;color:#64748B;background:#F8FAFC;padding:10px 14px;border-radius:6px;border-left:3px solid #E2E8F0">
          <span style="font-weight:600;color:#0F172A">Impacto de Negocio:</span> {impact}
        </div>
      </div>
      
      <div style="display:flex;gap:12px;align-items:flex-start;background:#FFFBEB;padding:14px;border-radius:8px;border:1px solid #FEF3C7">
        <div style="font-size:1.1rem;margin-top:2px">🎯</div>
        <div>
          <div style="font-size:0.65rem;font-weight:700;color:#D97706;
                      text-transform:uppercase;letter-spacing:0.5px;
                      margin-bottom:4px">Acción Recomendada</div>
          <div style="font-size:0.85rem;color:#0F172A;line-height:1.5;font-weight:500">{rec}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ── Market Briefing ───────────────────────────────────────────────────────────

def market_briefing(df, insights: list) -> None:
    """Bold strategic narrative derived from real data. Renders at top of Executive Summary."""
    import pandas as pd
    from datetime import date

    if df is None or df.empty:
        return

    rappi = df[df["platform"] == "rappi"]
    ue    = df[df["platform"] == "ubereats"]
    dd    = df[df["platform"] == "didi"]

    r_price = rappi["final_price"].mean() if not rappi.empty else 0
    d_price = dd["final_price"].mean()    if not dd.empty    else 0
    r_eta   = rappi["eta_min"].mean()     if not rappi.empty else 0
    u_eta   = ue["eta_min"].mean()        if not ue.empty    else 0

    didi_diff = ((r_price - d_price) / max(d_price, 1)) * 100 if d_price > 0 else 0
    eta_diff  = r_eta - u_eta if u_eta > 0 else 0

    high_sigs  = [i for i in insights if i.get("severity") in ("CRITICAL", "HIGH")]
    crit_sigs  = [i for i in insights if i.get("severity") == "CRITICAL"]

    if len(crit_sigs) >= 1:
        threat_label, threat_color, threat_bg = "CRÍTICO",  "#EF4444", "#FEF2F2"
    elif len(high_sigs) >= 2:
        threat_label, threat_color, threat_bg = "ALTO",     "#F97316", "#FFF7ED"
    else:
        threat_label, threat_color, threat_bg = "MODERADO", "#F59E0B", "#FFFBEB"

    sentences = []
    if didi_diff > 5:
        sentences.append(
            f'DiDi Food opera con precios <b>{didi_diff:.0f}% por debajo de Rappi</b> '
            f'en promedio — presión directa sobre conversión en todos los segmentos.'
        )
    if eta_diff > 5:
        sentences.append(
            f'Uber Eats supera a Rappi por <b>{eta_diff:.0f} minutos en velocidad de entrega</b> '
            f'— riesgo de pérdida de preferencia en horas pico.'
        )
    if not sentences:
        sentences.append('Monitoreo activo en tiempo real. Sin alertas críticas en este período.')

    top_rec = ""
    if insights:
        top_rec = insights[0].get("recommendation", "")[:90]
        if len(insights[0].get("recommendation", "")) > 90:
            top_rec += "…"

    narrative = "".join(
        f'<span style="display:block;margin-bottom:5px">{s}</span>' for s in sentences[:2]
    )
    today_str = date.today().strftime("%d %b %Y").upper()

    st.markdown(f"""
    <div class="fade-in" style="background:linear-gradient(135deg,#FFFBF7,#FFF7ED);
                border:1px solid #FED7AA;border-radius:12px;padding:20px 24px;
                margin-bottom:20px;display:flex;align-items:flex-start;gap:24px">
      <div style="flex:1">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
          <span style="font-size:0.6rem;font-weight:700;color:#94A3B8;
                       letter-spacing:1.5px;text-transform:uppercase">
            Market Briefing · {today_str}</span>
          <span style="background:{threat_bg};color:{threat_color};
                       border:1px solid {threat_color}44;border-radius:6px;
                       padding:2px 8px;font-size:0.62rem;font-weight:700;letter-spacing:0.5px">
            ⚑ Amenaza {threat_label}</span>
        </div>
        <div style="font-size:0.875rem;color:#1E293B;line-height:1.7;margin-bottom:{'10px' if top_rec else '0'}">
          {narrative}
        </div>
        {f'<div style="font-size:0.75rem;color:#64748B;background:rgba(255,255,255,0.6);padding:8px 12px;border-radius:6px;border-left:3px solid #FB923C"><b style="color:#0F172A">Acción sugerida:</b> {top_rec}</div>' if top_rec else ''}
      </div>
      <div style="text-align:center;flex-shrink:0;padding:8px 16px;
                  background:white;border-radius:10px;border:1px solid #FED7AA">
        <div style="font-size:2.4rem;font-weight:800;color:#FB923C;line-height:1">
          {len(high_sigs)}</div>
        <div style="font-size:0.6rem;color:#94A3B8;font-weight:700;
                    text-transform:uppercase;letter-spacing:0.5px;margin-top:2px">
          señales activas</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ── Battle Card ───────────────────────────────────────────────────────────────

def battlecard(df) -> None:
    """3-column head-to-head platform comparison with dynamic winner badges."""
    import pandas as pd

    if df is None or df.empty:
        return

    pf_order = ["rappi", "ubereats", "didi"]
    pf_meta  = {
        "rappi":    ("Rappi",     "ANFITRIÓN",  "#FF6B35", "#FFF7ED", "#FED7AA"),
        "ubereats": ("Uber Eats", "VELOCIDAD",  "#059669", "#ECFDF5", "#A7F3D0"),
        "didi":     ("DiDi Food", "PRECIO",     "#D97706", "#FFFBEB", "#FDE68A"),
    }

    stats: dict = {}
    for p in pf_order:
        sub = df[df["platform"] == p]
        if sub.empty:
            continue
        stats[p] = {
            "price": sub["final_price"].mean(),
            "fee":   sub["delivery_fee"].mean(),
            "eta":   sub["eta_min"].mean(),
            "promo": (sub["discount"] > 0).mean() * 100,
        }

    if not stats:
        return

    def _winner(metric: str, direction: str = "min") -> str:
        vals = {p: stats[p][metric] for p in stats}
        return (min if direction == "min" else max)(vals, key=vals.get)

    price_w = _winner("price", "min")
    fee_w   = _winner("fee",   "min")
    eta_w   = _winner("eta",   "min")
    promo_w = _winner("promo", "max")

    def _row(label: str, fmt_val: str, is_winner: bool) -> str:
        badge = (' <span style="font-size:0.75rem;color:#10B981;font-weight:700">✓</span>'
                 if is_winner else '')
        vcolor = "#10B981" if is_winner else "#0F172A"
        return (
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:8px 0;border-bottom:1px solid #F1F5F9;">'
            f'<span style="font-size:0.72rem;color:#64748B">{label}</span>'
            f'<span style="font-size:0.8rem;font-weight:700;color:{vcolor}">{fmt_val}{badge}</span>'
            f'</div>'
        )

    cols_html: list[str] = []
    for p in pf_order:
        if p not in stats:
            continue
        s = stats[p]
        pname, pos_label, color, bg, border = pf_meta[p]

        wins = sum(1 for w in [price_w, fee_w, eta_w, promo_w] if w == p)
        rows = (
            _row("Precio Final",    f'${s["price"]:.0f} MXN', p == price_w) +
            _row("Delivery Fee",    f'${s["fee"]:.0f} MXN',   p == fee_w)   +
            _row("ETA Promedio",    f'{s["eta"]:.0f} min',     p == eta_w)   +
            _row("Promo Coverage",  f'{s["promo"]:.0f}%',      p == promo_w)
        )
        win_color = "#10B981" if wins >= 3 else "#F97316" if wins >= 2 else "#EF4444"
        win_label = "Lidera mercado" if wins >= 3 else "Posición mixta" if wins >= 2 else "En desventaja"

        cols_html.append(
            f'<div style="border:2px solid {color};border-radius:12px;padding:20px;'
            f'background:{bg};flex:1;min-width:0">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">'
            f'<span style="font-weight:800;font-size:1rem;color:{color}">{pname}</span>'
            f'<span style="background:white;color:{color};border:1px solid {border};'
            f'border-radius:6px;padding:2px 8px;font-size:0.62rem;font-weight:700">{pos_label}</span>'
            f'</div>'
            f'{rows}'
            f'<div style="margin-top:12px;padding-top:10px;border-top:1px solid {border};'
            f'display:flex;justify-content:space-between;align-items:center">'
            f'<span style="font-size:0.7rem;color:#94A3B8">Categorías ganadas</span>'
            f'<span style="font-size:0.82rem;font-weight:700;color:{win_color}">'
            f'{wins}/4 · {win_label}</span>'
            f'</div>'
            f'</div>'
        )

    st.markdown(
        f'<div style="display:flex;gap:14px;margin:4px 0 20px">'
        f'{"".join(cols_html)}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Empty state ───────────────────────────────────────────────────────────────

def empty_state(msg: str = "Ejecuta: python app/main.py --mock") -> None:
    st.markdown(f"""
    <div style="text-align:center;padding:56px 24px;background:#FFFFFF;
                border:1px solid #F1F5F9;border-radius:14px;margin:16px 0;
                box-shadow:0 1px 4px rgba(0,0,0,0.04)">
      <div style="font-size:2rem;margin-bottom:12px;opacity:0.25">◈</div>
      <div style="font-size:0.9rem;font-weight:600;color:#0F172A;margin-bottom:6px">
        Sin datos disponibles</div>
      <code style="font-size:0.75rem;color:#94A3B8;background:#F8FAFC;
                   padding:4px 10px;border-radius:4px">{msg}</code>
    </div>
    """, unsafe_allow_html=True)
