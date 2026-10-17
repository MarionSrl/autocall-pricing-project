"""Figure E — Effet d'un indice Volatility Target sur le coupon au pair d'un
autocall, à forward contrôlé, seul puis combiné à un décrément (extension du
mémoire).

Produit identique à la Figure B : Athena 10 ans, observations annuelles,
barrière de rappel 100 %, PDI 60 % observé à maturité uniquement, coupon à
mémoire versé au rappel, coupon résolu pour que le prix = 100 % du nominal
(cf. src/pricer_autocall.py et src/coupon_solver.py). Seule la construction
du sous-jacent change.

Modèle : volatilité à 2 régimes (calme / stress) identique à la Figure D
(src/vol_target.py::simuler_regimes) -- indispensable ici, une vol constante
viderait le mécanisme Vol Target de son intérêt.

--- Pourquoi une grille à forward contrôlé (et pas juste "nu vs VT") -------

Une première version de cette figure comparait directement l'indice nu
"price return" (dividende q=3 %, forward 10 ans = S0*exp((r-q)*T) ~ 95) à un
indice Vol Target construit SANS décrément sur la jambe total return
(dividendes réinvestis, forward 10 ans = S0*exp(r*T) ~ 128.4 -- c'est la
propriété de martingale actualisée de l'indice VT, cf.
`tests/test_figure_e.py::test_indice_vt_martingale_sous_q`, PAS un "effet du
cash en période de stress" comme une lecture rapide pourrait le suggérer).
L'écart de coupon entre les deux mélangeait donc un effet de forward (~33
points d'indice d'écart, mécanique, rien à voir avec la volatilité) et
l'effet de volatilité que la figure est censée isoler -- ce que la vol
réalisée moyenne (17.7 % vs 16.2 % seulement) ne suffisait pas à expliquer.

Cette version compare à la place deux LIGNES (indice nu sur la jambe total
return à 100 % d'exposition / Vol Target 15 %) à travers trois COLONNES de
décrément en % (0 %, 3 %=q, 5 %), qui jouent exactement le rôle de l'indice B
de la Figure B (B_t = U_t * exp(-D*t), multiplicateur déterministe appliqué a
posteriori) : à D fixé, les deux lignes ont EXACTEMENT le même forward
théorique S0*exp((r-D)*T), déjà démontré identique pour l'indice nu et pour
l'indice Vol Target par la propriété de martingale actualisée ci-dessus.
Tout écart de coupon entre les deux lignes à D fixé est donc un effet de
volatilité pur, plus de forward. La colonne D=3%=q est de plus directement
comparable à l'indice "price return" historique des Figures A, B et D
(même forward, même mécanisme que le cas de contrôle B' de la Figure B --
voir `tests/test_figure_e.py::test_coupon_pair_identique_nu_decrement3_vs_price_return`).

Deux configurations supplémentaires sont conservées hors de cette grille
2x3, pour exposition complète du mécanisme :
    - Vol Target 10 % + décrément 3 % (même colonne D=3%=q que la grille,
      cible de volatilité plus basse)
    - Vol Target 15 % + décrément en points (K=5, soit 5 % de S0) : contexte
      path-dépendant, pas de forward contrôlable a priori (cf. ci-dessous).

--- Construction de l'indice Vol Target -----------------------------------

src/vol_target.py::construire_indice_vt, réutilisée telle quelle : jambe
risquée = indice total return (dividendes réinvestis, drift r), poche cash
rémunérée à r, levier L_t = min(sigma_cible / sigma_hat_t, 150%), sigma_hat_t
= vol réalisée sur une fenêtre glissante de 20 jours ouvrés CONNUE À LA
CLÔTURE DU JOUR t (donc utilisée sans anticipation pour l'exposition du jour
t vers t+1 -- le décalage d'un jour est déjà la convention native de
`vol_realisee_glissante`, voir sa docstring). Cette construction est
cohérente en risque neutre : la jambe risquée et la poche cash sont chacune,
une fois actualisées à r, des martingales sous Q, et un portefeuille
rebalancé à poids prévisibles (connus à t-1) entre deux martingales
actualisées en est une aussi -- vérifié empiriquement par
`tests/test_figure_e.py::test_indice_vt_martingale_sous_q`.

Le décrément (en %, aux niveaux 0/3/5 ; en points, K=5 comme la Figure B) est
appliqué APRÈS le Vol Target ou après l'indice nu, comme dans les indices
réels (le décrément est un frais prélevé sur l'indice déjà construit, pas sur
le sous-jacent brut) : src/indices.py::indice_decrement_pourcentage pour le
décrément en %, src/indices.py::appliquer_decrement_points pour le décrément
en points -- cette dernière PLANCHERISE désormais l'indice à 0 (barrière
absorbante), à la différence volontaire de l'indice C de la Figure B
(inchangé) : voir la docstring de la fonction pour la justification (la perte
de l'investisseur sur un produit à capital protégé/à risque ne peut pas
dépasser 100 % du nominal).

--- Forward théorique -------------------------------------------------------

Pour toute configuration à décrément en % D (y compris D=0, cas "rendement
total pur") : forward_theorique = S0 * exp((r-D)*T), EXACT (martingale
actualisée démontrée ci-dessus), identique pour la ligne "nu" et la ligne
"Vol Target" à D fixé.

Pour le décrément en points (vt15_decr_pts) : la même relation de récurrence
E[C_t | F_{t-1}] = exp(r*dt) * C_{t-1} - K*dt tient exactement, SANS
PLANCHER (le plancher casse la linéarité une fois un chemin absorbé à 0),
quel que soit le levier Vol Target appliqué -- parce que la jambe risquée et
le cash ont chacun un rendement conditionnel moyen exp(r*dt), quel que soit
le poids prévisible qui les combine (même argument que la martingale
actualisée). `src/indices.py::forward_theorique_decrement_points` (déjà
utilisée par la Figure B) s'applique donc ici aussi, à condition de la lire
comme un forward "SANS PLANCHER" : l'écart entre ce forward théorique et le
forward Monte Carlo effectivement observé (qui, lui, voit le plancher)
mesure la masse de probabilité absorbée à 0.

200 000 trajectoires, pas quotidien (252/an), 10 ans.

Écrit figures/figureE_vol_target_decrement.png (300 dpi) et les résultats
numériques dans figures/figureE_resultats.{csv,md}.
"""

import os
import sys
import time

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.marche import SEED_GLOBAL
from src.vol_target import simuler_regimes, simuler_indice_sous_jacent, construire_indice_vt
from src.indices import (
    indice_decrement_pourcentage,
    appliquer_decrement_points,
    forward_theorique_decrement_points,
)
from src.coupon_solver import resoudre_coupon_pair
from src.style_graphique import appliquer_style
from src.reporting import ecrire_csv_et_md

# Produit (identique à la Figure B)
S0 = 100.0
R = 0.025
Q = 0.03                   # dividende "price return" historique (= décrément 3% de la grille)
MATURITE = 10
DATES_OBS = np.arange(1, MATURITE + 1)
BARRIERE_AUTOCALL = 1.0
BARRIERE_CAPITAL = 0.60
NOMINAL = 1.0

# Modèle de volatilité à 2 régimes (identique à la Figure D)
SIGMA_BAS = 0.09
SIGMA_HAUT = 0.32
DUREE_CALME = 60
DUREE_STRESS = 20

# Mécanique Volatility Target (fenêtre identique à la Figure D, deux cibles ici)
L_MAX = 1.50
FENETRE = 20
SIGMA_CIBLE_1 = 0.15
SIGMA_CIBLE_2 = 0.10

# Grille 2 (nu / VT15) x 3 (décrément 0% / 3%=q / 5%) à forward contrôlé
DECREMENTS_GRILLE = {"decr0": 0.0, "decr3": Q, "decr5": 0.05}
DECREMENT_VT10 = Q           # config supplémentaire : VT10 + décrément 3%=q
K_DECREMENT = 5.0            # décrément en points (5% de S0), identique à la Figure B

NB_SIM = 200_000
NB_PAS_AN = 252
SEED = SEED_GLOBAL         # source unique : src/marche.py::SEED_GLOBAL

REPERTOIRE_RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPERTOIRE_FIGURES = os.path.join(REPERTOIRE_RACINE, "figures")

NOMS_NU = [f"nu_{d}" for d in DECREMENTS_GRILLE]
NOMS_VT15 = [f"vt15_{d}" for d in DECREMENTS_GRILLE]
NOMS = NOMS_NU + NOMS_VT15 + ["vt10_decr3", "vt15_decr_pts"]

LIBELLES = {
    "nu_decr0": "Indice nu, décrément 0% (= rendement total)",
    "nu_decr3": "Indice nu, décrément 3% (= Price Return q=3%)",
    "nu_decr5": "Indice nu, décrément 5%",
    "vt15_decr0": "Vol Target 15%, décrément 0% (= rendement total)",
    "vt15_decr3": "Vol Target 15%, décrément 3%",
    "vt15_decr5": "Vol Target 15%, décrément 5%",
    "vt10_decr3": "Vol Target 10%, décrément 3%",
    "vt15_decr_pts": "Vol Target 15% + décrément points (K=5, plancher 0)",
}
LIBELLES_COURTS = {
    "nu_decr0": "Nu 0%",
    "nu_decr3": "Nu 3%",
    "nu_decr5": "Nu 5%",
    "vt15_decr0": "VT15 0%",
    "vt15_decr3": "VT15 3%",
    "vt15_decr5": "VT15 5%",
    "vt10_decr3": "VT10 3%",
    "vt15_decr_pts": "VT15+pts",
}
COULEURS = {
    "nu_decr0": "#1f77b4",
    "nu_decr3": "#1f77b4",
    "nu_decr5": "#1f77b4",
    "vt15_decr0": "#d62728",
    "vt15_decr3": "#d62728",
    "vt15_decr5": "#d62728",
    "vt10_decr3": "#ff7f0e",
    "vt15_decr_pts": "#9467bd",
}


TAILLE_LOT = 20_000  # trajectoires par lot -- cf. docstring de construire_configurations


def extraire_obs_vol_terminal(trajectoire_quotidienne):
    """Extrait, à partir d'une trajectoire quotidienne (nb_sim, nb_jours+1) :
    les valeurs aux dates d'observation annuelles (hors t=0), la vol réalisée
    annualisée PAR TRAJECTOIRE sur l'horizon complet, la valeur terminale PAR
    TRAJECTOIRE (pour le forward MC), et un indicateur PAR TRAJECTOIRE du
    passage à un niveau == 0 à un moment quelconque de l'historique -- non
    encore moyennés, pour rester agrégeables correctement après concaténation
    de plusieurs lots.

    Le passage à 0 n'est possible QUE pour l'indice à décrément en points
    (src/indices.py::appliquer_decrement_points, plancherisé à 0, barrière
    absorbante) : le prélèvement est un montant fixe en points, pas un
    pourcentage, et une fois l'indice retombé à 0 il y reste. np.log(0) vaut
    -inf, et la vol réalisée (diff de logs) d'une trajectoire qui atteint ce
    plancher vaut alors -inf puis NaN (inf - inf) : volontairement propagée
    plutôt que masquée, et agrégée par la suite avec np.nanmean (cf.
    construire_configurations)."""
    indices_obs = [int(round(t * NB_PAS_AN)) for t in DATES_OBS]
    spots_obs = trajectoire_quotidienne[:, indices_obs]
    jamais_nul = (trajectoire_quotidienne <= 0.0).any(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        log_rendements = np.diff(np.log(trajectoire_quotidienne), axis=1)
        vol_par_trajectoire = log_rendements.std(axis=1, ddof=1) * np.sqrt(NB_PAS_AN)
    # .copy() impératif : un slice+indice entier (contrairement à l'indexation
    # "fancy" par liste utilisée ci-dessus pour spots_obs) renvoie une VUE
    # numpy, pas une copie -- cette vue retient tout le tableau quotidien
    # sous-jacent (plusieurs centaines de Mo par lot) vivant en mémoire via
    # son attribut .base, même après le `del` de la variable d'origine dans
    # la boucle de lots. Vérifié empiriquement : c'est la cause exacte d'une
    # fuite mémoire qui tue le script par OOM après une dizaine de lots.
    valeur_terminale = trajectoire_quotidienne[:, -1].copy()
    return spots_obs, vol_par_trajectoire, valeur_terminale, jamais_nul


def construire_configurations():
    """Construit les 8 configurations par lots de TAILLE_LOT trajectoires
    (NB_SIM / TAILLE_LOT lots), pour borner la mémoire : une trajectoire
    quotidienne complète à 200 000 trajectoires x 10 ans x 252 pas pèse ~4 Go
    en float64, et `simuler_indice_sous_jacent` alloue plusieurs tableaux
    temporaires de cette taille en interne (chocs, incréments, log-prix) --
    les garder tous en mémoire à la fois dépasse la mémoire disponible
    (vérifié : la version à un seul lot de 200 000 est tuée par l'OOM
    killer). Par lot de 20 000, chaque tableau quotidien pèse ~400 Mo :
    largement gérable, et regrouper des lots indépendants de même loi est la
    façon standard d'agrandir un échantillon Monte Carlo sans tout garder en
    mémoire simultanément.

    Au sein de CHAQUE lot, toutes les configurations partagent exactement les
    mêmes chocs browniens et le même chemin de régimes de volatilité : une
    seule trajectoire total return (q=0) est simulée par lot, et toutes les
    configurations (lignes "nu" ET lignes "Vol Target") en sont dérivées par
    décrément déterministe -- l'indice nu n'est plus simulé séparément avec
    un drift r-q (ce qui serait redondant : U_t * exp(-D*t) avec D=q donne
    exactement la même trajectoire, pas à pas, cf. `indice_decrement_pourcentage`
    et le test de neutralité dédié). Les lots entre eux utilisent des seeds
    différentes (dérivées de SEED_GLOBAL), donc indépendantes.
    """
    assert NB_SIM % TAILLE_LOT == 0, "NB_SIM doit être un multiple de TAILLE_LOT"
    nb_lots = NB_SIM // TAILLE_LOT
    nb_jours = NB_PAS_AN * MATURITE
    t0 = time.time()

    accum = {nom: {"spots_obs": [], "vol": [], "terminal": [], "nul": []} for nom in NOMS}

    def accumuler(nom, trajectoire_quotidienne):
        spots_obs, vol, terminal, nul = extraire_obs_vol_terminal(trajectoire_quotidienne)
        accum[nom]["spots_obs"].append(spots_obs)
        accum[nom]["vol"].append(vol)
        accum[nom]["terminal"].append(terminal)
        accum[nom]["nul"].append(nul)

    for lot in range(nb_lots):
        t_lot = time.time()
        seed_regime = SEED + lot
        seed_choc = SEED + 100_000 + lot  # décalage arbitraire, distincte de seed_regime

        sigma_path = simuler_regimes(nb_jours, TAILLE_LOT, seed_regime,
                                      SIGMA_BAS, SIGMA_HAUT, DUREE_CALME, DUREE_STRESS)

        # Jambe total return (q=0), commune à TOUTES les configurations de ce
        # lot -- lignes "nu" (exposition 100%, décrément appliqué directement)
        # et lignes "Vol Target" (décrément appliqué après construction VT).
        traj_tr = simuler_indice_sous_jacent(S0, R, 0.0, sigma_path, NB_PAS_AN, seed_choc)
        del sigma_path
        t_quotidien = np.arange(traj_tr.shape[1]) / NB_PAS_AN

        for d_nom, D in DECREMENTS_GRILLE.items():
            nu_d = traj_tr if D == 0.0 else indice_decrement_pourcentage(traj_tr, t_quotidien, D)
            accumuler(f"nu_{d_nom}", nu_d)
            if D != 0.0:
                del nu_d

        vt15, _ = construire_indice_vt(traj_tr, R, SIGMA_CIBLE_1, L_MAX, FENETRE, NB_PAS_AN)
        for d_nom, D in DECREMENTS_GRILLE.items():
            vt15_d = vt15 if D == 0.0 else indice_decrement_pourcentage(vt15, t_quotidien, D)
            accumuler(f"vt15_{d_nom}", vt15_d)
            if D != 0.0:
                del vt15_d

        vt15_decr_pts = appliquer_decrement_points(vt15, K_DECREMENT, NB_PAS_AN)
        accumuler("vt15_decr_pts", vt15_decr_pts)
        del vt15, vt15_decr_pts

        vt10, _ = construire_indice_vt(traj_tr, R, SIGMA_CIBLE_2, L_MAX, FENETRE, NB_PAS_AN)
        del traj_tr
        vt10_decr3 = indice_decrement_pourcentage(vt10, t_quotidien, DECREMENT_VT10)
        accumuler("vt10_decr3", vt10_decr3)
        del vt10, vt10_decr3

        print(f"  lot {lot + 1}/{nb_lots} terminé en {time.time() - t_lot:.1f}s")

    configs = {}
    for nom in NOMS:
        spots_obs = np.concatenate(accum[nom]["spots_obs"], axis=0)
        vol = np.concatenate(accum[nom]["vol"])
        terminal = np.concatenate(accum[nom]["terminal"])
        nul = np.concatenate(accum[nom]["nul"])
        # nanmean : quelques trajectoires de 'vt15_decr_pts' atteignent le
        # plancher 0 à un moment de l'historique (cf. extraire_obs_vol_terminal)
        # et ont donc une vol réalisée NaN -- ne doit pas invalider la moyenne
        # des autres trajectoires.
        configs[nom] = (spots_obs, float(np.nanmean(vol)), float(terminal.mean()), float(nul.mean()))
        if nul.mean() > 0:
            print(f"  ATTENTION config '{nom}' : {nul.mean() * 100:.2f}% des trajectoires "
                  f"atteignent le plancher 0 à un moment de l'historique (cf. docstring du module).")

    print(f"Toutes les configurations construites en {time.time() - t0:.1f}s")
    return configs


def forward_theorique_par_config():
    """Forward théorique à MATURITE, EXACT pour toute configuration à
    décrément en % (identique pour les lignes "nu" et "Vol Target" à D fixé
    -- cf. docstring du module). Pour le décrément en points, forward
    théorique SANS PLANCHER (cf. docstring du module) : l'écart avec le
    forward Monte Carlo (qui lui voit le plancher) mesure la masse de
    probabilité absorbée à 0."""
    forwards = {}
    for d_nom, D in DECREMENTS_GRILLE.items():
        forwards[f"nu_{d_nom}"] = S0 * np.exp((R - D) * MATURITE)
        forwards[f"vt15_{d_nom}"] = S0 * np.exp((R - D) * MATURITE)
    forwards["vt10_decr3"] = S0 * np.exp((R - DECREMENT_VT10) * MATURITE)
    forwards["vt15_decr_pts"] = forward_theorique_decrement_points(S0, R, K_DECREMENT, MATURITE, NB_PAS_AN)
    return forwards


def coupon_ic95(resultat, r):
    """Approxime l'écart-type du coupon au pair par la méthode delta locale :
    d(payoff)/d(coupon) = t_rappel * exp(-r*t_rappel) pour une trajectoire
    rappelée (coupon versé = (1+coupon*t_rappel)*disc), 0 pour une
    trajectoire non rappelée (le payoff ne dépend alors pas du coupon).
    L'écart-type du coupon est l'écart-type Monte Carlo du prix divisé par
    la sensibilité moyenne (jacobien scalaire de la relation prix(coupon),
    valide localement autour du coupon au pair résolu)."""
    t_rappel = resultat.dates_rappel
    rappelees = ~np.isnan(t_rappel)
    t_rappel_sans_nan = np.where(rappelees, t_rappel, 0.0)
    sensibilite = np.where(rappelees, t_rappel_sans_nan * np.exp(-r * t_rappel_sans_nan), 0.0)
    dprix_dcoupon = sensibilite.mean()
    erreur_std_coupon = resultat.erreur_std / dprix_dcoupon
    return erreur_std_coupon, 1.96 * erreur_std_coupon


def main():
    t0 = time.time()
    os.makedirs(REPERTOIRE_FIGURES, exist_ok=True)

    configs = construire_configurations()
    forwards_theoriques = forward_theorique_par_config()

    lignes = []
    resultats_figure = {}
    for nom in NOMS:
        spots_obs, vol_moyenne, forward_mc, proba_nul = configs[nom]
        coupon_pair, resultat = resoudre_coupon_pair(
            spots_obs, S0, R, DATES_OBS, BARRIERE_AUTOCALL, BARRIERE_CAPITAL, nominal=NOMINAL
        )
        erreur_std_coupon, demi_largeur_ic95 = coupon_ic95(resultat, R)

        # Vérification (pas seulement affichée mais testée) : la perte de
        # l'investisseur ne peut pas dépasser 100% du nominal -- garanti par
        # le plancher à 0 de l'indice sous-jacent (spot_final >= 0 partout).
        assert resultat.spot_final.min() >= -1e-9, nom
        assert resultat.payoffs.min() >= -1e-9, nom

        proba_maturite = np.isnan(resultat.dates_rappel).mean()
        proba_rappel_avant_maturite = 1.0 - proba_maturite
        proba_pdi = resultat.pdi_actif.mean()
        if resultat.pdi_actif.any():
            pertes_individuelles = 1.0 - resultat.spot_final[resultat.pdi_actif] / S0
            assert pertes_individuelles.max() <= 1.0 + 1e-9, nom
            perte_cond = pertes_individuelles.mean()
        else:
            perte_cond = np.nan

        resultats_figure[nom] = {
            "coupon_pair": coupon_pair,
            "coupon_ic95_demi_largeur": demi_largeur_ic95,
            "proba_rappel_avant_maturite": proba_rappel_avant_maturite,
            "proba_pdi": proba_pdi,
            "perte_cond": perte_cond,
        }
        lignes.append({
            "configuration": LIBELLES[nom],
            "coupon_pair_pct": coupon_pair * 100,
            "coupon_ic95_demi_largeur_pct": demi_largeur_ic95 * 100,
            "vol_realisee_moyenne_pct": vol_moyenne * 100,
            "proba_rappel_avant_maturite_pct": proba_rappel_avant_maturite * 100,
            "proba_pdi_actif_pct": proba_pdi * 100,
            "perte_moyenne_cond_pct": perte_cond * 100,
            "forward_theorique_10y": forwards_theoriques[nom],
            "forward_mc_10y": forward_mc,
            "prix_verif_pct": resultat.prix * 100,
            "erreur_std_mc_pct": resultat.erreur_std * 100,
            # Diagnostic : fraction des trajectoires où l'indice décrémenté
            # atteint le plancher 0 à un moment de l'historique -- possible
            # uniquement pour le décrément en points (plancherisé), jamais
            # pour un décrément en % (multiplicatif, toujours strictement
            # positif) ni pour l'indice nu ou le Vol Target seuls. Nul pour
            # toute configuration où le phénomène ne s'applique pas.
            "proba_indice_nul_pct": proba_nul * 100,
        })
        print(f"  {nom:14s} coupon au pair = {coupon_pair * 100:6.2f}% "
              f"(IC95% +/-{demi_largeur_ic95 * 100:.3f} pt), "
              f"vol réalisée moy. = {vol_moyenne * 100:5.2f}%, "
              f"forward théo. = {forwards_theoriques[nom]:6.1f}, forward MC = {forward_mc:6.1f}"
              + (f", indice nul : {proba_nul * 100:.2f}%" if proba_nul > 0 else ""))

    df = pd.DataFrame(lignes)
    ecrire_csv_et_md(df, os.path.join(REPERTOIRE_FIGURES, "figureE_resultats"), float_format="{:.3f}")

    tracer_figure(resultats_figure)
    print(f"Terminé en {time.time() - t0:.1f}s")


def tracer_figure(resultats):
    appliquer_style()
    fig, (ax_coupon, ax_risque) = plt.subplots(1, 2, figsize=(15, 6.5))

    # --- Panneau principal : grille 2x3 à forward contrôlé, barres groupées
    # nu vs Vol Target 15% pour chaque niveau de décrément -- lecture directe
    # de l'effet Vol Target "toutes choses égales par ailleurs" (même forward
    # théorique sur chaque paire). ---
    labels_decrement = ["0% (= rendement total)", "3% (= q)", "5%"]
    x = np.arange(len(DECREMENTS_GRILLE))
    largeur = 0.35
    coupons_nu = [resultats[f"nu_{d}"]["coupon_pair"] * 100 for d in DECREMENTS_GRILLE]
    erreurs_nu = [resultats[f"nu_{d}"]["coupon_ic95_demi_largeur"] * 100 for d in DECREMENTS_GRILLE]
    coupons_vt = [resultats[f"vt15_{d}"]["coupon_pair"] * 100 for d in DECREMENTS_GRILLE]
    erreurs_vt = [resultats[f"vt15_{d}"]["coupon_ic95_demi_largeur"] * 100 for d in DECREMENTS_GRILLE]

    ax_coupon.bar(x - largeur / 2, coupons_nu, width=largeur, yerr=erreurs_nu,
                  color=COULEURS["nu_decr0"], capsize=4, label="Indice nu")
    ax_coupon.bar(x + largeur / 2, coupons_vt, width=largeur, yerr=erreurs_vt,
                  color=COULEURS["vt15_decr0"], capsize=4, label="Vol Target 15%")
    ax_coupon.set_xticks(x)
    ax_coupon.set_xticklabels(labels_decrement)
    ax_coupon.set_xlabel("Décrément en % (forward contrôlé à D fixé)")
    ax_coupon.set_ylabel("Coupon annuel au pair (%, IC95%)")
    ax_coupon.legend()

    # --- Panneau secondaire : rappel / PDI / perte conditionnelle pour les 8
    # configurations (barres groupées, axe de pourcentage partagé -- cf.
    # convention de la Figure B). ---
    noms = NOMS
    libelles_courts = [LIBELLES_COURTS[n] for n in noms]
    x2 = np.arange(len(noms))
    largeur2 = 0.25
    proba_rappel = [resultats[n]["proba_rappel_avant_maturite"] * 100 for n in noms]
    proba_pdi = [resultats[n]["proba_pdi"] * 100 for n in noms]
    pertes = [resultats[n]["perte_cond"] * 100 for n in noms]
    ax_risque.bar(x2 - largeur2, proba_rappel, width=largeur2, color="#1f77b4",
                  label="Proba. rappel avant maturité")
    ax_risque.bar(x2, proba_pdi, width=largeur2, color="#d62728",
                  label="Proba. activation PDI")
    ax_risque.bar(x2 + largeur2, pertes, width=largeur2, color="#7f7f7f",
                  label="Perte moy. conditionnelle")
    ax_risque.set_xticks(x2)
    ax_risque.set_xticklabels(libelles_courts, rotation=25, ha="right")
    ax_risque.set_ylabel("Pourcentage (%)")
    ax_risque.legend(fontsize=8)

    fig.tight_layout()
    chemin = os.path.join(REPERTOIRE_FIGURES, "figureE_vol_target_decrement.png")
    fig.savefig(chemin, dpi=300)
    plt.close(fig)
    print(f"Figure enregistrée : {chemin}")


if __name__ == "__main__":
    main()
