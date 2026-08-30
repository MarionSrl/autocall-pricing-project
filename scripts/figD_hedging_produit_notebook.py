"""Figure D — Delta hedging et risques résiduels de couverture (section III.2).

ATTENTION, à lire avant interprétation : cette figure porte sur le produit du
notebook d'exploration (notebooks/Pricer_Autocall_MC.ipynb) -- 5 ans, coupon
FIXE 7% (non résolu au pair), volatilité modèle 20%, sans dividende -- et non
sur le produit de référence des Figures A-C (10 ans, coupon résolu au pair,
q=3%). Voir le README pour la justification de ce choix : le mécanisme
démontré ici (risque résiduel de gap aux barrières, sensibilité au mismatch
de volatilité) est structurel au produit autocall à barrières et ne dépend
pas de la maturité ni du niveau de coupon.

Panneau (a) : PnL de couverture (delta hedging, rebalancement 5j) en fonction
de la volatilité réalisée (15/20/25/30%, vol modèle 20%), avec superposition
de la prédiction théorique de gamma-trading -- voir src/delta_hedging.py pour
la convention de signe et sa validation.

Panneau (b) : dispersion du PnL (boxplot) en fonction de la fréquence de
rebalancement (1/5/10/20 jours) -- résultat volontairement contre-intuitif :
la dispersion reste quasi plate, le risque résiduel vient des discontinuités
de payoff aux barrières (gap risk), pas de la granularité du rebalancement.

Écrit figures/figureD_hedging.png (300 dpi) et les résultats numériques dans
figures/figureD_*.{csv,md}.
"""

import os
import sys
import time

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.marche import SEED_GLOBAL
from src.simulation import simuler_trajectoires_bs
from src.pricer_autocall import pricer_autocall
from src.delta_hedging import construire_grille_delta_gamma, simuler_couverture
from src.style_graphique import appliquer_style, PALETTE
from src.reporting import ecrire_csv_et_md

# Produit du NOTEBOOK (5 ans) -- distinct du produit de référence des Figures A-C.
S0 = 100.0
R = 0.03
Q = 0.0
SIGMA_MODELE = 0.20
MATURITE = 5
DATES_OBS = np.arange(1, MATURITE + 1)
BARRIERE_AUTOCALL = 1.0
COUPON = 0.07
BARRIERE_CAPITAL = 0.60
NB_PAS_AN = 252

NB_SIM_GRILLE = 10_000
NB_SIM_PRICING = 100_000
NB_HEDGE = 2_000
SEED = SEED_GLOBAL

VOLS_REALISEES = [0.15, 0.20, 0.25, 0.30]
FREQUENCES_REBAL = [1, 5, 10, 20]
FREQ_REFERENCE = 5

REPERTOIRE_RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPERTOIRE_FIGURES = os.path.join(REPERTOIRE_RACINE, "figures")

COULEUR_PNL = PALETTE["A"]
COULEUR_THEORIQUE = "#d62728"


def construire_grille():
    spots_grid = np.linspace(40.0, 200.0, 25)
    temps_grid = np.linspace(0.0, MATURITE - 0.01, 40)
    return construire_grille_delta_gamma(
        S0, R, Q, SIGMA_MODELE, DATES_OBS, BARRIERE_AUTOCALL, COUPON, BARRIERE_CAPITAL,
        spots_grid, temps_grid, NB_SIM_GRILLE, SEED,
    )


def prix_initial_modele():
    spots_obs = simuler_trajectoires_bs(
        S0, R - Q, SIGMA_MODELE, MATURITE, MATURITE, NB_SIM_PRICING, SEED
    )[:, 1:]
    return pricer_autocall(spots_obs, S0, R, DATES_OBS, BARRIERE_AUTOCALL, COUPON, BARRIERE_CAPITAL).prix


def simuler_scenario(vol_reelle, freq_rebal, interp_delta, interp_gamma, prix_init, seed):
    """Simule NB_HEDGE trajectoires de couverture pour un (vol_réalisée, fréquence)
    donné. Retourne (pnls, temps_sortie, points_gamma)."""
    trajectoires = simuler_trajectoires_bs(
        S0, R - Q, vol_reelle, MATURITE, NB_PAS_AN * MATURITE, NB_HEDGE, seed
    )
    pnls = np.empty(NB_HEDGE)
    temps_sortie = np.empty(NB_HEDGE)
    points_gamma = []
    for k in range(NB_HEDGE):
        pnl, pts, t_sortie = simuler_couverture(
            trajectoires[k], S0, R, interp_delta, DATES_OBS, BARRIERE_AUTOCALL, COUPON, BARRIERE_CAPITAL,
            prix_init, NB_PAS_AN, freq_rebal, interp_gamma=interp_gamma,
        )
        pnls[k] = pnl
        temps_sortie[k] = t_sortie
        points_gamma.extend(pts)
    return pnls, temps_sortie, points_gamma


def panneau_a_pnl_vs_vol(interp_delta, interp_gamma, prix_init):
    """PnL vs volatilité réalisée, à fréquence de rebalancement de référence
    (5j), + gamma moyen et temps de sortie moyen réalisés au scénario de
    référence (vol réalisée = vol modèle), utilisés pour la prédiction
    théorique."""
    lignes = []
    resultats_pnl = {}
    gamma_moyen_dollar = None
    gamma_s2_moyen = None
    t_moyen_reference = None

    for i, vol in enumerate(VOLS_REALISEES):
        pnls, temps_sortie, points_gamma = simuler_scenario(
            vol, FREQ_REFERENCE, interp_delta, interp_gamma, prix_init, SEED + 10 + i
        )
        resultats_pnl[vol] = pnls
        lignes.append({
            "vol_realisee_pct": vol * 100,
            "pnl_moyen": pnls.mean(),
            "pnl_erreur_std": pnls.std(ddof=1) / np.sqrt(NB_HEDGE),
            "nb_trajectoires": NB_HEDGE,
        })
        if abs(vol - SIGMA_MODELE) < 1e-9:
            spots_pts = np.array([p[0] for p in points_gamma])
            gammas_pts = np.array([p[1] for p in points_gamma])
            gamma_moyen_dollar = gammas_pts.mean()
            gamma_s2_moyen = (gammas_pts * spots_pts**2).mean()
            t_moyen_reference = temps_sortie.mean()

    # prédiction théorique (cf. src/delta_hedging.py pour la convention de signe) :
    # dPnL ~ 1/2 * gamma_$ * S^2 * (sigma_modele^2 - sigma_reelle^2) * T,
    # avec gamma_$*S^2 estimé par sa moyenne réalisée (gamma_s2_moyen) au
    # scénario de référence, plus précis qu'une substitution gamma_moyen*S0^2.
    for ligne in lignes:
        vol = ligne["vol_realisee_pct"] / 100
        ligne["pnl_theorique"] = 0.5 * gamma_s2_moyen * (SIGMA_MODELE**2 - vol**2) * t_moyen_reference

    df = pd.DataFrame(lignes)
    resume = pd.DataFrame([{
        "gamma_moyen_dollar": gamma_moyen_dollar,
        "gamma_s2_moyen": gamma_s2_moyen,
        "temps_sortie_moyen_annees": t_moyen_reference,
        "prix_initial_pct": prix_init * 100,
        "nb_trajectoires_grille_delta": NB_SIM_GRILLE,
        "nb_trajectoires_couverture_par_scenario": NB_HEDGE,
        "coupon_pct": COUPON * 100,
        "maturite_annees": MATURITE,
        "vol_modele_pct": SIGMA_MODELE * 100,
    }])
    return df, resume, resultats_pnl


def panneau_b_pnl_vs_frequence(interp_delta, interp_gamma, prix_init):
    lignes = []
    pnls_par_freq = {}
    for i, freq in enumerate(FREQUENCES_REBAL):
        pnls, _, _ = simuler_scenario(
            SIGMA_MODELE, freq, interp_delta, interp_gamma, prix_init, SEED + 20 + i
        )
        pnls_par_freq[freq] = pnls
        lignes.append({
            "freq_rebal_jours": freq,
            "pnl_moyen": pnls.mean(),
            "pnl_ecart_type": pnls.std(ddof=1),
            "pnl_erreur_std": pnls.std(ddof=1) / np.sqrt(NB_HEDGE),
            "nb_trajectoires": NB_HEDGE,
        })
    df = pd.DataFrame(lignes)
    df_brut = pd.DataFrame({
        "freq_rebal_jours": np.repeat(FREQUENCES_REBAL, NB_HEDGE),
        "pnl": np.concatenate([pnls_par_freq[f] for f in FREQUENCES_REBAL]),
    })
    return df, df_brut, pnls_par_freq


def tracer_figure(df_vol, resume, df_freq, pnls_par_freq):
    appliquer_style()
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(13, 5.5))

    # --- Panneau (a) ---
    vols = df_vol["vol_realisee_pct"].values
    ax_a.errorbar(vols, df_vol["pnl_moyen"], yerr=df_vol["pnl_erreur_std"],
                  fmt="o", color=COULEUR_PNL, capsize=4, markersize=7, label="PnL simulé (moyenne ± erreur std)")

    gamma_s2_moyen = resume["gamma_s2_moyen"].iloc[0]
    t_moyen = resume["temps_sortie_moyen_annees"].iloc[0]
    vols_fins = np.linspace(vols.min(), vols.max(), 100)
    pnl_theorique_fin = 0.5 * gamma_s2_moyen * (SIGMA_MODELE**2 - (vols_fins / 100) ** 2) * t_moyen
    ax_a.plot(vols_fins, pnl_theorique_fin,
              color=COULEUR_THEORIQUE, linestyle="--", linewidth=1.4,
              label="Prédiction théorique (gamma-trading)")
    ax_a.axhline(0.0, color="grey", linewidth=0.6)
    ax_a.axvline(SIGMA_MODELE * 100, color="grey", linestyle=":", linewidth=0.8)
    ax_a.set_xlabel("Volatilité réalisée (%)")
    ax_a.set_ylabel("PnL de couverture (base nominal 100)")
    ax_a.legend(fontsize=8)

    # --- Panneau (b) ---
    donnees_boxplot = [pnls_par_freq[f] for f in FREQUENCES_REBAL]
    bp = ax_b.boxplot(donnees_boxplot, tick_labels=[f"{f}j" for f in FREQUENCES_REBAL], patch_artist=True)
    for patch in bp["boxes"]:
        patch.set_facecolor(COULEUR_PNL)
        patch.set_alpha(0.5)
    ax_b.axhline(0.0, color="grey", linewidth=0.6)
    ax_b.set_xlabel("Fréquence de rebalancement")
    ax_b.set_ylabel("PnL de couverture (base nominal 100)")

    fig.tight_layout()
    chemin = os.path.join(REPERTOIRE_FIGURES, "figureD_hedging.png")
    fig.savefig(chemin, dpi=300)
    plt.close(fig)
    print(f"Figure enregistrée : {chemin}")


def main():
    t0 = time.time()
    os.makedirs(REPERTOIRE_FIGURES, exist_ok=True)

    print("Construction de la grille de delta/gamma...")
    _, _, interp_delta, interp_gamma = construire_grille()
    print(f"  -> grille construite en {time.time() - t0:.1f}s")

    prix_init = prix_initial_modele()
    print(f"Prix initial (modèle) : {prix_init * 100:.2f}%")

    print("Panneau (a) : PnL vs volatilité réalisée...")
    df_vol, resume, resultats_pnl = panneau_a_pnl_vs_vol(interp_delta, interp_gamma, prix_init)
    print(df_vol.to_string(index=False))
    print(resume.to_string(index=False))

    print("Panneau (b) : PnL vs fréquence de rebalancement...")
    df_freq, df_freq_brut, pnls_par_freq = panneau_b_pnl_vs_frequence(interp_delta, interp_gamma, prix_init)
    print(df_freq.to_string(index=False))

    ecrire_csv_et_md(df_vol, os.path.join(REPERTOIRE_FIGURES, "figureD_pnl_vs_vol_realisee"), float_format="{:.4f}")
    note_gamma = (
        "*Convention de signe (cf. `src/delta_hedging.py`) : `gamma_moyen_dollar` et "
        "`gamma_s2_moyen` sont le gamma de f(S,sigma), la valeur actualisée du flux "
        "versé A L'INVESTISSEUR (même fonction et même convention que le vega de la "
        "Figure A -- aucun changement de perspective entre les deux figures), pas un "
        "gamma \"de position\" de l'émetteur. Il est négatif ici : f est concave près "
        "du spot initial, cohérent avec le vega négatif de l'autocall en Figure A "
        "(-68.40 pt de % au spot initial du produit de référence, `figureA_autocall_vega.csv`) "
        "-- même sous-jacent économique (le put down-and-in cédé par l'investisseur à "
        "l'émetteur). Un gamma_f négatif inverse le signe usuel de la formule de "
        "gamma-trading par rapport au cas manuel d'un vendeur d'option vanille "
        "(toujours convexe, donc \"short gamma\") : ici l'émetteur, qui vend le produit "
        "et se couvre en delta au prix modèle, se retrouve net LONG gamma sur son "
        "livre couvert, d'où le PnL de couverture croissant avec la volatilité "
        "réalisée (panneau a).*"
    )
    ecrire_csv_et_md(resume, os.path.join(REPERTOIRE_FIGURES, "figureD_resume"), float_format="{:.5f}", note=note_gamma)
    ecrire_csv_et_md(df_freq, os.path.join(REPERTOIRE_FIGURES, "figureD_pnl_vs_frequence"), float_format="{:.4f}")
    df_freq_brut.to_csv(os.path.join(REPERTOIRE_FIGURES, "figureD_pnl_vs_frequence_brut.csv"), index=False)

    tracer_figure(df_vol, resume, df_freq, pnls_par_freq)
    print(f"Terminé en {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
