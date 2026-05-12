"""
cache.py – Local record cache backed by competitive_data.csv.

Cache key  : (address_id, platform)
Freshness  : configurable TTL via CACHE_TTL_HOURS (default 6 h)
Persistence: the existing CSV is the backing store — no separate DB needed.

The cache is a read-through layer: if fresh data exists for a given
(platform, address) pair the router skips all network calls for that slot.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import pandas as pd

from app.core.config import CACHE_TTL_HOURS, COMPETITIVE_CSV
from app.core.logger import get_logger

log = get_logger(__name__)


class LocalCache:
    """Thin wrapper around the CSV data store that provides cache semantics."""

    # ── Read ──────────────────────────────────────────────────────────────────

    def get(
        self,
        address_id: str,
        platform: str,
        ignore_ttl: bool = False,
    ) -> Optional[list[dict]]:
        """
        Return cached records for (address_id, platform) when fresh.

        Returns None when:
          - CSV doesn't exist
          - No rows match the key
          - Data is older than CACHE_TTL_HOURS (unless ignore_ttl=True)
        """
        if not COMPETITIVE_CSV.exists():
            return None

        try:
            df = pd.read_csv(COMPETITIVE_CSV, encoding="utf-8-sig")
        except Exception as exc:
            log.warning(f"Cache read error: {exc}")
            return None

        mask = (df["address_id"] == address_id) & (df["platform"] == platform)
        sub  = df[mask]

        if sub.empty:
            return None

        if not ignore_ttl:
            try:
                latest = pd.to_datetime(sub["timestamp"], utc=True).max()
                now    = datetime.now(timezone.utc)
                age_h  = (now - latest).total_seconds() / 3600
                if age_h > CACHE_TTL_HOURS:
                    log.debug(
                        f"Cache stale ({age_h:.1f}h > {CACHE_TTL_HOURS}h) "
                        f"for {platform}/{address_id}"
                    )
                    return None
            except Exception:
                return None

        records = sub.to_dict(orient="records")
        log.debug(f"Cache hit — {len(records)} records for {platform}/{address_id}")
        return records

    # ── Write ─────────────────────────────────────────────────────────────────

    def upsert(
        self,
        address_id: str,
        platform: str,
        records: list[dict],
    ) -> None:
        """
        Replace records for (address_id, platform) in the CSV.

        Keeps all other rows untouched — acts like an upsert.
        This ensures the CSV never accumulates stale duplicates.
        """
        if not records:
            return

        try:
            if COMPETITIVE_CSV.exists():
                df   = pd.read_csv(COMPETITIVE_CSV, encoding="utf-8-sig")
                keep = ~(
                    (df["address_id"] == address_id) & (df["platform"] == platform)
                )
                df = df[keep]
            else:
                df = pd.DataFrame()

            new_df = pd.DataFrame(records)
            df     = pd.concat([df, new_df], ignore_index=True)
            COMPETITIVE_CSV.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(COMPETITIVE_CSV, index=False, encoding="utf-8-sig")
            log.debug(f"Cache updated — {len(records)} records for {platform}/{address_id}")

        except Exception as exc:
            log.warning(f"Cache write error: {exc}")
