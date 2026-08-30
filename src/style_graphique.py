"""Style graphique et palette partagés par les 3 figures du mémoire :
sobre, sans titre dans l'image (les légendes sont ajoutées dans le Word),
grille légère, labels en français."""

import matplotlib.pyplot as plt

# Palette cohérente pour les cas comparés dans le mémoire (indices A/B/C, leurs
# variantes de contrôle B' et C', et la barrière dégressive). Réutilisée par
# les Figures A, B, C et D.
PALETTE = {
    "A": "#1f77b4",
    "B": "#ff7f0e",
    "C": "#2ca02c",
    "A_degressive": "#9467bd",
    "B_prime": "#17becf",
    "C_prime": "#bcbd22",
}

LIBELLES = {
    "A": "A — Indice classique",
    "B": "B — Décrément % (D=5 %/an)",
    "C": "C — Décrément points (K=5)",
    "A_degressive": "A — Barrière dégressive",
    "B_prime": "B′ — Décrément % (D=q=3 %, contrôle)",
    "C_prime": "C′ — Décrément points + barrière dégressive",
}

LIBELLES_COURTS = {
    "A": "A",
    "B": "B (D=5 %)",
    "C": "C",
    "A_degressive": "A + dégr.",
    "B_prime": "B′ (D=q)",
    "C_prime": "C + dégr.",
}

ORDRE_CAS = ["A", "B", "B_prime", "C", "C_prime", "A_degressive"]


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
