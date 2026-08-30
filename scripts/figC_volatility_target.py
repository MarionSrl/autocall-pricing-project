"""Figure C — Indice Volatility Target (section III.3.1 du mémoire).

Indice VT construit sur l'indice A (classique), avec un modèle de volatilité
à 2 régimes (calme / stress) plutôt que Heston — voir la justification en
tête de src/vol_target.py. Mécanique : e_t = min(L_max, sigma_cible /
sigma_réalisée_t), sigma_cible = 15%, L_max = 150%, fenêtre glissante de 20
jours ouvrés, rebalancement quotidien, sans coût de transaction (limite
documentée dans le README).

Trois sorties :
1. Trajectoire type (5 ans) : indice sous-jacent, indice VT, exposition e_t
   en second axe.
2. Distribution de la vol réalisée annualisée de l'indice VT (5000
   trajectoires, 1 an) vs la cible de 15% : montre qu'elle ne l'égale pas.
3. Scénario V scripté (chute -30% puis rebond symétrique, déterministe) :
   indice nu vs indice VT, quantification de la sous-participation au
   rebond, et comparaison fenêtre 20j vs 60j (bonus).

Écrit figures/figureC_volatility_target.png (300 dpi) et les résultats
numériques dans figures/figureC_*.{csv,md}.
"""

import os
import sys
import time

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.marche import SEED_GLOBAL
from src.vol_target import (
    simuler_regimes,
    simuler_indice_sous_jacent,
    construire_indice_vt,
    scenario_v_scripte,
)
from src.style_graphique import appliquer_style, PALETTE
from src.reporting import ecrire_csv_et_md

# Marché
R = 0.025
Q = 0.03
S0 = 100.0
NB_PAS_AN = 252
SEED = SEED_GLOBAL  # source unique : src/marche.py::SEED_GLOBAL

# Modèle de volatilité à 2 régimes (cf. src/vol_target.py pour la justification)
SIGMA_BAS = 0.09
SIGMA_HAUT = 0.32
DUREE_CALME = 60    # jours ouvrés, durée moyenne du régime calme
DUREE_STRESS = 20   # jours ouvrés, durée moyenne du régime de stress

# Mécanique Volatility Target (spec §3)
SIGMA_CIBLE = 0.15
L_MAX = 1.50
FENETRE = 20

REPERTOIRE_RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPERTOIRE_FIGURES = os.path.join(REPERTOIRE_RACINE, "figures")

COULEUR_SOUS_JACENT = PALETTE["A"]
COULEUR_VT = "#d62728"
COULEUR_VT_60J = "#9467bd"
COULEUR_EXPOSITION = "#7f7f7f"


def sortie1_trajectoire_type():
    nb_jours = NB_PAS_AN * 5  # 5 ans, assez pour voir plusieurs cycles de régime
    sigma_path = simuler_regimes(nb_jours, 1, SEED, SIGMA_BAS, SIGMA_HAUT, DUREE_CALME, DUREE_STRESS)
    traj = simuler_indice_sous_jacent(S0, R, Q, sigma_path, NB_PAS_AN, SEED + 1)
    vt, expositions = construire_indice_vt(traj, R, SIGMA_CIBLE, L_MAX, FENETRE, NB_PAS_AN)

    t_annees = np.arange(traj.shape[1]) / NB_PAS_AN
    df = pd.DataFrame({
        "annee": t_annees,
        "indice_sous_jacent": traj[0],
        "indice_vt": vt[0],
        "exposition_pct": expositions[0] * 100,
    })
    return df


def sortie2_distribution_vol_realisee(nb_sim=5000, horizon_annees=1):
    nb_jours = int(NB_PAS_AN * horizon_annees)
    sigma_path = simuler_regimes(nb_jours, nb_sim, SEED, SIGMA_BAS, SIGMA_HAUT, DUREE_CALME, DUREE_STRESS)
    traj = simuler_indice_sous_jacent(S0, R, Q, sigma_path, NB_PAS_AN, SEED + 2)
    vt, _ = construire_indice_vt(traj, R, SIGMA_CIBLE, L_MAX, FENETRE, NB_PAS_AN)

    log_rendements_vt = np.diff(np.log(vt), axis=1)
    vol_finale = log_rendements_vt.std(axis=1, ddof=1) * np.sqrt(NB_PAS_AN)

    resume = pd.DataFrame([{
        "sigma_cible_pct": SIGMA_CIBLE * 100,
        "vol_realisee_moyenne_pct": vol_finale.mean() * 100,
        "vol_realisee_mediane_pct": np.median(vol_finale) * 100,
        "vol_realisee_ecart_type_pct": vol_finale.std(ddof=1) * 100,
        "proba_dans_plus_ou_moins_2pt_pct": float(
            np.mean(np.abs(vol_finale - SIGMA_CIBLE) <= 0.02)
        ) * 100,
    }])
    return vol_finale, resume


def sortie3_scenario_v():
    n_avant, n_chute, n_rebond, n_apres = 65, 20, 20, 80
    trajectoire_nue = scenario_v_scripte(S0, 0.30, n_avant, n_chute, n_rebond, n_apres)
    trajectoire_nue = trajectoire_nue[None, :]

    resultats = {}
    for fenetre, couleur in [(20, COULEUR_VT), (60, COULEUR_VT_60J)]:
        vt, expositions = construire_indice_vt(trajectoire_nue, R, SIGMA_CIBLE, L_MAX, fenetre, NB_PAS_AN)
        resultats[fenetre] = (vt[0], expositions[0])

    idx_fin_rebond = n_avant + n_chute + n_rebond
    idx_fin = n_avant + n_chute + n_rebond + n_apres

    lignes = []
    for fenetre in (20, 60):
        vt, _ = resultats[fenetre]
        lignes.append({
            "fenetre_jours": fenetre,
            "niveau_indice_nu_fin_rebond": trajectoire_nue[0, idx_fin_rebond],
            "niveau_indice_vt_fin_rebond": vt[idx_fin_rebond],
            "sous_participation_pts": trajectoire_nue[0, idx_fin_rebond] - vt[idx_fin_rebond],
            "niveau_indice_vt_fin_episode": vt[idx_fin],
            "niveau_plancher_indice_nu": trajectoire_nue[0].min(),
            "niveau_plancher_indice_vt": vt.min(),
        })
    df_resume = pd.DataFrame(lignes)

    jours = np.arange(len(trajectoire_nue[0]))
    df_trajectoires = pd.DataFrame({
        "jour": jours,
        "indice_nu": trajectoire_nue[0],
        "indice_vt_20j": resultats[20][0],
        "exposition_20j_pct": resultats[20][1] * 100,
        "indice_vt_60j": resultats[60][0],
        "exposition_60j_pct": resultats[60][1] * 100,
    })
    reperes = {"n_avant": n_avant, "n_chute": n_chute, "n_rebond": n_rebond, "n_apres": n_apres}
    return df_trajectoires, df_resume, reperes


def tracer_figure(df1, vol_finale, df3, reperes):
    appliquer_style()
    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1])

    # --- Sortie 1 : trajectoire type ---
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(df1["annee"], df1["indice_sous_jacent"], color=COULEUR_SOUS_JACENT,
              linewidth=1.1, label="Indice sous-jacent (A)")
    ax1.plot(df1["annee"], df1["indice_vt"], color=COULEUR_VT, linewidth=1.1,
              label="Indice Volatility Target")
    ax1.set_xlabel("Années")
    ax1.set_ylabel("Niveau (base 100)")
    ax1_bis = ax1.twinx()
    ax1_bis.plot(df1["annee"], df1["exposition_pct"], color=COULEUR_EXPOSITION,
                 linewidth=0.6, alpha=0.6, label="Exposition e_t (droite)")
    ax1_bis.set_ylabel("Exposition e_t (%)")
    ax1_bis.grid(False)
    lignes_1, labels_1 = ax1.get_legend_handles_labels()
    lignes_2, labels_2 = ax1_bis.get_legend_handles_labels()
    ax1.legend(lignes_1 + lignes_2, labels_1 + labels_2, fontsize=8, loc="upper left")

    # --- Sortie 2 : distribution vol réalisée ---
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.hist(vol_finale * 100, bins=50, color=COULEUR_VT, alpha=0.75)
    ax2.axvline(SIGMA_CIBLE * 100, color="black", linestyle="--", linewidth=1.2,
                label=f"Cible ({SIGMA_CIBLE * 100:.0f}%)")
    ax2.axvline(vol_finale.mean() * 100, color="grey", linestyle=":", linewidth=1.2,
                label=f"Moyenne ({vol_finale.mean() * 100:.1f}%)")
    ax2.set_xlabel("Vol réalisée annualisée de l'indice VT (%)")
    ax2.set_ylabel("Nombre de trajectoires")
    ax2.legend(fontsize=8)

    # --- Sortie 3 : scénario V ---
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.plot(df3["jour"], df3["indice_nu"], color=COULEUR_SOUS_JACENT, linewidth=1.4,
              label="Indice nu")
    ax3.plot(df3["jour"], df3["indice_vt_20j"], color=COULEUR_VT, linewidth=1.4,
              label="Indice VT (fenêtre 20j)")
    ax3.plot(df3["jour"], df3["indice_vt_60j"], color=COULEUR_VT_60J, linewidth=1.2,
              linestyle="--", label="Indice VT (fenêtre 60j)")
    ax3.axhline(100.0, color="grey", linewidth=0.6)
    idx_fin_rebond = reperes["n_avant"] + reperes["n_chute"] + reperes["n_rebond"]
    ax3.axvline(idx_fin_rebond, color="grey", linestyle=":", linewidth=0.8)
    ax3.set_xlabel("Jours")
    ax3.set_ylabel("Niveau (base 100)")
    ax3.legend(fontsize=8)

    fig.tight_layout()
    chemin = os.path.join(REPERTOIRE_FIGURES, "figureC_volatility_target.png")
    fig.savefig(chemin, dpi=300)
    plt.close(fig)
    print(f"Figure enregistrée : {chemin}")


def main():
    t0 = time.time()
    os.makedirs(REPERTOIRE_FIGURES, exist_ok=True)

    print("Sortie 1 : trajectoire type (5 ans)...")
    df1 = sortie1_trajectoire_type()
    pct_temps_plafond = (df1["exposition_pct"] >= L_MAX * 100 - 1e-6).mean() * 100
    df1_resume = pd.DataFrame([{"pct_temps_exposition_plafond": pct_temps_plafond}])
    print(f"  -> temps passé à l'exposition plafond ({L_MAX * 100:.0f}%) : {pct_temps_plafond:.1f}%")

    print("Sortie 2 : distribution de la vol réalisée (5000 trajectoires, 1 an)...")
    vol_finale, df2_resume = sortie2_distribution_vol_realisee()
    print(df2_resume.to_string(index=False))

    print("Sortie 3 : scénario V scripté...")
    df3, df3_resume, reperes = sortie3_scenario_v()
    print(df3_resume.to_string(index=False))

    ecrire_csv_et_md(df1, os.path.join(REPERTOIRE_FIGURES, "figureC_trajectoire_type"), float_format="{:.4f}")
    ecrire_csv_et_md(df1_resume, os.path.join(REPERTOIRE_FIGURES, "figureC_trajectoire_type_resume"), float_format="{:.4f}")
    ecrire_csv_et_md(df2_resume, os.path.join(REPERTOIRE_FIGURES, "figureC_distribution_vol_realisee"), float_format="{:.4f}")
    ecrire_csv_et_md(df3, os.path.join(REPERTOIRE_FIGURES, "figureC_scenario_v"), float_format="{:.4f}")
    ecrire_csv_et_md(df3_resume, os.path.join(REPERTOIRE_FIGURES, "figureC_scenario_v_resume"), float_format="{:.4f}")

    tracer_figure(df1, vol_finale, df3, reperes)
    print(f"Terminé en {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
