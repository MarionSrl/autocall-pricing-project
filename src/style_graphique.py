"""Style graphique et palette partagés par les 3 figures du mémoire :
sobre, sans titre dans l'image (les légendes sont ajoutées dans le Word),
grille légère, labels en français."""

import matplotlib.pyplot as plt

# Palette cohérente pour les 4 cas comparés dans le mémoire (indices A/B/C et
# variante à barrière dégressive). Réutilisée par les Figures 1, 2 et 3.
PALETTE = {
    "A": "#1f77b4",
    "B": "#ff7f0e",
    "C": "#2ca02c",
    "A_degressive": "#9467bd",
}

LIBELLES = {
    "A": "A — Indice classique",
    "B": "B — Décrément % (5 %/an)",
    "C": "C — Décrément points (K=5)",
    "A_degressive": "A — Barrière dégressive",
}

ORDRE_CAS = ["A", "B", "C", "A_degressive"]


def appliquer_style():
    plt.rcParams.update({
        "figure.dpi": 100,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "font.size": 10,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linewidth": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.axisbelow": True,
    })
