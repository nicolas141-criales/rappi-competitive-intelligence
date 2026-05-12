"""
browser.py – Playwright con stealth básico y soporte opcional ZenRows.

Filosofía: simple, robusto, suficiente para competitive intelligence.
No es un sistema anti-bot enterprise — es scraping controlado y estratégico.
"""
from __future__ import annotations
import os
import random
from typing import Optional, TYPE_CHECKING

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Browser = BrowserContext = Page = Playwright = None  # type: ignore

from app.core.config import (
    BROWSER, HEADLESS, SLOW_MO,
    SCREENSHOTS_DIR, SCREENSHOTS_ENABLED,
    USER_AGENTS, ZENROWS_API_KEY, SCRAPERAPI_KEY,
)
from app.core.logger import get_logger
from app.core.proxies import proxy_rotator
from app.core.utils import now_iso

log = get_logger(__name__)

VIEWPORTS = [
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
    {"width": 1280, "height": 800},
]

# Script mínimo de stealth — elimina el fingerprint de WebDriver
_STEALTH = """
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'plugins',   {get: () => [1,2,3]});
    Object.defineProperty(navigator, 'languages', {get: () => ['es-MX','es']});
    window.chrome = {runtime: {}};
"""


class BrowserManager:
    """
    Context manager async para Playwright.

    - Stealth básico (UA rotation, fingerprint mínimo)
    - Proxy opcional via PROXY_LIST en .env
    - ZenRows opcional via ZENROWS_API_KEY en .env
    - Si todo falla: el sistema cae al modo demo (fallback en main.py)

    Uso:
        async with BrowserManager() as bm:
            page = await bm.new_page()
    """

    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None

    async def __aenter__(self) -> "BrowserManager":
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError(
                "Playwright no instalado.\n"
                "Instala: pip install playwright && playwright install chromium\n"
                "O usa: python app/main.py --mock"
            )

        self._playwright = await async_playwright().start()
        launcher = getattr(self._playwright, BROWSER)

        launch_kwargs: dict = {
            "headless": HEADLESS,
            "slow_mo": SLOW_MO,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--lang=es-MX",
            ],
        }

        # Proxy opcional
        proxy = proxy_rotator.next()
        if proxy:
            from urllib.parse import urlparse
            p = urlparse(proxy)
            cfg: dict = {"server": f"{p.scheme}://{p.hostname}:{p.port}"}
            if p.username: cfg["username"] = p.username
            if p.password: cfg["password"] = p.password
            launch_kwargs["proxy"] = cfg
            log.info(f"Proxy activo: {p.hostname}:{p.port}")

        self._browser = await launcher.launch(**launch_kwargs)
        log.info(f"Browser listo ({BROWSER}, headless={HEADLESS})")
        return self

    async def __aexit__(self, *_) -> None:
        if self._browser: await self._browser.close()
        if self._playwright: await self._playwright.stop()

    async def new_page(self) -> Page:
        """Página con fingerprint aleatorio y bloqueo de recursos innecesarios."""
        ctx = await self._browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport=random.choice(VIEWPORTS),
            locale="es-MX",
            timezone_id="America/Mexico_City",
            ignore_https_errors=True,
            extra_http_headers={
                "Accept-Language": "es-MX,es;q=0.9",
                "DNT": "1",
            },
        )
        await ctx.add_init_script(_STEALTH)

        page = await ctx.new_page()

        # Bloquear imágenes/fonts → carga más rápida
        async def _route(route, req):
            if req.resource_type in {"image", "font", "media", "stylesheet"}:
                await route.abort()
            else:
                await route.continue_()
        await page.route("**/*", _route)

        return page


# ── API wrappers — transparentes y opcionales ────────────────────────────────
# El scraper llama siempre a wrap_url(url) y no sabe qué provider se usa.

def zenrows_wrap(url: str, js: bool = True) -> str:
    """Redirige via ZenRows si ZENROWS_API_KEY está configurado."""
    if not ZENROWS_API_KEY:
        return url
    log.debug(f"ZenRows → {url[:60]}…")
    return (f"https://api.zenrows.com/v1/?apikey={ZENROWS_API_KEY}"
            f"&url={url}&js_render={'true' if js else 'false'}&antibot=true")


def scraperapi_wrap(url: str, js: bool = True, country: str = "mx") -> str:
    """Redirige via ScraperAPI si SCRAPERAPI_KEY está configurado."""
    if not SCRAPERAPI_KEY:
        return url
    log.debug(f"ScraperAPI → {url[:60]}…")
    return (f"http://api.scraperapi.com/?api_key={SCRAPERAPI_KEY}"
            f"&url={url}&render={'true' if js else 'false'}&country_code={country}")


def wrap_url(url: str, js: bool = True) -> str:
    """
    Punto de entrada único para wrappers de API.
    Prioridad: ZenRows → ScraperAPI → URL original (Playwright directo).
    El scraper solo llama a wrap_url() y no gestiona providers.
    """
    if ZENROWS_API_KEY:
        return zenrows_wrap(url, js)
    if SCRAPERAPI_KEY:
        return scraperapi_wrap(url, js)
    return url  # Playwright directo


# ── Screenshot helper ─────────────────────────────────────────────────────────

async def take_screenshot(page: Optional[Page], name: str) -> Optional[str]:
    if not (PLAYWRIGHT_AVAILABLE and SCREENSHOTS_ENABLED and page):
        return None
    try:
        path = SCREENSHOTS_DIR / f"{name}_{now_iso().replace(':', '-')}.png"
        await page.screenshot(path=str(path), full_page=True)
        log.debug(f"Screenshot → {path.name}")
        return str(path)
    except Exception as exc:
        log.debug(f"Screenshot skip: {exc}")
        return None
