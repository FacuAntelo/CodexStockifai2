"""Utilidades para normalizar teléfonos"""

from __future__ import annotations

import re
from typing import Optional

DEFAULT_COUNTRY_CODE = "54"  # Argentina como default


def normalize_local_phone(phone: str) -> str:
    """Normaliza un teléfono eliminando espacios extra."""
    return re.sub(r"\s+", " ", phone).strip()


def to_e164_digits(phone: str, country_code: str = DEFAULT_COUNTRY_CODE) -> Optional[str]:
    """Convierte un número local a dígitos E164 sin el prefijo +.

    No pretende ser perfecto pero cubre los casos comunes de Argentina.
    """
    if not phone:
        return None

    digits = re.sub(r"[^0-9]", "", phone)
    if not digits:
        return None

    # quitar prefijo 00 internacional
    if digits.startswith("00"):
        digits = digits[2:]

    # quitar prefijo + si quedó
    digits = digits.lstrip("+")

    # quitar 0 inicial típico de Argentina
    if digits.startswith("0"):
        digits = digits[1:]

    # quitar prefijo 15 si corresponde
    if digits.startswith("15") and len(digits) > 8:
        digits = digits[2:]

    if not digits.startswith(country_code):
        digits = f"{country_code}{digits}"

    return digits
