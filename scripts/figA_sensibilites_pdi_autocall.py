"""Figure A — Sensibilités du PDI et de l'autocall (section III.1.1 du mémoire).

Panneau (a) : le PDI seul, en formule fermée (Bouzoubaa & Osseiran §10.2.2,
cas H<K ; équivalent Hull ch.26). PDI 100/60, maturité 1 an. Prix, delta
(discontinuité de sensibilité près de la barrière), vega et vanna (différences
finies centrées sur la formule fermée), en fonction du spot (40%→130%).

Panneau (b) : vega de l'autocall complet (produit de référence 10 ans, section
1 de la spec ; coupon résolu au pair à spot=100), par Monte Carlo, bump de vol
±1pt avec differencing commun (mêmes trajectoires pour le bump, sinon le bruit
MC noie le signal). Vega total + décomposition en jambe "autocall sans PDI" et
jambe "PDI" (src/pricer_autocall.py::decomposer_legs_pdi), en fonction du spot.

Ce que la figure démontre (cf. README) : le vega du PDI seul (panneau a) est de
signe constant (put : vega positif), mais le vega de l'autocall complet
(panneau b) change de signe selon le spot, parce que la jambe "sans PDI" et la
jambe "PDI" ont des expositions vega opposées.

Validations obligatoires (voir aussi tests/test_barrier_options.py) :
KI + KO = vanille sur la formule fermée, et convergence MC vers la formule
fermée pour le PDI (écart < 0.5% à 200k trajectoires).

Écrit figures/figureA_sensibilites_pdi_autocall.png (300 dpi) et les résultats
numériques dans figures/figureA_*.{csv,md}.
"""

import os
import sys
import time

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import brentq

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.barrier_options import (
    pdi_grecques,
    put_down_and_in,
    put_down_and_out,
    bs_put,
    mc_put_down_and_in,
)
from src.marche import SEED_GLOBAL
from src.simulation import simuler_trajectoires_bs
from src.indices import simuler_indices
from src.pricer_autocall import pricer_autocall, decomposer_legs_pdi
from src.coupon_solver import resoudre_coupon_pair
from src.style_graphique import appliquer_style, PALETTE
from src.reporting import ecrire_csv_et_md

# Marché (identique à la Figure B)
R = 0.025
Q = 0.03
SIGMA = 0.18
# D, K : paramètres de décrément requis par la signature de simuler_indices
# (Figure B), mais sans effet sur l'indice A qu'on en extrait ici.
D_INUTILISE = 0.05
K_INUTILISE = 5.0
NB_PAS_AN = 252

# Panneau (a) : PDI seul
K_PDI = 100.0
H_PDI = 60.0
T_PDI = 1.0

# Panneau (b) : produit de référence (section 1 de la spec)
S_REF = 100.0
MATURITE = 10
DATES_OBS = np.arange(1, MATURITE + 1)
BARRIERE_AUTOCALL = 1.0
BARRIERE_CAPITAL = 0.60
NB_SIM = 200_000
DV_VEGA = 0.01  # bump de vol +/-1pt
SEED = SEED_GLOBAL  # source unique : src/marche.py::SEED_GLOBAL

REPERTOIRE_RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPERTOIRE_FIGURES = os.path.join(REPERTOIRE_RACINE, "figures")

COULEUR_A = PALETTE["A"]
COULEUR_SANS_PDI = "#2ca02c"
COULEUR_PDI = "#d62728"


def calculer_panneau_a():
    spots = np.linspace(40.0, 130.0, 361)
    grecques = pdi_grecques(spots, K_PDI, H_PDI, R, Q, SIGMA, T_PDI)
    return pd.DataFrame({
        "spot": spots,
        "prix": grecques["prix"],
        "delta": grecques["delta"],
        "vega": grecques["vega"],
        "vanna": grecques["vanna"],
    })


def valider_formule_fermee():
    """KI+KO=vanille et convergence MC (validations obligatoires)."""
    spots_validation = np.array([65.0, 70.0, 75.0, 80.0, 90.0, 100.0])
    di = put_down_and_in(spots_validation, K_PDI, H_PDI, R, Q, SIGMA, T_PDI)
    do = put_down_and_out(spots_validation, K_PDI, H_PDI, R, Q, SIGMA, T_PDI)
    vanille = bs_put(spots_validation, K_PDI, R, Q, SIGMA, T_PDI)

    lignes = [
        {
            "validation": f"KI+KO=vanille (spot={s:.0f})",
            "resultat": d + o,
            "reference": v,
            "ecart_relatif_pct": abs(d + o - v) / v * 100,
        }
        for s, d, o, v in zip(spots_validation, di, do, vanille)
    ]

    spot_mc = 70.0
    prix_ferme = put_down_and_in(spot_mc, K_PDI, H_PDI, R, Q, SIGMA, T_PDI)
    prix_mc, erreur_std_mc = mc_put_down_and_in(spot_mc, K_PDI, H_PDI, R, Q, SIGMA, T_PDI, NB_SIM, SEED)
    lignes.append({
        "validation": f"MC vs formule fermée (spot={spot_mc:.0f}, {NB_SIM:,} traj., erreur std={erreur_std_mc:.4f})",
        "resultat": prix_mc,
        "reference": prix_ferme,
        "ecart_relatif_pct": abs(prix_mc - prix_ferme) / prix_ferme * 100,
    })
    return pd.DataFrame(lignes)


def resoudre_coupon_reference():
    """Coupon au pair du cas A (indice classique), calculé EXACTEMENT comme dans
    scripts/figB_autocall_vs_decrement.py (même simuler_indices, même seed, même
    grille quotidienne) : la spec impose une seule seed globale, donc la même
    quantité (coupon au pair de l'indice classique à spot=100) doit ressortir au
    même chiffre dans les deux figures. Un simuler_trajectoires_bs séparé à 10 pas
    annuels, même à seed identique, tire un nombre différent de gaussiennes par
    trajectoire et ne reproduit donc PAS les mêmes trajectoires -- d'où l'écart
    (11.83% vs 11.81%) observé avant cette correction.
    """
    indices = simuler_indices(
        S_REF, R, Q, SIGMA, D_INUTILISE, K_INUTILISE, MATURITE, NB_PAS_AN, DATES_OBS, NB_SIM, SEED
    )
    spots_obs = indices["A"][:, 1:]
    coupon, _ = resoudre_coupon_pair(spots_obs, S_REF, R, DATES_OBS, BARRIERE_AUTOCALL, BARRIERE_CAPITAL)
    return coupon


def calculer_panneau_b(coupon):
    spots_test = np.arange(40.0, 131.0, 5.0)
    lignes = []
    for i, s0_test in enumerate(spots_test):
        seed_local = SEED + i
        # differencing commun : mêmes trajectoires (même seed) pour les 3 vols
        resultats_vol = {}
        for vol in (SIGMA - DV_VEGA, SIGMA, SIGMA + DV_VEGA):
            spots_obs = simuler_trajectoires_bs(
                s0_test, R - Q, vol, MATURITE, len(DATES_OBS), NB_SIM, seed_local
            )[:, 1:]
            resultats_vol[vol] = pricer_autocall(
                spots_obs, S_REF, R, DATES_OBS, BARRIERE_AUTOCALL, coupon, BARRIERE_CAPITAL
            )

        r_down = resultats_vol[SIGMA - DV_VEGA]
        r_up = resultats_vol[SIGMA + DV_VEGA]
        r_mid = resultats_vol[SIGMA]

        jambe_sans_pdi_down, jambe_pdi_down = decomposer_legs_pdi(r_down, S_REF, R, DATES_OBS[-1])
        jambe_sans_pdi_up, jambe_pdi_up = decomposer_legs_pdi(r_up, S_REF, R, DATES_OBS[-1])

        vega_total = (r_up.payoffs - r_down.payoffs) / (2 * DV_VEGA)
        vega_sans_pdi = (jambe_sans_pdi_up - jambe_sans_pdi_down) / (2 * DV_VEGA)
        vega_pdi = (jambe_pdi_up - jambe_pdi_down) / (2 * DV_VEGA)

        lignes.append({
            "spot": s0_test,
            "prix": r_mid.prix * 100,
            "erreur_std_prix_pct": r_mid.erreur_std * 100,
            "vega_total_pct": vega_total.mean() * 100,
            "erreur_std_vega_total_pct": vega_total.std(ddof=1) / np.sqrt(len(vega_total)) * 100,
            "vega_leg_sans_pdi_pct": vega_sans_pdi.mean() * 100,
            "vega_leg_pdi_pct": vega_pdi.mean() * 100,
        })
    return pd.DataFrame(lignes)


def calculer_discontinuite_delta(epsilon=0.01, h_spot_rel=1e-6):
    """Delta juste sous et juste au-dessus de la barrière (H +/- epsilon), avec
    un pas de différences finies assez petit (h_spot_rel) pour ne pas enjamber
    la barrière et donc ne pas moyenner les deux régimes."""
    delta_bas = pdi_grecques(H_PDI - epsilon, K_PDI, H_PDI, R, Q, SIGMA, T_PDI, h_spot_rel=h_spot_rel)["delta"]
    delta_haut = pdi_grecques(H_PDI + epsilon, K_PDI, H_PDI, R, Q, SIGMA, T_PDI, h_spot_rel=h_spot_rel)["delta"]
    return pd.DataFrame([
        {"spot": H_PDI - epsilon, "position": "juste sous la barrière", "delta": float(delta_bas)},
        {"spot": H_PDI + epsilon, "position": "juste au-dessus de la barrière", "delta": float(delta_haut)},
    ])


def vega_total_moyen(s0_test, coupon, seed=SEED):
    """Vega total moyen (MC, differencing commun), à seed FIXE (contrairement
    au balayage de calculer_panneau_b) pour que la fonction soit bien définie
    pendant la recherche de racine ci-dessous."""
    spots_down = simuler_trajectoires_bs(
        s0_test, R - Q, SIGMA - DV_VEGA, MATURITE, len(DATES_OBS), NB_SIM, seed
    )[:, 1:]
    spots_up = simuler_trajectoires_bs(
        s0_test, R - Q, SIGMA + DV_VEGA, MATURITE, len(DATES_OBS), NB_SIM, seed
    )[:, 1:]
    r_down = pricer_autocall(spots_down, S_REF, R, DATES_OBS, BARRIERE_AUTOCALL, coupon, BARRIERE_CAPITAL)
    r_up = pricer_autocall(spots_up, S_REF, R, DATES_OBS, BARRIERE_AUTOCALL, coupon, BARRIERE_CAPITAL)
    vega = (r_up.payoffs - r_down.payoffs) / (2 * DV_VEGA)
    return vega.mean(), vega.std(ddof=1) / np.sqrt(len(vega))


def trouver_spot_zero_vega(coupon, borne_basse=68.0, borne_haute=76.0):
    """Spot où le vega total MC de l'autocall s'annule (dichotomie de Brent,
    seed fixe). Le vega décroît régulièrement de positif à négatif sur cette
    plage (vérifié empiriquement), la recherche de racine est donc bien posée."""
    spot_zero = brentq(lambda s: vega_total_moyen(s, coupon)[0], borne_basse, borne_haute, xtol=0.005)
    vega_au_zero, erreur_std = vega_total_moyen(spot_zero, coupon)
    return spot_zero, vega_au_zero, erreur_std


def tracer_figure(df_a, df_b):
    appliquer_style()
    fig = plt.figure(figsize=(15, 9))
    gs = fig.add_gridspec(2, 4, height_ratios=[1, 1.1])

    ax_prix = fig.add_subplot(gs[0, 0])
    ax_delta = fig.add_subplot(gs[0, 1])
    ax_vega = fig.add_subplot(gs[0, 2])
    ax_vanna = fig.add_subplot(gs[0, 3])
    ax_vega_ac = fig.add_subplot(gs[1, :])

    for ax, col, ylabel in [
        (ax_prix, "prix", "Prix du PDI"),
        (ax_delta, "delta", "Delta du PDI"),
        (ax_vega, "vega", "Vega du PDI (pour 1 pt de vol)"),
        (ax_vanna, "vanna", "Vanna du PDI"),
    ]:
        ax.plot(df_a["spot"], df_a[col], color=COULEUR_A, linewidth=1.3)
        ax.axvline(H_PDI, color="grey", linestyle="--", linewidth=0.8)
        ax.axvline(K_PDI, color="grey", linestyle=":", linewidth=0.8)
        ax.set_xlabel("Spot (% du niveau initial)")
        ax.set_ylabel(ylabel)

    ax_vega_ac.axhline(0.0, color="grey", linewidth=0.8)
    ax_vega_ac.axvline(BARRIERE_CAPITAL * 100, color="grey", linestyle="--", linewidth=0.8)
    ax_vega_ac.axvline(BARRIERE_AUTOCALL * 100, color="grey", linestyle=":", linewidth=0.8)
    ax_vega_ac.plot(df_b["spot"], df_b["vega_total_pct"], color="black", linewidth=1.6,
                     label="Vega total")
    ax_vega_ac.plot(df_b["spot"], df_b["vega_leg_sans_pdi_pct"], color=COULEUR_SANS_PDI,
                     linewidth=1.3, linestyle="--", label="Jambe autocall (sans PDI)")
    ax_vega_ac.plot(df_b["spot"], df_b["vega_leg_pdi_pct"], color=COULEUR_PDI,
                     linewidth=1.3, linestyle="--", label="− Jambe PDI")
    ax_vega_ac.set_xlabel("Spot (% du niveau initial)")
    ax_vega_ac.set_ylabel("Vega de l'autocall complet\n(points de %, pour 1 pt de vol)")
    ax_vega_ac.legend(fontsize=8, loc="best")

    fig.tight_layout()
    chemin = os.path.join(REPERTOIRE_FIGURES, "figureA_sensibilites_pdi_autocall.png")
    fig.savefig(chemin, dpi=300)
    plt.close(fig)
    print(f"Figure enregistrée : {chemin}")


def main():
    t0 = time.time()
    os.makedirs(REPERTOIRE_FIGURES, exist_ok=True)

    print("Panneau (a) : formule fermée du PDI...")
    df_a = calculer_panneau_a()
    df_validations = valider_formule_fermee()
    print(df_validations.to_string(index=False))
    assert (df_validations["ecart_relatif_pct"] < 0.5).all(), "validation obligatoire échouée"

    print("Résolution du coupon au pair du produit de référence (spot=100)...")
    coupon = resoudre_coupon_reference()
    print(f"  coupon au pair = {coupon * 100:.2f}%")

    print("Panneau (b) : vega de l'autocall complet par Monte Carlo...")
    df_b = calculer_panneau_b(coupon)

    print("Discontinuité de delta à la barrière...")
    df_delta_discontinuite = calculer_discontinuite_delta()
    print(df_delta_discontinuite.to_string(index=False))

    print("Recherche du spot où le vega total de l'autocall s'annule...")
    spot_zero, vega_au_zero, erreur_std_zero = trouver_spot_zero_vega(coupon)
    print(f"  spot = {spot_zero:.2f}  (vega = {vega_au_zero * 100:.4f}%, erreur std = {erreur_std_zero * 100:.4f}%)")
    df_zero_vega = pd.DataFrame([{
        "spot_zero_vega": spot_zero,
        "vega_pct": vega_au_zero * 100,
        "erreur_std_pct": erreur_std_zero * 100,
    }])

    ecrire_csv_et_md(df_a, os.path.join(REPERTOIRE_FIGURES, "figureA_pdi_formule_fermee"), float_format="{:.4f}")
    # table Markdown allégée (points ronds) pour recopie directe dans le mémoire
    spots_ronds = np.arange(40, 131, 10)
    df_a_md = df_a[df_a["spot"].round(0).isin(spots_ronds)]
    ecrire_csv_et_md(df_a_md, os.path.join(REPERTOIRE_FIGURES, "figureA_pdi_formule_fermee_resume"), float_format="{:.4f}")

    ecrire_csv_et_md(df_validations, os.path.join(REPERTOIRE_FIGURES, "figureA_validations"), float_format="{:.4f}")
    ecrire_csv_et_md(df_b, os.path.join(REPERTOIRE_FIGURES, "figureA_autocall_vega"), float_format="{:.4f}")
    ecrire_csv_et_md(df_delta_discontinuite, os.path.join(REPERTOIRE_FIGURES, "figureA_delta_discontinuite"), float_format="{:.4f}")
    ecrire_csv_et_md(df_zero_vega, os.path.join(REPERTOIRE_FIGURES, "figureA_spot_zero_vega"), float_format="{:.4f}")

    tracer_figure(df_a, df_b)
    print(f"Terminé en {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
