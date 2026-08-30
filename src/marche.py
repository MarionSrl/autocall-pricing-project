"""Paramètres de marché partagés par les figures du mémoire."""

from dataclasses import dataclass

# Seed globale unique (spec §4) : source unique pour les 3 scripts de figure
# (figA_*.py, figB_*.py, figC_*.py), afin qu'une même quantité recalculée dans
# deux figures (ex. le coupon au pair de l'indice classique) reproduise
# exactement le même chiffre. Ne pas dupliquer cette valeur ailleurs.
SEED_GLOBAL = 2026


@dataclass(frozen=True)
class ParametresMarche:
    s0: float = 100.0
    r: float = 0.025
    sigma: float = 0.18
    q: float = 0.03
