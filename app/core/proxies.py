"""
proxies.py – Proxy support, simple and optional.
Si PROXY_ENABLED=false, el sistema corre directamente sin proxy.
"""
from __future__ import annotations
import itertools
from typing import Optional
from app.core.config import PROXY_ENABLED, PROXY_LIST
from app.core.logger import get_logger

log = get_logger(__name__)


class ProxyRotator:
    """Round-robin sobre lista de proxies. Si está vacía, devuelve None."""

    def __init__(self):
        self._pool = list(PROXY_LIST) if PROXY_ENABLED and PROXY_LIST else []
        self._cycle = itertools.cycle(self._pool) if self._pool else None
        log.info(
            f"Proxies: {len(self._pool)} configurados"
            if self._pool else "Proxies: desactivados (modo directo)"
        )

    def next(self) -> Optional[str]:
        return next(self._cycle) if self._cycle else None

    @property
    def is_active(self) -> bool:
        return bool(self._pool)


proxy_rotator = ProxyRotator()
