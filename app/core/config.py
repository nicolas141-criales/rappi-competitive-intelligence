"""
config.py – Configuración central del sistema.
Lee variables de entorno y provee constantes globales.
"""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Cargar .env ───────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env", override=False)

# ── Directorios ───────────────────────────────────────────────────────────────
DATA_DIR       = BASE_DIR / "app" / "data"
RAW_DIR        = DATA_DIR / "raw"
PROCESSED_DIR  = DATA_DIR / "processed"
SCREENSHOTS_DIR= DATA_DIR / "screenshots"

for _d in (RAW_DIR, PROCESSED_DIR, SCREENSHOTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ── Archivos de salida ────────────────────────────────────────────────────────
ADDRESSES_CSV       = DATA_DIR / "addresses.csv"
COMPETITIVE_CSV     = PROCESSED_DIR / "competitive_data.csv"
COMPETITIVE_JSON    = PROCESSED_DIR / "competitive_data.json"
INSIGHTS_JSON       = PROCESSED_DIR / "insights.json"
DB_PATH             = DATA_DIR / "competitive.db"

# ── Playwright ────────────────────────────────────────────────────────────────
HEADLESS    = os.getenv("HEADLESS", "true").lower() == "true"
SLOW_MO     = int(os.getenv("SLOW_MO", "120"))
BROWSER     = os.getenv("BROWSER", "chromium")

# ── Rate limiting ─────────────────────────────────────────────────────────────
MIN_DELAY   = float(os.getenv("MIN_DELAY", "2"))
MAX_DELAY   = float(os.getenv("MAX_DELAY", "5"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# ── Proxies ───────────────────────────────────────────────────────────────────
PROXY_ENABLED = os.getenv("PROXY_ENABLED", "false").lower() == "true"
PROXY_LIST    = [p.strip() for p in os.getenv("PROXY_LIST", "").split(",") if p.strip()]

# ── Scraping mode & API providers (ambos opcionales) ─────────────────────────
SCRAPING_MODE    = os.getenv("SCRAPING_MODE", "mock")   # "mock" | "live"
ZENROWS_API_KEY  = os.getenv("ZENROWS_API_KEY", "")
SCRAPERAPI_KEY   = os.getenv("SCRAPERAPI_KEY", "")
CACHE_TTL_HOURS  = int(os.getenv("CACHE_TTL_HOURS", "6"))


# ── Screenshots ───────────────────────────────────────────────────────────────
SCREENSHOTS_ENABLED = os.getenv("SCREENSHOTS_ENABLED", "true").lower() == "true"

# ── Plataformas ───────────────────────────────────────────────────────────────
PLATFORMS = [p.strip() for p in os.getenv("PLATFORMS", "rappi,ubereats,didi").split(",")]

# ── Productos comparables (estandarizados) ───────────────────────────────────
REFERENCE_PRODUCTS = [
    # Fast food
    {"id": "big_mac",       "name": "Big Mac",                  "category": "fast_food",  "restaurant": "McDonald's"},
    {"id": "mccombo_med",   "name": "McCombo Mediano",          "category": "fast_food",  "restaurant": "McDonald's"},
    {"id": "nuggets_10",    "name": "Nuggets 10 piezas",        "category": "fast_food",  "restaurant": "McDonald's"},
    # Retail
    {"id": "coca_500",      "name": "Coca-Cola 500ml",          "category": "retail",     "restaurant": "OXXO"},
    {"id": "agua_1l",       "name": "Agua purificada 1L",       "category": "retail",     "restaurant": "OXXO"},
]

# ── 50 Direcciones representativas de CDMX ───────────────────────────────────
CDMX_ADDRESSES = [
    # ── Zona Premium / Residencial (12) ──────────────────────────────────────
    {"id":"addr_01","zone":"premium",     "label":"Polanco",            "lat":19.4326,"lon":-99.1905,"address":"Presidente Masaryk 61, Polanco, 11560 Ciudad de México"},
    {"id":"addr_02","zone":"premium",     "label":"Santa Fe",           "lat":19.3664,"lon":-99.2596,"address":"Vasco de Quiroga 3800, Santa Fe, 05348 Ciudad de México"},
    {"id":"addr_03","zone":"premium",     "label":"Lomas Chapultepec",  "lat":19.4267,"lon":-99.2112,"address":"Paseo de las Palmas 530, Lomas de Chapultepec, 11000 Ciudad de México"},
    {"id":"addr_04","zone":"premium",     "label":"Condesa",            "lat":19.4116,"lon":-99.1750,"address":"Ámsterdam 92, Condesa, 06140 Ciudad de México"},
    {"id":"addr_05","zone":"premium",     "label":"Roma Norte",         "lat":19.4183,"lon":-99.1619,"address":"Álvaro Obregón 64, Roma Norte, 06700 Ciudad de México"},
    {"id":"addr_21","zone":"premium",     "label":"Bosques Lomas",      "lat":19.3912,"lon":-99.2734,"address":"Paseo de los Tamarindos 400, Bosques de las Lomas, 05120 Ciudad de México"},
    {"id":"addr_22","zone":"premium",     "label":"San Ángel",          "lat":19.3495,"lon":-99.1949,"address":"Amargura 17, San Ángel, 01000 Ciudad de México"},
    {"id":"addr_31","zone":"premium",     "label":"Anzures",            "lat":19.4292,"lon":-99.1800,"address":"Anatole France 13, Anzures, 11590 Ciudad de México"},
    {"id":"addr_32","zone":"premium",     "label":"Lomas Altas",        "lat":19.4108,"lon":-99.2389,"address":"Volcán 150, Lomas Altas, 11950 Ciudad de México"},
    {"id":"addr_33","zone":"premium",     "label":"Lomas Virreyes",     "lat":19.4301,"lon":-99.2093,"address":"Reforma 2631, Lomas Virreyes, 11000 Ciudad de México"},
    {"id":"addr_34","zone":"premium",     "label":"Pedregal S.Ángel",   "lat":19.3312,"lon":-99.2099,"address":"Av. de las Fuentes 42, Pedregal de San Ángel, 01900 Ciudad de México"},
    {"id":"addr_35","zone":"premium",     "label":"Santa Fe Res.",      "lat":19.3521,"lon":-99.2714,"address":"Paseo de las Lomas 100, Santa Fe, 01219 Ciudad de México"},
    # ── Zona Media (13) ───────────────────────────────────────────────────────
    {"id":"addr_06","zone":"media",       "label":"Coyoacán",           "lat":19.3435,"lon":-99.1619,"address":"Av. Universidad 1200, Coyoacán, 04510 Ciudad de México"},
    {"id":"addr_07","zone":"media",       "label":"Del Valle",          "lat":19.3855,"lon":-99.1724,"address":"Insurgentes Sur 1602, Del Valle, 03100 Ciudad de México"},
    {"id":"addr_08","zone":"media",       "label":"Narvarte",           "lat":19.3983,"lon":-99.1621,"address":"Eje 7 Félix Cuevas 14, Narvarte, 03020 Ciudad de México"},
    {"id":"addr_09","zone":"media",       "label":"Tlalpan",            "lat":19.2966,"lon":-99.1713,"address":"Calzada de Tlalpan 4864, Tlalpan, 14000 Ciudad de México"},
    {"id":"addr_10","zone":"media",       "label":"Xochimilco",         "lat":19.2567,"lon":-99.1033,"address":"Morelos 5, Xochimilco, 16000 Ciudad de México"},
    {"id":"addr_23","zone":"media",       "label":"Portales",           "lat":19.3834,"lon":-99.1479,"address":"Calzada de Tlalpan 1220, Portales Nte, 03300 Ciudad de México"},
    {"id":"addr_24","zone":"media",       "label":"Escandón",           "lat":19.4057,"lon":-99.1851,"address":"Av. Revolución 110, Escandón I Secc, 11800 Ciudad de México"},
    {"id":"addr_25","zone":"media",       "label":"Lindavista",         "lat":19.4866,"lon":-99.1268,"address":"Montevideo 363, Lindavista, 07300 Ciudad de México"},
    {"id":"addr_41","zone":"media",       "label":"Mixcoac",            "lat":19.3748,"lon":-99.1877,"address":"Av. Revolución 1425, Mixcoac, 03910 Ciudad de México"},
    {"id":"addr_42","zone":"media",       "label":"Obrera",             "lat":19.4088,"lon":-99.1451,"address":"Av. Chapultepec 480, Obrera, 06800 Ciudad de México"},
    {"id":"addr_43","zone":"media",       "label":"Del Valle Sur",      "lat":19.3920,"lon":-99.1624,"address":"Gabriel Mancera 1053, Del Valle Sur, 03100 Ciudad de México"},
    {"id":"addr_44","zone":"media",       "label":"Tacubaya",           "lat":19.4013,"lon":-99.1984,"address":"Av. Jalisco 40, Tacubaya, 11870 Ciudad de México"},
    {"id":"addr_45","zone":"media",       "label":"Álamos",             "lat":19.3978,"lon":-99.1577,"address":"Eje Central Lázaro Cárdenas 869, Álamos, 03400 Ciudad de México"},
    # ── Zona Corporativa (11) ─────────────────────────────────────────────────
    {"id":"addr_11","zone":"corporativa", "label":"Reforma",            "lat":19.4270,"lon":-99.1672,"address":"Paseo de la Reforma 250, Cuauhtémoc, 06600 Ciudad de México"},
    {"id":"addr_12","zone":"corporativa", "label":"Centro Histórico",   "lat":19.4328,"lon":-99.1332,"address":"Av. Juárez 76, Centro, 06010 Ciudad de México"},
    {"id":"addr_13","zone":"corporativa", "label":"Insurgentes Sur",    "lat":19.3986,"lon":-99.1724,"address":"Insurgentes Sur 800, Nápoles, 03810 Ciudad de México"},
    {"id":"addr_14","zone":"corporativa", "label":"Pedregal",           "lat":19.3218,"lon":-99.2012,"address":"Periférico Sur 4329, Jardines del Pedregal, 01900 Ciudad de México"},
    {"id":"addr_26","zone":"corporativa", "label":"Nuevo Polanco",      "lat":19.4420,"lon":-99.1955,"address":"Blvd. Miguel de Cervantes Saavedra 303, Granada, 11520 Ciudad de México"},
    {"id":"addr_27","zone":"corporativa", "label":"Santa Fe Corp",      "lat":19.3580,"lon":-99.2614,"address":"Prol. Paseo de la Reforma 1015, Santa Fe, 01210 Ciudad de México"},
    {"id":"addr_36","zone":"corporativa", "label":"Tlatelolco",         "lat":19.4518,"lon":-99.1345,"address":"Av. Ricardo Flores Magón 1, Tlatelolco, 06995 Ciudad de México"},
    {"id":"addr_37","zone":"corporativa", "label":"WTC / Nápoles",      "lat":19.3914,"lon":-99.1725,"address":"Montecito 38, Nápoles, 03810 Ciudad de México"},
    {"id":"addr_38","zone":"corporativa", "label":"Doctores",           "lat":19.4139,"lon":-99.1541,"address":"Dr. Balmis 148, Doctores, 06720 Ciudad de México"},
    {"id":"addr_39","zone":"corporativa", "label":"Cuajimalpa",         "lat":19.3622,"lon":-99.2893,"address":"Av. Jalalpa Tepito 2, Cuajimalpa, 05200 Ciudad de México"},
    {"id":"addr_40","zone":"corporativa", "label":"Polanco III Secc",   "lat":19.4381,"lon":-99.2009,"address":"Homero 425, Polanco III Secc, 11560 Ciudad de México"},
    # ── Periferia (14) ───────────────────────────────────────────────────────
    {"id":"addr_15","zone":"periferia",   "label":"Iztapalapa",         "lat":19.3557,"lon":-99.0555,"address":"Av. Ermita Iztapalapa 1200, Iztapalapa, 09010 Ciudad de México"},
    {"id":"addr_16","zone":"periferia",   "label":"Gustavo A. Madero",  "lat":19.4882,"lon":-99.1113,"address":"Av. Instituto Politécnico Nte. 2508, Gustavo A. Madero, 07738 Ciudad de México"},
    {"id":"addr_17","zone":"periferia",   "label":"Azcapotzalco",       "lat":19.4849,"lon":-99.1889,"address":"Av. Azcapotzalco 486, Azcapotzalco, 02000 Ciudad de México"},
    {"id":"addr_18","zone":"periferia",   "label":"Tláhuac",            "lat":19.2785,"lon":-99.0025,"address":"Av. Tláhuac 5420, Tláhuac, 13550 Ciudad de México"},
    {"id":"addr_19","zone":"periferia",   "label":"Milpa Alta",         "lat":19.1884,"lon":-99.0238,"address":"Av. Constitución 1, Villa Milpa Alta, 12000 Ciudad de México"},
    {"id":"addr_20","zone":"periferia",   "label":"Magdalena Contreras","lat":19.3072,"lon":-99.2374,"address":"Av. Luis Cabrera 100, Magdalena Contreras, 10100 Ciudad de México"},
    {"id":"addr_28","zone":"periferia",   "label":"Iztacalco",          "lat":19.3967,"lon":-99.1001,"address":"Av. Té 950, Granjas México, 08400 Ciudad de México"},
    {"id":"addr_29","zone":"periferia",   "label":"Venustiano Carranza","lat":19.4252,"lon":-99.0946,"address":"Fray Servando Teresa de Mier 419, Merced Balbuena, 15810 Ciudad de México"},
    {"id":"addr_30","zone":"periferia",   "label":"Zaragoza",           "lat":19.3940,"lon":-99.0497,"address":"Calz. Ignacio Zaragoza 1200, Tepalcates, 09210 Ciudad de México"},
    {"id":"addr_46","zone":"periferia",   "label":"Nezahualcóyotl",     "lat":19.4108,"lon":-99.0178,"address":"Av. Chimalhuacán 435, Ciudad Nezahualcóyotl, 57000 Estado de México"},
    {"id":"addr_47","zone":"periferia",   "label":"Ecatepec",           "lat":19.5836,"lon":-99.0278,"address":"Av. Central 100, Ecatepec de Morelos, 55000 Estado de México"},
    {"id":"addr_48","zone":"periferia",   "label":"Cuautepec",          "lat":19.5102,"lon":-99.1421,"address":"Av. 5 de Mayo 200, Cuautepec El Alto, 07500 Ciudad de México"},
    {"id":"addr_49","zone":"periferia",   "label":"La Paz",             "lat":19.3536,"lon":-99.0182,"address":"Av. Cuauhtémoc 100, Los Reyes La Paz, 56400 Estado de México"},
    {"id":"addr_50","zone":"periferia",   "label":"Chimalhuacán",       "lat":19.4245,"lon":-99.0008,"address":"Av. Hidalgo 380, Chimalhuacán, 56330 Estado de México"},
]


# Número máximo de direcciones (configurable por env)
MAX_ADDRESSES = int(os.getenv("MAX_ADDRESSES", str(len(CDMX_ADDRESSES))))
CDMX_ADDRESSES = CDMX_ADDRESSES[:MAX_ADDRESSES]

# ── User Agents rotativos ─────────────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
]
