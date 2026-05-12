"""
base_scraper.py – Clase base abstracta para todos los scrapers.
Define la interfaz y delega el fallback chain a ScrapeRouter.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from app.core.browser import BrowserManager
from app.core.config import COMPETITIVE_CSV, COMPETITIVE_JSON
from app.core.logger import get_logger
from app.core.scrape_router import ScrapeRouter
from app.core.utils import append_record, human_delay, now_iso

log = get_logger(__name__)


class BaseScraper(ABC):
    """
    Clase base para scrapers.
    Subclases implementan _pw_scrape, _html_scrape, _generate_simulated_records.
    ScrapeRouter maneja el chain: cache → Playwright → ScraperAPI → cache stale → sim.
    """

    platform: str = "unknown"
    base_url: str = ""

    def __init__(self):
        self._results: list[dict[str, Any]] = []

    # ── Plantilla de registro ─────────────────────────────────────────────────
    def _make_record(
        self,
        address_info: dict,
        restaurant: str,
        product: str,
        base_price: float = 0.0,
        delivery_fee: float = 0.0,
        service_fee: float = 0.0,
        discount: float = 0.0,
        final_price: float = 0.0,
        eta_min: int = 0,
        eta_max: int = 0,
        promo_label: str = "",
        available: bool = True,
        screenshot_path: str = "",
        category: str = "",
        **extra,
    ) -> dict[str, Any]:
        record = {
            "platform":        self.platform,
            "address_id":      address_info.get("id", ""),
            "address_label":   address_info.get("label", ""),
            "zone":            address_info.get("zone", ""),
            "address":         address_info.get("address", ""),
            "lat":             address_info.get("lat", 0.0),
            "lon":             address_info.get("lon", 0.0),
            "restaurant":      restaurant,
            "product":         product,
            "category":        category,
            "base_price":      base_price,
            "delivery_fee":    delivery_fee,
            "service_fee":     service_fee,
            "discount":        discount,
            "final_price":     final_price if final_price else round(base_price + delivery_fee + service_fee - discount, 2),
            "eta_min":         eta_min,
            "eta_max":         eta_max,
            "promo_label":     promo_label,
            "available":       available,
            "screenshot_path": screenshot_path,
            "timestamp":       now_iso(),
        }
        record.update(extra)
        return record

    # ── Abstract interface ────────────────────────────────────────────────────
    @abstractmethod
    async def _pw_scrape(
        self,
        page: Any,
        address_info: dict,
    ) -> list[dict[str, Any]]:
        """
        Extract records from an already-navigated Playwright page.
        ScrapeRouter handles page creation, goto, and closing.
        Return empty list when live extraction is not yet implemented.
        """
        ...

    @abstractmethod
    def _html_scrape(
        self,
        html: str,
        address_info: dict,
    ) -> Optional[list[dict[str, Any]]]:
        """Parse ScraperAPI HTML. Return None when not implemented."""
        ...

    @abstractmethod
    def _generate_simulated_records(
        self,
        address_info: dict,
    ) -> list[dict[str, Any]]:
        """Generate realistic simulated data for this platform."""
        ...

    # ── Entry point — delegates to ScrapeRouter ───────────────────────────────
    async def scrape_with_retry(
        self,
        address_info: dict,
        browser_manager: BrowserManager,
    ) -> list[dict[str, Any]]:
        router = ScrapeRouter(
            platform   = self.platform,
            address_id = address_info["id"],
        )
        records, source = await router.run(
            base_url        = self.base_url,
            address_info    = address_info,
            browser_manager = browser_manager,
            pw_scrape_fn    = self._pw_scrape,
            html_scrape_fn  = self._html_scrape,
            simulate_fn     = self._generate_simulated_records,
        )
        self._results.extend(records)
        for r in records:
            append_record(r, COMPETITIVE_CSV, COMPETITIVE_JSON)
        log.info(
            f"[{self.platform}] '{address_info['label']}' → "
            f"{len(records)} records [{source}]"
        )
        return records

    # ── Ejecutar sobre múltiples direcciones ──────────────────────────────────
    async def run(self, addresses: list[dict]) -> list[dict[str, Any]]:
        """Ejecuta el scraper sobre todas las direcciones de forma secuencial."""
        async with BrowserManager() as bm:
            for addr in addresses:
                await self.scrape_with_retry(addr, bm)
                await human_delay()
        log.info(f"[{self.platform}] Run complete. Total records: {len(self._results)}")
        return self._results

    @property
    def results(self) -> list[dict[str, Any]]:
        return self._results
