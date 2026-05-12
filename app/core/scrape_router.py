"""
scrape_router.py – Orchestrates the scraping fallback chain.

Chain (in order):
  1. LocalCache (fresh)          — zero network, instant
  2. Playwright + block detect   — live scraping, up to PW_MAX_RETRIES attempts
  3. ScraperAPI HTTP fallback    — requires SCRAPERAPI_KEY in .env
  4. LocalCache (stale)          — best-effort: serve old data with a warning
  5. Simulated data              — guaranteed result, never raises

Each step logs its outcome so operators can audit what actually happened.
"""
from __future__ import annotations

import asyncio
import random
from typing import Any, Callable, Optional, TYPE_CHECKING

from app.core.config import SCRAPERAPI_KEY, MAX_RETRIES
from app.core.logger import get_logger
from app.core.cache import LocalCache

if TYPE_CHECKING:
    from app.core.browser import BrowserManager

log = get_logger(__name__)

# ── Source labels (logged + returned alongside records) ────────────────────────
SOURCE_PLAYWRIGHT  = "playwright"
SOURCE_SCRAPERAPI  = "scraperapi"
SOURCE_CACHE       = "cache"
SOURCE_CACHE_STALE = "cache_stale"
SOURCE_SIMULATED   = "simulated"

# Max Playwright retries before escalating to ScraperAPI (< global MAX_RETRIES)
PW_MAX_RETRIES = min(2, MAX_RETRIES)


# ── Sentinel exception ─────────────────────────────────────────────────────────

class BlockDetectedError(Exception):
    """Raised when a page shows block/CAPTCHA/rate-limit signals."""


# ── Block detector ─────────────────────────────────────────────────────────────

_BLOCK_SIGNALS = frozenset({
    "access denied", "captcha", "challenge", "blocked",
    "403 forbidden", "cloudflare", "cf-challenge",
    "robot", "bot detected", "verifica que eres humano",
    "too many requests", "rate limit", "service unavailable",
    "verificación de seguridad",
})


async def detect_block(page: Any) -> bool:
    """
    Returns True when a Playwright page shows anti-bot signals.

    Checks:
      - Page title for block keywords
      - First 3 KB of HTML content for block keywords
      - Suspiciously short content (< 500 chars → probably an error page)

    Conservative: a false positive causes an unnecessary ScraperAPI call,
    which is cheap. A false negative wastes a full Playwright session.
    """
    try:
        title   = (await page.title()).lower()
        content = (await page.content())[:3_000].lower()

        if any(sig in title   for sig in _BLOCK_SIGNALS):
            log.debug(f"Block signal in title: '{title[:80]}'")
            return True
        if any(sig in content for sig in _BLOCK_SIGNALS):
            log.debug("Block signal detected in page content")
            return True
        if len(content) < 500:
            log.debug(f"Suspiciously short page content ({len(content)} chars)")
            return True

        return False
    except Exception as exc:
        log.debug(f"detect_block error (ignoring): {exc}")
        return False


# ── ScraperAPI HTTP fetch ──────────────────────────────────────────────────────

async def scraperapi_fetch(
    url: str,
    *,
    render: bool = True,
    country: str = "mx",
    timeout_s: float = 60.0,
) -> str:
    """
    Fetch a URL through ScraperAPI and return the raw HTML string.

    Args:
        url     : Target URL (Rappi / UberEats / DiDi homepage for that session)
        render  : Request JavaScript rendering on ScraperAPI's side (default True)
        country : Request an IP in this country (default "mx" for México)
        timeout_s: HTTP client timeout in seconds

    Raises:
        httpx.HTTPStatusError : Non-2xx response from ScraperAPI
        httpx.RequestError    : Network-level failures
        RuntimeError          : SCRAPERAPI_KEY not set (checked before calling)
    """
    if not SCRAPERAPI_KEY:
        raise RuntimeError("SCRAPERAPI_KEY not configured")

    import httpx
    params: dict[str, str] = {
        "api_key":      SCRAPERAPI_KEY,
        "url":          url,
        "render":       "true" if render else "false",
        "country_code": country,
    }
    log.info(f"ScraperAPI → {url[:70]}{'…' if len(url) > 70 else ''}")

    async with httpx.AsyncClient(timeout=timeout_s) as client:
        resp = await client.get("http://api.scraperapi.com/", params=params)
        resp.raise_for_status()
        log.debug(f"ScraperAPI response: {len(resp.text):,} chars, HTTP {resp.status_code}")
        return resp.text


# ── Router ─────────────────────────────────────────────────────────────────────

class ScrapeRouter:
    """
    Manages the complete fallback chain for a single (platform, address) scrape.

    Intended to be instantiated once per (platform, address_id) pair inside
    BaseScraper.scrape_with_retry().

    Usage:
        router  = ScrapeRouter(platform="rappi", address_id="addr_01")
        records, source = await router.run(
            base_url       = "https://www.rappi.com.mx",
            address_info   = addr,
            browser_manager= bm,
            pw_scrape_fn   = self._pw_scrape,
            html_scrape_fn = self._html_scrape,
            simulate_fn    = self._generate_simulated_records,
        )
        # source ∈ {playwright, scraperapi, cache, cache_stale, simulated}
    """

    def __init__(self, platform: str, address_id: str) -> None:
        self.platform   = platform
        self.address_id = address_id
        self._cache     = LocalCache()
        self._label     = f"[{platform}/{address_id}]"

    # ── Public entry point ─────────────────────────────────────────────────────

    async def run(
        self,
        *,
        base_url: str,
        address_info: dict,
        browser_manager: "BrowserManager",
        pw_scrape_fn: Callable,      # async (page, addr_info) → list[dict]
        html_scrape_fn: Callable,    # (html_str, addr_info) → list[dict] | None
        simulate_fn: Callable,       # (addr_info) → list[dict]
    ) -> tuple[list[dict[str, Any]], str]:
        """
        Execute the chain and return (records, source_label).

        Never raises — always returns at least simulated data.
        """
        label = self._label

        # ── Step 1: Fresh cache ───────────────────────────────────────────────
        cached = self._cache.get(self.address_id, self.platform)
        if cached:
            log.info(f"{label} Cache hit → {len(cached)} records (skipping network)")
            return cached, SOURCE_CACHE

        # ── Step 2: Playwright (with retry + block detection) ─────────────────
        pw_records = await self._try_playwright(
            base_url, address_info, browser_manager, pw_scrape_fn
        )
        if pw_records is not None:
            self._cache.upsert(self.address_id, self.platform, pw_records)
            return pw_records, SOURCE_PLAYWRIGHT

        # ── Step 3: ScraperAPI HTTP fallback ──────────────────────────────────
        if SCRAPERAPI_KEY:
            sapi_records = await self._try_scraperapi(
                base_url, address_info, html_scrape_fn
            )
            if sapi_records is not None:
                self._cache.upsert(self.address_id, self.platform, sapi_records)
                return sapi_records, SOURCE_SCRAPERAPI
        else:
            log.debug(f"{label} SCRAPERAPI_KEY not set — step 3 skipped")

        # ── Step 4: Stale cache ───────────────────────────────────────────────
        stale = self._cache.get(self.address_id, self.platform, ignore_ttl=True)
        if stale:
            log.warning(f"{label} Serving stale cache ({len(stale)} records)")
            return stale, SOURCE_CACHE_STALE

        # ── Step 5: Simulated (guaranteed) ───────────────────────────────────
        sim = simulate_fn(address_info)
        log.info(f"{label} Simulated → {len(sim)} records")
        return sim, SOURCE_SIMULATED

    # ── Internal helpers ───────────────────────────────────────────────────────

    async def _try_playwright(
        self,
        base_url: str,
        address_info: dict,
        browser_manager: "BrowserManager",
        pw_scrape_fn: Callable,
    ) -> Optional[list[dict]]:
        """
        Attempt Playwright scraping up to PW_MAX_RETRIES times.

        Returns records list on success, None on all failures or block detection.
        """
        label = self._label

        for attempt in range(1, PW_MAX_RETRIES + 1):
            page = None
            try:
                page = await browser_manager.new_page()
                await page.goto(
                    base_url, wait_until="domcontentloaded", timeout=30_000
                )

                if await detect_block(page):
                    log.warning(
                        f"{label} Block detected on attempt {attempt} "
                        f"— escalating to ScraperAPI"
                    )
                    return None  # Don't retry: escalate immediately

                records = await pw_scrape_fn(page, address_info)
                if records:
                    log.success(
                        f"{label} Playwright ✓ ({len(records)} records, "
                        f"attempt {attempt}/{PW_MAX_RETRIES})"
                    )
                    return records

                log.debug(f"{label} Playwright attempt {attempt}: no records extracted")

            except BlockDetectedError:
                log.warning(f"{label} BlockDetectedError — escalating to ScraperAPI")
                return None

            except Exception as exc:
                log.warning(
                    f"{label} Playwright attempt {attempt}/{PW_MAX_RETRIES} "
                    f"failed: {type(exc).__name__}: {exc}"
                )
                if attempt < PW_MAX_RETRIES:
                    backoff = 2 ** attempt + random.uniform(0, 1)
                    log.debug(f"{label} Retrying in {backoff:.1f}s…")
                    await asyncio.sleep(backoff)

            finally:
                if page:
                    try:
                        await page.close()
                    except Exception:
                        pass

        log.warning(f"{label} All Playwright attempts exhausted")
        return None

    async def _try_scraperapi(
        self,
        url: str,
        address_info: dict,
        html_scrape_fn: Callable,
    ) -> Optional[list[dict]]:
        """
        Fetch via ScraperAPI and parse the returned HTML.

        Returns records on success, None if the fetch or parsing fails.
        """
        label = self._label
        try:
            html    = await scraperapi_fetch(url)
            records = html_scrape_fn(html, address_info)
            if records:
                log.success(
                    f"{label} ScraperAPI ✓ ({len(records)} records)"
                )
                return records
            log.debug(
                f"{label} ScraperAPI: HTML received but parser returned nothing"
            )
        except Exception as exc:
            log.warning(f"{label} ScraperAPI failed: {type(exc).__name__}: {exc}")
        return None
