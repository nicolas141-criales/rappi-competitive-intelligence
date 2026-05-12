"""
didi_scraper.py – Scraper para DiDi Food México.

Estrategia:
  1. Navega a food.didiglobal.com/mx
  2. Ingresa dirección de entrega
  3. Extrae precios, fees y tiempos

Datos simulados con patrones característicos de DiDi Food:
- Precios más bajos (estrategia de penetración de mercado)
- Delivery fees competitivos en zonas medias y periferia
- Menos cobertura en zonas premium
"""
from __future__ import annotations

import random
from typing import Any

try:
    from playwright.async_api import TimeoutError as PlaywrightTimeout
except ImportError:
    PlaywrightTimeout = Exception  # type: ignore

from app.core.browser import BrowserManager, take_screenshot
from app.core.config import REFERENCE_PRODUCTS
from app.core.logger import get_logger
from app.core.utils import human_delay
from app.scrapers.base_scraper import BaseScraper

log = get_logger(__name__)

BASE_URL = "https://food.didiglobal.com/mx"


class DiDiScraper(BaseScraper):
    platform = "didi"
    base_url = BASE_URL

    _SELECTORS = {
        "address_input": [
            "input[placeholder*='Ingresa tu dirección']",
            "input[placeholder*='dirección']",
            "[class*='address-input']",
            "input[type='text']",
        ],
        "delivery_fee": [
            "[class*='delivery-fee']",
            "span[class*='fee']",
        ],
        "eta": [
            "[class*='delivery-time']",
            "span[class*='time']",
        ],
    }

    async def _pw_scrape(
        self,
        page: Any,
        address_info: dict,
    ) -> list[dict[str, Any]]:
        """Interact with DiDi Food's already-loaded page. Returns [] until DOM parsing is implemented."""
        try:
            await human_delay(1, 2)
            for selector in self._SELECTORS["address_input"]:
                try:
                    el = await page.wait_for_selector(selector, timeout=5_000)
                    if el:
                        await el.click()
                        await el.fill(address_info["address"])
                        await human_delay(1, 1.5)
                        log.debug(f"[didi] Address input: {selector}")
                        break
                except PlaywrightTimeout:
                    continue
            await take_screenshot(page, f"didi_{address_info['id']}")
        except Exception as exc:
            log.debug(f"[didi] _pw_scrape error: {exc}")
        return []

    def _html_scrape(
        self,
        html: str,
        address_info: dict,
    ) -> None:
        return None

    def _generate_simulated_records(self, address_info: dict) -> list[dict]:
        """
        Datos simulados de DiDi Food con sus patrones distintivos:
        - Precios ~5-8% más bajos que competencia (estrategia agresiva)
        - Delivery fees competitivos, especialmente en zonas medias
        - Menos cobertura en zonas premium y periferia extrema
        - Muchas promociones de descuento para ganar cuota de mercado
        """
        zone    = address_info.get("zone", "media")
        records = []

        # DiDi tiene cobertura limitada en periferia extrema
        coverage_rate = {"premium": 0.80, "media": 0.95, "corporativa": 0.85, "periferia": 0.65}
        if random.random() > coverage_rate.get(zone, 0.80):
            log.info(f"[didi] No coverage for zone '{zone}' – {address_info['label']}")
            return []  # Sin cobertura en esta zona

        zone_profile = {
            "premium":     {"base_mult": 1.03, "fee": 18, "service": 8,  "eta_base": 30},
            "media":       {"base_mult": 0.97, "fee": 16, "service": 7,  "eta_base": 38},
            "corporativa": {"base_mult": 1.00, "fee": 14, "service": 8,  "eta_base": 28},
            "periferia":   {"base_mult": 0.93, "fee": 22, "service": 6,  "eta_base": 52},
        }
        zp = zone_profile.get(zone, zone_profile["media"])

        # DiDi Food tiene precios base más bajos (sin markup agresivo)
        product_prices = {
            "big_mac":     {"price": 132.0,  "restaurant": "McDonald's", "category": "fast_food"},
            "mccombo_med": {"price": 162.0,  "restaurant": "McDonald's", "category": "fast_food"},
            "nuggets_10":  {"price": 112.0,  "restaurant": "McDonald's", "category": "fast_food"},
            "coca_500":    {"price": 26.0,   "restaurant": "OXXO",       "category": "retail"},
            "agua_1l":     {"price": 17.0,   "restaurant": "OXXO",       "category": "retail"},
        }

        # DiDi es muy agresivo en descuentos para adquirir usuarios
        promo_options = [
            ("30% OFF primeros 3 pedidos", 0.30),
            ("DiDi Food Pass – Envío gratis", 0.0),
            ("25% OFF en tu pedido", 0.25),
            ("Envío gratis hoy", 0.0),
            ("", 0.0),
        ]
        promo_label, promo_pct = random.choices(
            promo_options,
            weights=[25, 20, 15, 15, 25],
            k=1
        )[0]

        # DiDi Pass: envío gratis (~20% usuarios)
        has_didi_pass = "Pass" in promo_label or "Envío gratis" in promo_label
        delivery_fee  = 0.0 if has_didi_pass else round(zp["fee"] + random.uniform(-3, 3), 2)
        service_fee   = round(zp["service"] + random.uniform(-1, 1), 2)

        eta_min = max(12, zp["eta_base"] + random.randint(-10, 10))
        eta_max = eta_min + random.randint(5, 15)

        for prod in REFERENCE_PRODUCTS:
            prod_id  = prod["id"]
            prod_ref = product_prices.get(prod_id, {})
            if not prod_ref:
                continue

            base_price = round(prod_ref["price"] * zp["base_mult"] + random.uniform(-2, 2), 2)
            discount   = round(base_price * promo_pct, 2) if promo_pct > 0 else 0.0
            final      = round(base_price + delivery_fee + service_fee - discount, 2)

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
