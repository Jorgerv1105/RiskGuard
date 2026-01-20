from __future__ import annotations

from dataclasses import dataclass


def risk_level(score: int) -> str:
    """Clasificacion de riesgo segun escala 1-25.

    - 1-5: Bajo
    - 6-10: Medio
    - 11-15: Alto
    - 16-25: Critico
    """
    if score <= 5:
        return "Bajo"
    if score <= 10:
        return "Medio"
    if score <= 15:
        return "Alto"
    return "Critico"


def cid_to_impact(cid_total: int) -> int:
    """Traduce CID total (3-9) a impacto (1,3,5) segun metodologia."""
    if cid_total <= 4:
        return 1
    if cid_total <= 7:
        return 3
    return 5


def severity_rank(level: str) -> int:
    order = {"Bajo": 1, "Medio": 2, "Alto": 3, "Critico": 4}
    return order.get(level, 0)


@dataclass
class KPI:
    label: str
    value: str
    note: str | None = None
