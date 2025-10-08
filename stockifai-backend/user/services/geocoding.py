"""Utilities para geocodificar direcciones usando Nominatim (OpenStreetMap)."""

from __future__ import annotations

import logging
from typing import Optional, Tuple

import requests

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "stockifai-backend/1.0"

def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """Retorna (lat, lon) para la dirección indicada o ``None`` si no se pudo geocodificar."""
    if not address:
        return None

    params = {
        "q": address,
        "format": "json",
        "limit": 1,
        "addressdetails": 0,
    }
    headers = {"User-Agent": USER_AGENT}

    try:
        resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:  # pragma: no cover - dependiente de red
        logger.warning("No se pudo geocodificar la dirección '%s': %s", address, exc)
        return None
    except ValueError as exc:  # pragma: no cover - JSON inesperado
        logger.warning("Respuesta inválida de Nominatim para '%s': %s", address, exc)
        return None

    if not data:
        logger.info("Nominatim no encontró resultados para '%s'", address)
        return None

    try:
        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
    except (KeyError, TypeError, ValueError) as exc:  # pragma: no cover
        logger.warning("Formato inesperado al parsear coordenadas para '%s': %s", address, exc)
        return None

    return lat, lon
