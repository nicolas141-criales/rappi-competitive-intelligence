"""
theme.py – Rappi CI · Light mode premium design system v3.
Fixes: undefined chart titles, sidebar CSS, spacing.
"""
from __future__ import annotations

COLORS = {
    "bg":          "#F8FAFC",  # Lighter, crisper background
    "card":        "#FFFFFF",
    "border":      "#E2E8F0",  # Softer borders
    "rappi":       "#FB923C",  # Soft Premium Orange
    "ubereats":    "#34D399",  # Muted Sophisticated Green
    "didi":        "#FBBF24",  # Executive Warm Yellow
    "text_dark":   "#0F172A",
    "text_mid":    "#475569",
    "text_light":  "#94A3B8",
}

SEVERITY_COLORS = {
    "CRITICAL": "#EF4444",   # Red-500
    "HIGH":     "#F97316",   # Orange-500
    "MEDIUM":   "#F59E0B",   # Amber-500
    "LOW":      "#10B981",   # Emerald-500
}

SEVERITY_BG = {
    "CRITICAL": "#FEF2F2",
    "HIGH":     "#FFF7ED",
    "MEDIUM":   "#FFFBEB",
    "LOW":      "#F0FDF4",
}

PLATFORM_COLORS = {
    "rappi":    COLORS["rappi"],
    "ubereats": COLORS["ubereats"],
    "didi":     COLORS["didi"],
}
PLATFORM_LABELS = {
    "rappi":    "Rappi",
    "ubereats": "Uber Eats",
    "didi":     "DiDi Food",
}
ZONE_ORDER = ["premium", "corporativa", "media", "periferia"]

NAV_ITEMS = [
    ("Resumen Ejecutivo",      "▣"),
    ("Comparación de Precios", "◈"),
    ("Benchmarking Operativo", "◉"),
    ("Promociones",            "◆"),
    ("Mapas Geográficos",      "◐"),
    ("Galería de Evidencias",  "📸"),
    ("Explorador de Datos",    "▦"),
    ("Centro de Exportación",  "⬇"),
]


# ── Plotly light theme (Minimalist Enterprise) ────────────────────────────────
PLOTLY_LAYOUT = dict(
    template="plotly_white",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#64748B", size=11),
    margin=dict(l=0, r=0, t=10, b=0),
    legend=dict(
        bgcolor="rgba(255,255,255,0.7)",
        bordercolor="#E2E8F0",
        borderwidth=1,
        font=dict(color="#64748B", size=10),
    ),
    xaxis=dict(
        gridcolor="#F8FAFC",
        linecolor="#E2E8F0",
        tickfont=dict(color="#94A3B8", size=10),
        showgrid=False,
        zeroline=False,
    ),
    yaxis=dict(
        gridcolor="#F1F5F9",
        linecolor="rgba(0,0,0,0)",
        tickfont=dict(color="#94A3B8", size=10),
        showgrid=True,
        zeroline=False,
    ),
    colorway=[COLORS["rappi"], COLORS["ubereats"], COLORS["didi"]],
    hoverlabel=dict(
        bgcolor="#FFFFFF",
        bordercolor="#E2E8F0",
        font=dict(color="#0F172A", size=12, family="Inter"),
        namelength=-1,
    ),
)


def get_layout(**overrides) -> dict:
    layout = dict(PLOTLY_LAYOUT)
    for k, v in overrides.items():
        if k in layout and isinstance(layout[k], dict) and isinstance(v, dict):
            layout[k] = {**layout[k], **v}
        else:
            layout[k] = v
    return layout


GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Reset Streamlit chrome ────────────────────────────────────────────── */
#MainMenu,footer,header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"]          { display:none!important; }
html,body,[class*="css"]               { font-family:'Inter',sans-serif!important; }
.stApp                                 { background:#F7F8FC!important; }
.block-container                       { padding:0 2rem 2rem!important;
                                          max-width:100%!important; }

/* ── Sidebar shell ─────────────────────────────────────────────────────── */
section[data-testid="stSidebar"]       { background:#FFFFFF!important;
                                          border-right:1px solid #F1F5F9!important;
                                          min-width:230px!important;
                                          max-width:230px!important; }
section[data-testid="stSidebar"]>div:first-child { padding:0!important; }

/* ── Sidebar Radio Navigation ─────────────────────────────────────────── */
/* Each nav option */
section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] {
    display:flex!important;
    align-items:center!important;
    width:calc(100% - 16px)!important;
    margin:0 8px 2px!important;
    padding:8px 12px!important;
    border-radius:8px!important;
    border-left:3px solid transparent!important;
    cursor:pointer!important;
    transition:background 0.12s,border-color 0.12s!important;
    box-sizing:border-box!important;
}
/* Hide the radio circle */
section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] > div:first-child {
    display:none!important;
}
/* Label text */
section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] p {
    font-size:0.81rem!important;
    font-weight:500!important;
    color:#64748B!important;
    margin:0!important;
    white-space:nowrap!important;
    overflow:hidden!important;
    text-overflow:ellipsis!important;
    transition:color 0.12s,font-weight 0.12s!important;
}
/* Hover */
section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:hover {
    background:#FFF7ED!important;
    border-left-color:#FED7AA!important;
}
section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:hover p {
    color:#EA580C!important;
}
/* Active (selected) — uses :has() supported in Chrome 105+, Safari 15.4+, FF 121+ */
section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:has(input[type="radio"]:checked) {
    background:#FFEDD5!important;
    border-left-color:#FB923C!important;
}
section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:has(input[type="radio"]:checked) p {
    color:#EA580C!important;
    font-weight:700!important;
}
/* Option group spacing */
section[data-testid="stSidebar"] .stRadio [role="radiogroup"] {
    gap:0!important;
}

/* ── Run Live Scan button ─────────────────────────────────────────────── */
section[data-testid="stSidebar"] .stButton>button {
    width:100%!important;
    background:linear-gradient(135deg,#0F172A 0%,#1E293B 100%)!important;
    color:#F8FAFC!important;
    border:1px solid #334155!important;
    border-radius:8px!important;
    padding:9px 16px!important;
    font-size:0.78rem!important;
    font-weight:700!important;
    letter-spacing:0.04em!important;
    box-shadow:0 2px 8px rgba(0,0,0,0.18)!important;
    transition:all 0.15s!important;
    text-align:center!important;
    white-space:nowrap!important;
}
section[data-testid="stSidebar"] .stButton>button:hover {
    background:linear-gradient(135deg,#1E293B 0%,#334155 100%)!important;
    box-shadow:0 4px 14px rgba(0,0,0,0.24)!important;
    border-color:#475569!important;
    transform:translateY(-1px)!important;
}
section[data-testid="stSidebar"] .stButton>button:focus,
section[data-testid="stSidebar"] .stButton>button:active {
    box-shadow:0 2px 8px rgba(0,0,0,0.15)!important;
    outline:none!important;
    transform:none!important;
    border:1px solid #334155!important;
}

/* ── Plotly chart container cleanup ────────────────────────────────────── */
[data-testid="stPlotlyChart"] {
    background:transparent;
    border:none;
    padding:0;
    box-shadow:none;
}

/* ── KPI column spacing ─────────────────────────────────────────────────── */
[data-testid="column"] { padding:0 8px!important; }
[data-testid="column"]:first-child { padding-left:0!important; }
[data-testid="column"]:last-child  { padding-right:0!important; }

/* ── Multiselect ────────────────────────────────────────────────────────── */
[data-baseweb="select"]>div {
    background:#F8FAFC!important;
    border:1px solid #E2E8F0!important;
    border-radius:6px!important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.01)!important;
}
[data-baseweb="select"] [data-baseweb="tag"] {
    background:#FFF7ED!important;
    border:1px solid #FFEDD5!important;
    border-radius:4px!important;
    color:#EA580C!important;
}

/* ── Download button ────────────────────────────────────────────────────── */
[data-testid="stDownloadButton"]>button {
    background:#FFFFFF!important;
    border:1px solid #E2E8F0!important;
    border-radius:6px!important;
    color:#0F172A!important;
    font-weight:500!important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02)!important;
}

/* ── Dataframe ──────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] { border-radius:8px!important; overflow:hidden; border:1px solid #E2E8F0; }

/* ── Scrollbar ──────────────────────────────────────────────────────────── */
::-webkit-scrollbar      { width:4px;height:4px; }
::-webkit-scrollbar-track{ background:transparent; }
::-webkit-scrollbar-thumb{ background:#E2E8F0;border-radius:2px; }

/* ── Remove stMarkdown bottom margin inside sidebar ─────────────────────── */
section[data-testid="stSidebar"] .stMarkdown { margin-bottom:0!important; }

/* ── Fade-in ─────────────────────────────────────────────────────────────── */
@keyframes fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.fade-in{animation:fadeIn 0.3s ease forwards}

/* ── Chip button selectors (Pricing Console filters) ────────────────────── */
div.chip-btn .stButton>button {
    border-radius:20px!important;
    border:1.5px solid #E2E8F0!important;
    background:#F8FAFC!important;
    color:#64748B!important;
    font-size:0.74rem!important;
    font-weight:500!important;
    padding:4px 12px!important;
    height:auto!important;
    min-height:28px!important;
    box-shadow:none!important;
    transition:all 0.15s ease!important;
}
div.chip-btn .stButton>button:hover {
    background:#FFF7ED!important;
    border-color:#FED7AA!important;
    color:#FB923C!important;
}
div.chip-active .stButton>button {
    border-radius:20px!important;
    border:2px solid #F97316!important;
    background:#FB923C!important;
    color:#FFFFFF!important;
    font-size:0.74rem!important;
    font-weight:700!important;
    padding:4px 12px!important;
    height:auto!important;
    min-height:28px!important;
    box-shadow:0 3px 10px rgba(251,146,60,0.32)!important;
    transition:all 0.15s ease!important;
}
div.chip-active .stButton>button:hover {
    background:#F97316!important;
    border-color:#EA580C!important;
    box-shadow:0 4px 14px rgba(249,115,22,0.38)!important;
}
div.chip-active .stButton>button:focus,
div.chip-btn .stButton>button:focus    { box-shadow:none!important;outline:none!important; }

/* ── Active filter pill buttons (removable tags) ─────────────────────────── */
div.filter-pill-btn .stButton>button {
    border-radius:16px!important;
    border:1.5px solid #FED7AA!important;
    background:#FFF7ED!important;
    color:#C2410C!important;
    font-size:0.7rem!important;
    font-weight:600!important;
    padding:3px 10px!important;
    height:auto!important;
    min-height:26px!important;
    box-shadow:none!important;
    transition:all 0.12s ease!important;
    white-space:nowrap!important;
}
div.filter-pill-btn .stButton>button:hover {
    background:#FFEDD5!important;
    border-color:#FB923C!important;
    color:#9A3412!important;
}
div.filter-pill-btn .stButton>button:focus { box-shadow:none!important;outline:none!important; }

/* ── Live Pulse Indicator ────────────────────────────────────────────────── */
@keyframes pulse {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
    70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}
.live-pulse {
    display: inline-block;
    width: 8px;
    height: 8px;
    background-color: #10B981;
    border-radius: 50%;
    margin-right: 8px;
    animation: pulse 2s infinite;
}

/* ── Custom Cards ────────────────────────────────────────────────────────── */
.premium-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02), 0 1px 2px rgba(0,0,0,0.01);
    margin-bottom: 16px;
    transition: box-shadow 0.2s ease;
}
.premium-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.04), 0 2px 4px rgba(0,0,0,0.02);
}
.score-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
}
.narrative-text {
    font-size: 0.9rem;
    color: #475569;
    line-height: 1.5;
}
.narrative-title {
    font-size: 1rem;
    font-weight: 600;
    color: #0F172A;
    margin-bottom: 8px;
}

/* ── Page-header contextual export button ───────────────────────────────────── */
div.hdr-export-btn [data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, #FF6B35 0%, #FB923C 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 0.76rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.03em !important;
    padding: 7px 16px !important;
    box-shadow: 0 2px 8px rgba(251,146,60,0.32) !important;
    transition: all 0.15s !important;
    white-space: nowrap !important;
}
div.hdr-export-btn [data-testid="stDownloadButton"] > button:hover {
    background: linear-gradient(135deg, #EA580C 0%, #F97316 100%) !important;
    box-shadow: 0 4px 14px rgba(249,115,22,0.40) !important;
    transform: translateY(-1px) !important;
}
div.hdr-export-btn [data-testid="stDownloadButton"] > button:focus,
div.hdr-export-btn [data-testid="stDownloadButton"] > button:active {
    box-shadow: 0 2px 8px rgba(251,146,60,0.22) !important;
    outline: none !important;
    transform: none !important;
}
</style>
"""
