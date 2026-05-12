# Rappi Competitive Intelligence Platform

**Plataforma enterprise de inteligencia competitiva** para equipos de Strategy, Pricing y Operations.
Monitorea y analiza Rappi vs. Uber Eats vs. DiDi Food en tiempo real a través de 50 puntos de captura en CDMX.

> *"El objetivo no es scrapear internet. Es construir evidencia estratégica suficiente para tomar decisiones de negocio."*

---

## Problema de Negocio

Los equipos de Pricing y Strategy en Rappi necesitan responder preguntas concretas:

- ¿Cuánto cobra DiDi de delivery fee en Polanco vs. Iztapalapa?
- ¿En qué zonas está Uber Eats agrediendo con envío gratis?
- ¿Hay subcotización de precio en segmentos fast food específicos?
- ¿Cómo varía el ETA de Rappi frente al mercado en hora pico?

Estas preguntas requieren datos frescos, estructurados y georreferenciados — no una hoja de cálculo manual.

---

## Alcance del Sistema

| Dimensión | Detalle |
|---|---|
| **Plataformas** | Rappi · Uber Eats · DiDi Food |
| **Geografía** | 50 direcciones representativas de CDMX, 4 zonas |
| **Zonas** | Premium · Corporativa · Media · Periferia |
| **Productos** | Big Mac, McCombo Mediano, Nuggets 10pz, Coca-Cola 500ml, Agua 1L |
| **Categorías** | Fast Food (McDonald's) · Retail (OXXO) |
| **Señales** | Precio · Fee · ETA · Descuentos · Estrategia promocional |

Las 50 direcciones fueron seleccionadas para representar los distintos corredores económicos de CDMX: desde Polanco y Santa Fe hasta Iztapalapa, Ecatepec y Milpa Alta.

---

## Dashboard Interactivo — 8 Páginas

| Página | Contenido |
|---|---|
| **Resumen Ejecutivo** | KPIs clave, scores competitivos, señales de prioridad alta |
| **Consola de Precios** | Battlecards de producto, análisis de brecha, filtros por zona |
| **Benchmarking Operativo** | Arquitectura de fees, rendimiento ETA, fricción operativa |
| **Centro de Promociones** | Densidad promo, estrategia por plataforma, matriz zona × táctica |
| **Monitor Territorial** | Mapa de CDMX con inteligencia por zona, ranking de riesgo |
| **Galería de Evidencias** | Screenshots de scraping en vivo, registro de señales con timestamp |
| **Explorador de Datos** | Tabla interactiva con filtros, preview de datos brutos |
| **Centro de Exportación** | Paquetes descargables: CSV, JSON, HTML briefs ejecutivos |

---

## Arquitectura Técnica

```
app/
├── core/
│   ├── config.py           # Variables de entorno centralizadas
│   ├── browser.py          # Playwright + stealth + ScraperAPI fallback
│   ├── proxies.py          # Proxy rotation
│   └── logger.py           # Logging estructurado
├── scrapers/
│   ├── base_scraper.py     # Clase base: retry, delay adaptativo, fallback
│   ├── rappi_scraper.py
│   ├── uber_scraper.py
│   └── didi_scraper.py
├── analytics/
│   ├── insights.py         # Motor de señales estratégicas con severity scoring
│   ├── price_analysis.py
│   ├── fee_analysis.py
│   └── geo_analysis.py
├── dashboard/
│   ├── dashboard.py        # Router principal — 8 páginas
│   ├── components.py       # Componentes UI reutilizables
│   └── theme.py            # Design system light mode
└── main.py                 # CLI: --mock | --live
```

---

## Stack Tecnológico

| Componente | Tecnología | Por qué |
|---|---|---|
| **Browser automation** | Playwright (Chromium) | Rappi y Uber Eats son SPAs con React — los precios se cargan vía JS dinámico, HTTP scraping no aplica |
| **Fallback API** | ScraperAPI | Proxy rotation gestionado si el scraping directo es bloqueado; integración transparente |
| **Dashboard** | Streamlit | Despliegue rápido, componentes reactivos, compatible con Plotly sin overhead de frontend |
| **Visualización** | Plotly | Gráficos interactivos de alta calidad, exportable como imagen |
| **Data layer** | Pandas + SQLite | Procesamiento local, sin dependencias de infraestructura externa |
| **Containerización** | Docker Compose | Reproducibilidad del entorno para el equipo evaluador |
| **Cache** | `@st.cache_data` + archivo local | Cache-first: el dashboard opera con datos locales incluso sin acceso a red |

---

## Estrategia de Scraping y Resiliencia

### Por qué Playwright, no HTTP

Rappi, Uber Eats y DiDi Food son aplicaciones React con carga asincrónica de datos.
Los precios, fees y disponibilidad se renderizan en el browser, no en el HTML inicial.
Playwright lanza un browser real — captura el DOM como lo ve un usuario.

### Scraping controlado, no masivo

Las plataformas detectan patrones de alta frecuencia y bloquean por IP o rate limit.
La estrategia del sistema prioriza **calidad sobre volumen**:

- Delays adaptativos por request (configurables: default 2–5 segundos)
- User-Agent rotation (Chrome, Firefox, Safari — 5 perfiles)
- `navigator.webdriver = undefined` para bypass de detección básica
- Locale y timezone de CDMX
- Bloqueo de recursos innecesarios (imágenes, fuentes) para velocidad
- `HEADLESS=false` opcional (browser visible es menos detectable)

### Jerarquía de fallback — el sistema nunca falla

```
1. Scraping en vivo (Playwright directo)
   ↓ si bloqueado
2. ScraperAPI (proxy gestionado, bypass automático)
   ↓ si no configurado
3. Cache local (último scraping exitoso)
   ↓ si no existe
4. Datos demo estadísticamente calibrados
   ↓ siempre disponible
```

El dashboard comunica el modo activo en todo momento. No hay estado silencioso.

### Mock mode — demos estables

Los datos demo (`--mock`) son estadísticamente calibrados con rangos reales del mercado CDMX:

| Señal | Rango calibrado |
|---|---|
| Big Mac precio | $89–$120 MXN según zona |
| Fee de envío | Rappi $15–$45 · Uber Eats $10–$39 · DiDi $0–$35 MXN |
| ETA | Premium 18–25 min · Media 22–35 min · Periferia 30–55 min |
| Cobertura DiDi | Parcial en periferia (realista) |
| Tasa promo | 15–45% según plataforma y zona |

---

## Inteligencia Estratégica

El motor de análisis genera señales automáticas con **severity scoring** (CRITICAL / HIGH / MEDIUM / LOW) y **confidence scoring** en cada ejecución:

- **Subcotización de precio** — competidor ofreciendo el mismo SKU significativamente más barato
- **Ventaja ETA** — competitor con ventaja sostenida de velocidad de entrega en una zona
- **Promo activa** — escalada de densidad promocional en corredores clave
- **Envío gratis** — táctica de eliminación de fee en zonas estratégicas

Cada señal incluye: plataforma, zona, producto afectado, magnitud del gap y recomendación de acción.

---

## Setup y Ejecución

### Prerequisitos

```bash
Python 3.11+
pip install -r requirements.txt
playwright install chromium
```

### Variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
SCRAPING_MODE=mock          # mock | live
HEADLESS=true               # true | false (false = más stealth)
MIN_DELAY=2                 # segundos mínimos entre requests
MAX_DELAY=5                 # segundos máximos entre requests
MAX_ADDRESSES=10            # zonas a scrapear en modo live
SCREENSHOTS_ENABLED=true    # guardar evidencia visual
SCRAPERAPI_KEY=             # opcional — fallback API si Playwright es bloqueado
PROXY_ENABLED=false         # activar proxy rotation manual
PROXY_LIST=                 # proxies separados por coma
```

### Ejecución

```bash
# Modo demo — recomendado para evaluación (sin acceso a internet)
python app/main.py --mock

# Modo live — scraping real (requiere playwright install chromium)
python app/main.py --live --addresses 5

# Lanzar dashboard
streamlit run app/dashboard/dashboard.py --server.port 8502
```

Abre → `http://localhost:8502`

### Docker (entorno reproducible)

```bash
docker-compose up --build
```

El stack levanta el dashboard en el puerto 8502 con datos demo precargados.

---

## Outputs Generados

| Archivo | Contenido |
|---|---|
| `app/data/processed/competitive_data.csv` | Dataset principal con todos los registros |
| `app/data/processed/competitive_data.json` | Versión JSON del dataset |
| `app/data/processed/insights.json` | Señales estratégicas con severity y confidence |
| `app/data/screenshots/` | Evidencia visual de cada sesión de scraping |
| `app/data/competitive.db` | SQLite local para queries ad-hoc |

Desde el dashboard, el equipo puede exportar directamente:

- **Brief Ejecutivo HTML** — resumen listo para presentación
- **Brief de Precios HTML** — análisis de brecha por producto y zona
- **Brief Operativo HTML** — arquitectura de fees y ETA
- **Brief Promocional HTML** — estrategia y arquetipos por plataforma
- **Reporte Territorial HTML** — inteligencia geográfica por zona

---

## Decisiones de Diseño

| Decisión | Alternativa descartada | Razón |
|---|---|---|
| Playwright (browser real) | HTTP scraping | SPAs con React: sin JS no hay datos |
| Mock mode como primera línea | Forzar scraping live | La demo nunca depende de conectividad |
| ScraperAPI como fallback | Infraestructura propia de proxies | Costo-beneficio — sin sobre-ingeniería |
| Dashboard desacoplado del scraper | Proceso unificado | Resiliencia e independencia operativa |
| 50 zonas representativas vs. cobertura total | Scraping masivo de toda CDMX | Datos de calidad > volumen ruidoso |
| Severity + confidence scoring | Alertas binarias | Priorización ejecutiva accionable |

---

## Responsible Scraping

Este sistema fue diseñado con ética técnica explícita:

- Delays conservadores — nunca por debajo de 2 segundos entre requests
- Sin scraping de datos personales o privados de usuarios
- Scraping limitado a información pública de catálogo y precios
- Rotación de User-Agents para comportamiento humano, no para evasión masiva
- Modo mock disponible para cualquier evaluación sin generar carga en los servidores

El objetivo es inteligencia competitiva responsable, no extracción masiva de datos.

---

*Rappi Competitive Intelligence Platform — Interno, solo uso estratégico.*
