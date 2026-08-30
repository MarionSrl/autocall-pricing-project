"""Figure B — Autocall classique vs décrément (section III.1.3 du mémoire).

Compare, pour un autocall 10 ans / observations annuelles / PDI 60% à maturité :
    A             indice classique (price return)
    B             indice à décrément en % (D=5 %/an)
    B_prime       indice à décrément en % avec D=q=3 % — cas de contrôle : isole
                  l'effet du mécanisme de décrément de l'effet "D > q" (voir
                  src/indices.py::indice_decrement_pourcentage). Doit donner le
                  même coupon au pair qu'A (vérifié par les tests).
    C             indice à décrément en points (K=5, calibré à 5% de S0)
    C_prime       indice C avec barrière de rappel dégressive (-5 %/an, plancher
                  70 %) — configuration réellement commercialisée en retail : le
                  décrément seul rend le rappel trop improbable (cf. C), la
                  barrière dégressive compense.
    A_degressive  indice A avec barrière de rappel dégressive (-5%/an, plancher 70%)

Pour chacun : coupon au pair (solveur Brent, trajectoires figées), distribution
des dates de rappel, probabilité d'activation du PDI, perte moyenne
conditionnelle, et forward théorique à maturité de l'indice sous-jacent (la
variable qui explique l'essentiel des écarts de coupon entre cas). Écrit
figures/figureB_autocall_vs_decrement.png (300 dpi) et
figures/figureB_resultats.{csv,md}.
"""

import os
import sys
import time

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.marche import SEED_GLOBAL
from src.indices import (
    simuler_indices,
    barriere_degressive,
    indice_decrement_pourcentage,
    forward_theorique_decrement_points,
)
from src.coupon_solver import resoudre_coupon_pair
from src.style_graphique import appliquer_style, PALETTE, LIBELLES, LIBELLES_COURTS, ORDRE_CAS
from src.reporting import ecrire_csv_et_md

# ---------------------------------------------------------------------------
# Paramètres (SPEC §1 et §2)
# ---------------------------------------------------------------------------
S0 = 100.0
R = 0.025
SIGMA = 0.18
Q = 0.03
D = 0.05            # décrément en % (indice B)
K = 5.0             # décrément en points (indice C), calibré à 5% de S0
MATURITE = 10
DATES_OBS = np.arange(1, MATURITE + 1)
BARRIERE_AUTOCALL = 1.0
BARRIERE_CAPITAL = 0.60
NOMINAL = 1.0

NB_SIM = 200_000
NB_PAS_AN = 252
SEED = SEED_GLOBAL  # source unique : src/marche.py::SEED_GLOBAL

REPERTOIRE_RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPERTOIRE_FIGURES = os.path.join(REPERTOIRE_RACINE, "figures")


def construire_cas(indices):
    barriere_plate = np.full(len(DATES_OBS), BARRIERE_AUTOCALL)
    barriere_deg = barriere_degressive(
        DATES_OBS, niveau_initial=BARRIERE_AUTOCALL, baisse_annuelle=0.05, plancher=0.70
    )
    # B' : décrément en % au niveau du dividende réel (D=q) — cas de contrôle,
    # dérivé de U sans re-simulation (cf. indice_decrement_pourcentage).
    B_prime_obs = indice_decrement_pourcentage(indices["U"], indices["t_obs"], D=Q)
    return {
        "A": (indices["A"][:, 1:], barriere_plate),
        "B": (indices["B"][:, 1:], barriere_plate),
        "B_prime": (B_prime_obs[:, 1:], barriere_plate),
        "C": (indices["C"][:, 1:], barriere_plate),
        "C_prime": (indices["C"][:, 1:], barriere_deg),
        "A_degressive": (indices["A"][:, 1:], barriere_deg),
    }


def forward_theorique_par_cas():
    """Forward théorique à MATURITE de l'indice sous-jacent effectivement pricé
    dans chaque cas (seule la barrière diffère pour A_degressive et C_prime,
    donc même forward que leur cas de base A / C)."""
    forward_A = S0 * np.exp((R - Q) * MATURITE)
    forward_B = S0 * np.exp((R - D) * MATURITE)
    forward_C = forward_theorique_decrement_points(S0, R, K, MATURITE, NB_PAS_AN)
    return {
        "A": forward_A,
        "B": forward_B,
        "B_prime": forward_A,   # D=q => identique à A (voir test dédié)
        "C": forward_C,
        "C_prime": forward_C,   # même sous-jacent C, seule la barrière change
        "A_degressive": forward_A,
    }


def statistiques_cas(resultat):
    proba_rappel = {t: (resultat.dates_rappel == t).mean() for t in DATES_OBS}
    proba_maturite = np.isnan(resultat.dates_rappel).mean()
    proba_pdi = resultat.pdi_actif.mean()
    if resultat.pdi_actif.any():
        perte_cond = (1.0 - resultat.spot_final[resultat.pdi_actif] / S0).mean()
    else:
        perte_cond = np.nan
    return proba_rappel, proba_maturite, proba_pdi, perte_cond


def main():
    t0 = time.time()
    print(f"Simulation de {NB_SIM:,} trajectoires (antithétiques) sur {MATURITE} ans, "
          f"pas={NB_PAS_AN}/an (A, B, C sur les mêmes chocs)...")
    indices = simuler_indices(S0, R, Q, SIGMA, D, K, MATURITE, NB_PAS_AN, DATES_OBS, NB_SIM, SEED)
    print(f"  -> simulation terminée en {time.time() - t0:.1f}s")

    cas = construire_cas(indices)
    forward_par_cas = forward_theorique_par_cas()

    lignes = []
    resultats = {}
    for nom in ORDRE_CAS:
        spots_obs, barriere_ac = cas[nom]
        coupon_pair, resultat = resoudre_coupon_pair(
            spots_obs, S0, R, DATES_OBS, barriere_ac, BARRIERE_CAPITAL, nominal=NOMINAL
        )
        proba_rappel, proba_maturite, proba_pdi, perte_cond = statistiques_cas(resultat)
        resultats[nom] = {
            "coupon_pair": coupon_pair,
            "prix": resultat.prix,
            "erreur_std": resultat.erreur_std,
            "proba_rappel": proba_rappel,
            "proba_maturite": proba_maturite,
            "proba_pdi": proba_pdi,
            "perte_cond": perte_cond,
        }

        ligne = {
            "cas": LIBELLES[nom],
            "forward_theorique_10y": forward_par_cas[nom],
            "coupon_pair_pct": coupon_pair * 100,
            "prix_verif_pct": resultat.prix * 100,
            "erreur_std_mc_pct": resultat.erreur_std * 100,
            "proba_maturite_pct": proba_maturite * 100,
            "proba_pdi_actif_pct": proba_pdi * 100,
            "perte_moyenne_cond_pct": perte_cond * 100,
        }
        for t in DATES_OBS:
            ligne[f"proba_rappel_t{int(t)}_pct"] = proba_rappel[t] * 100
        lignes.append(ligne)
        print(f"  {nom:15s} coupon au pair = {coupon_pair * 100:5.2f}%  "
              f"(forward 10y = {forward_par_cas[nom]:.1f}, "
              f"prix vérif = {resultat.prix * 100:.2f}%, erreur std {resultat.erreur_std * 100:.3f}%)")

    df = pd.DataFrame(lignes)
    os.makedirs(REPERTOIRE_FIGURES, exist_ok=True)
    ecrire_csv_et_md(df, os.path.join(REPERTOIRE_FIGURES, "figureB_resultats"), float_format="{:.3f}")

    tracer_figure(resultats)
    print(f"Terminé en {time.time() - t0:.1f}s")


def tracer_figure(resultats):
    appliquer_style()
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))

    noms = ORDRE_CAS
    couleurs = [PALETTE[n] for n in noms]
    libelles = [LIBELLES[n] for n in noms]
    libelles_courts = [LIBELLES_COURTS[n] for n in noms]
    n_cas = len(noms)

    # (a) coupon au pair
    ax = axes[0, 0]
    coupons = [resultats[n]["coupon_pair"] * 100 for n in noms]
    ax.bar(libelles_courts, coupons, color=couleurs)
    ax.set_ylabel("Coupon annuel au pair (%)")
    ax.tick_params(axis="x", rotation=25)

    # (b) distribution des dates de rappel + probabilité d'aller à maturité
    ax = axes[0, 1]
    largeur = 0.8 / n_cas
    x_dates = np.arange(len(DATES_OBS) + 1)
    etiquettes_x = [f"t={int(t)}" for t in DATES_OBS] + ["maturité"]
    for i, n in enumerate(noms):
        proba_rappel = resultats[n]["proba_rappel"]
        proba_maturite = resultats[n]["proba_maturite"]
        valeurs = [proba_rappel[t] * 100 for t in DATES_OBS] + [proba_maturite * 100]
        decalage = (i - (n_cas - 1) / 2) * largeur
        ax.bar(x_dates + decalage, valeurs, width=largeur, color=PALETTE[n], label=libelles[i])
    ax.set_xticks(x_dates)
    ax.set_xticklabels(etiquettes_x, rotation=45, ha="right")
    ax.set_ylabel("Probabilité (%)")
    ax.legend(fontsize=6.5, loc="upper right")

    # (c) probabilité d'activation du PDI
    ax = axes[1, 0]
    probas_pdi = [resultats[n]["proba_pdi"] * 100 for n in noms]
    ax.bar(libelles_courts, probas_pdi, color=couleurs)
    ax.set_ylabel("Probabilité d'activation du PDI (%)")
    ax.tick_params(axis="x", rotation=25)

    # (d) perte moyenne conditionnelle sachant activation du PDI
    ax = axes[1, 1]
    pertes = [resultats[n]["perte_cond"] * 100 for n in noms]
    ax.bar(libelles_courts, pertes, color=couleurs)
    ax.set_ylabel("Perte moy. conditionnelle sachant\nactivation du PDI (%)")
    ax.tick_params(axis="x", rotation=25)

    fig.tight_layout()
    chemin = os.path.join(REPERTOIRE_FIGURES, "figureB_autocall_vs_decrement.png")
    fig.savefig(chemin, dpi=300)
    plt.close(fig)
    print(f"Figure enregistrée : {chemin}")


if __name__ == "__main__":
    main()
