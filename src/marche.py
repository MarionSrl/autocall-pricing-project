"""Paramètres de marché partagés par les figures du mémoire."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ParametresMarche:
    s0: float = 100.0
    r: float = 0.025
    sigma: float = 0.18
    q: float = 0.03
