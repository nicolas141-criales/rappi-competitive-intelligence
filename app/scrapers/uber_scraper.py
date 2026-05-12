"""
uber_scraper.py – Scraper para Uber Eats México.

Estrategia:
  1. Navega a ubereats.com
  2. Ingresa dirección y selecciona restaurante
  3. Extrae precios, delivery fee, service fee y ETA

Incluye datos simulados con distribuciones realistas como fallback.
"""
from __future__ import annotations

import random
from typing import Any

try:
    from playwright.async_api import Page, TimeoutError as PlaywrightTimeout
except ImportError:
    Page = None  # type: ignore
    PlaywrightTimeout = Exception  # type: ignore

from app.core.browser import BrowserManager, take_screenshot
from app.core.config import REFERENCE_PRODUCTS
from app.core.logger import get_logger
from app.core.utils import human_delay, parse_eta, parse_price
from app.scrapers.base_scraper import BaseScraper

log = get_logger(__name__)

BASE_URL = "https://www.ubereats.com/mx"


class UberEatsScraper(BaseScraper):
    platform = "ubereats"
    base_url = BASE_URL

    _SELECTORS = {
        "address_input": [
            "input[data-testid='location-typeahead-input']",
            "input[placeholder*='Enter delivery address']",
            "input[placeholder*='Ingresa']",
            "#location-typeahead-home-input",
        ],
        "restaurant_card": [
            "[data-testid='store-card']",
            "a[href*='/mx/store/']",
            "[class*='StoreCard']",
        ],
        "delivery_fee": [
            "[data-testid='delivery-fee']",
            "span[class*='delivery']",
        ],
        "eta": [
            "[data-testid='delivery-time']",
            "span[class*='eta']",
        ],
    }

    async def _pw_scrape(
        self,
        page: Any,
        address_info: dict,
    ) -> list[dict[str, Any]]:
        """Interact with Uber Eats' already-loaded page. Returns [] until DOM parsing is implemented."""
        try:
            await human_delay(1, 2)
            for selector in self._SELECTORS["address_input"]:
                try:
                    el = await page.wait_for_selector(selector, timeout=5_000)
                    if el:
                        await el.click()
                        await el.fill(address_info["address"])
                        await human_delay(1, 1.5)
                        log.debug(f"[ubereats] Address input found: {selector}")
                        break
                except PlaywrightTimeout:
                    continue
            await take_screenshot(page, f"ubereats_{address_info['id']}")
        except Exception as exc:
            log.debug(f"[ubereats] _pw_scrape error: {exc}")
        return []

    def _html_scrape(
        self,
        html: str,
        address_info: dict,
    ) -> None:
        return None

    def _generate_simulated_records(self, address_info: dict) -> list[dict]:
        """
        Datos simulados de Uber Eats con sus patrones característicos:
        - Delivery fees más bajos en zonas premium (estrategia de penetración)
        - Service fee fijo ~15% del subtotal
        - Uber One (similar a Rappi Prime) con envío gratis
        """
        zone = address_info.get("zone", "media")
        records = []

        # Uber Eats tiene fees más competitivos en zonas premium/corporativas
        zone_profile = {
            "premium":     {"base_mult": 1.12, "fee": 15, "service_pct": 0.15, "eta_base": 22},
            "media":       {"base_mult": 1.05, "fee": 19, "service_pct": 0.15, "eta_base": 32},
            "corporativa": {"base_mult": 1.10, "fee": 12, "service_pct": 0.15, "eta_base": 20},
            "periferia":   {"base_mult": 0.98, "fee": 28, "service_pct": 0.15, "eta_base": 48},
        }
        zp = zone_profile.get(zone, zone_profile["media"])

        # Precios Uber Eats (ligeramente más altos que en tienda)
        product_prices = {
            "big_mac":     {"price": 145.0,  "restaurant": "McDonald's", "category": "fast_food"},
            "mccombo_med": {"price": 178.0,  "restaurant": "McDonald's", "category": "fast_food"},
            "nuggets_10":  {"price": 125.0,  "restaurant": "McDonald's", "category": "fast_food"},
            "coca_500":    {"price": 30.0,   "restaurant": "OXXO",       "category": "retail"},
            "agua_1l":     {"price": 20.0,   "restaurant": "OXXO",       "category": "retail"},
        }

        # Uber One: 0 delivery fee
        has_uber_one  = random.random() < 0.25
        delivery_fee  = 0.0 if has_uber_one else round(zp["fee"] + random.uniform(-3, 4), 2)
        promo_label   = "Uber One – Envío gratis" if has_uber_one else random.choice([
            "20% OFF primer pedido", "Envío gratis en tu primer pedido", "", "", ""
        ])

        eta_min = max(10, zp["eta_base"] + random.randint(-8, 8))
        eta_max = eta_min + random.randint(5, 12)

        for prod in REFERENCE_PRODUCTS:
            prod_id  = prod["id"]
            prod_ref = product_prices.get(prod_id, {})
            if not prod_ref:
                continue

            base_price  = round(prod_ref["price"] * zp["base_mult"] + random.uniform(-2, 4), 2)
            service_fee = round(base_price * zp["service_pct"], 2)
            discount    = round(base_price * 0.20, 2) if "20%" in promo_label else 0.0
            final       = round(base_price + delivery_fee + service_fee - discount, 2)

            records.append(self._make_record(
                address_info = address_info,
                restaurant   = prod_ref["restaurant"],
                product      = prod["name"],
                category     = prod_ref["category"],
                base_price   = base_price,
                delivery_fee = delivery_fee,
                service_fee  = service_fee,
                discount     = discount,
                final_price  = final,
                eta_min      = eta_min,
                eta_max      = eta_max,
                promo_label  = promo_label,
                available    = True,
            ))

        return records
