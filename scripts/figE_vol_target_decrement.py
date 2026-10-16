"""Figure E — Effet d'un indice Volatility Target sur le coupon au pair d'un
autocall, seul puis combiné à un décrément (extension du mémoire).

Produit identique à la Figure B : Athena 10 ans, observations annuelles,
barrière de rappel 100 %, PDI 60 % observé à maturité uniquement, coupon à
mémoire versé au rappel, coupon résolu pour que le prix = 100 % du nominal
(cf. src/pricer_autocall.py et src/coupon_solver.py). Seule la construction
du sous-jacent change.

Modèle : volatilité à 2 régimes (calme / stress) identique à la Figure D
(src/vol_target.py::simuler_regimes) -- indispensable ici, une vol constante
viderait le mécanisme Vol Target de son intérêt.

Construction de l'indice Vol Target (src/vol_target.py::construire_indice_vt,
réutilisée telle quelle) : jambe risquée = indice total return (dividendes
réinvestis, drift r), poche cash rémunérée à r, levier L_t = min(sigma_cible
/ sigma_hat_t, 150%), sigma_hat_t = vol réalisée sur une fenêtre glissante de
20 jours ouvrés CONNUE À LA CLÔTURE DU JOUR t (donc utilisée sans anticipation
pour l'exposition du jour t vers t+1 -- le décalage d'un jour est déjà la
convention native de `vol_realisee_glissante`, voir sa docstring). Cette
construction est cohérente en risque neutre : la jambe risquée et la poche
cash sont chacune, une fois actualisées à r, des martingales sous Q, et un
portefeuille rebalancé à poids prévisibles (connus à t-1) entre deux
martingales actualisées en est une aussi -- vérifié empiriquement par
`tests/test_figure_e.py::test_indice_vt_martingale_sous_q`.

Le décrément (identique en paramètres à la Figure B : D=5%/an en %, K=5
points soit 5% de S0 en points) est appliqué APRÈS le Vol Target, comme dans
les indices réels (le décrément est un frais prélevé sur l'indice optimisé,
pas sur le sous-jacent brut) : src/indices.py::indice_decrement_pourcentage
pour le décrément en %, src/indices.py::appliquer_decrement_points (nouvelle
fonction, généralisation de la récurrence déjà utilisée par la Figure B à une
trajectoire quotidienne quelconque) pour le décrément en points.

Cinq configurations, TOUTES construites sur les mêmes chocs browniens et le
même chemin de régimes de volatilité (seule la seed du générateur de chocs
change entre l'indice "price return" et la jambe risquée "total return" des
indices Vol Target -- par construction de `simuler_indice_sous_jacent`, une
même seed produit les mêmes chocs quel que soit le drift demandé, donc la
même seed pour les deux donne les mêmes chocs, seul le drift diffère) :

    1. nu              indice nu price return (dividende q=3%, comme A en Fig. B)
    2. vt15            Vol Target 15%, sans décrément
    3. vt10            Vol Target 10%, sans décrément
    4. vt15_decr_pct   Vol Target 15% + décrément 5%/an en %
    5. vt15_decr_pts   Vol Target 15% + décrément en points (K=5, soit 5% de S0)

Hypothèse à vérifier (pas imposée au résultat -- les chiffres sont ceux de la
simulation) : à structure identique, un Vol Target seul réduirait le coupon
au pair par rapport à l'indice nu (l'investisseur cède de la convexité en
échange d'une volatilité plus stable), et c'est l'ajout d'un décrément qui
reconstituerait le budget de coupon. Les 5 lignes du tableau de résultats
permettent de confirmer ou d'infirmer ce mécanisme chiffre en main.

Pour chaque configuration : coupon au pair (solveur Brent, trajectoires
figées) avec IC95% approché par méthode delta (le payoff n'est linéaire en
coupon que pour les trajectoires rappelées : d(payoff)/d(coupon) = t_rappel *
exp(-r*t_rappel) si rappelée, 0 sinon -- l'écart-type du coupon est donc
l'écart-type Monte Carlo du prix divisé par cette sensibilité moyenne), vol
réalisée moyenne sur l'horizon complet, probabilité de rappel avant maturité,
probabilité d'activation du PDI, perte moyenne conditionnelle, et forward à
10 ans (moyenne Monte Carlo de la trajectoire terminale -- aucune formule
fermée n'existe pour un indice Vol Target, contrairement à l'indice nu dont
le forward MC sert de validation croisée contre le forward fermé
S0*exp((r-q)*T) de la Figure B).

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
from src.indices import indice_decrement_pourcentage, appliquer_decrement_points
from src.coupon_solver import resoudre_coupon_pair
from src.style_graphique import appliquer_style
from src.reporting import ecrire_csv_et_md

# Produit (identique à la Figure B)
S0 = 100.0
R = 0.025
Q = 0.03                   # dividende de l'indice nu "price return" (config 1 seulement)
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

# Décréments (mêmes paramètres que la Figure B)
D_DECREMENT = 0.05         # décrément en %, identique au D de la Figure B
K_DECREMENT = 5.0          # décrément en points (5% de S0), identique au K de la Figure B

NB_SIM = 200_000
NB_PAS_AN = 252
SEED = SEED_GLOBAL         # source unique : src/marche.py::SEED_GLOBAL

REPERTOIRE_RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPERTOIRE_FIGURES = os.path.join(REPERTOIRE_RACINE, "figures")

NOMS = ["nu", "vt15", "vt10", "vt15_decr_pct", "vt15_decr_pts"]

LIBELLES = {
    "nu": "Indice nu (price return)",
    "vt15": "Vol Target 15%",
    "vt10": "Vol Target 10%",
    "vt15_decr_pct": "Vol Target 15% + décrément 5%/an",
    "vt15_decr_pts": "Vol Target 15% + décrément points (K=5)",
}
LIBELLES_COURTS = {
    "nu": "Nu",
    "vt15": "VT 15%",
    "vt10": "VT 10%",
    "vt15_decr_pct": "VT 15% + décr. %",
    "vt15_decr_pts": "VT 15% + décr. pts",
}
COULEURS = {
    "nu": "#1f77b4",
    "vt15": "#d62728",
    "vt10": "#ff7f0e",
    "vt15_decr_pct": "#2ca02c",
    "vt15_decr_pts": "#9467bd",
}


TAILLE_LOT = 20_000  # trajectoires par lot -- cf. docstring de construire_configurations


def extraire_obs_vol_terminal(trajectoire_quotidienne):
    """Extrait, à partir d'une trajectoire quotidienne (nb_sim, nb_jours+1) :
    les valeurs aux dates d'observation annuelles (hors t=0), la vol réalisée
    annualisée PAR TRAJECTOIRE sur l'horizon complet, la valeur terminale PAR
    TRAJECTOIRE (pour le forward MC), et un indicateur PAR TRAJECTOIRE du
    passage à un niveau <= 0 à un moment quelconque de l'historique -- non
    encore moyennés, pour rester agrégeables correctement après concaténation
    de plusieurs lots.

    Le passage à 0 ou en-dessous n'est possible QUE pour un indice à
    décrément en points (src/indices.py::appliquer_decrement_points) : le
    prélèvement est un montant fixe en points, pas un pourcentage, et une
    fois l'indice retombé sous ce montant la récurrence n'est pas plafonnée
    à 0 (même convention, non plafonnée, que l'indice C de la Figure B) --
    elle continue à s'enfoncer en territoire négatif plutôt que de rester
    bloquée à 0. np.log d'une valeur <= 0 vaut NaN : la vol réalisée de ces
    trajectoires est donc NaN, propagée volontairement plutôt que masquée,
    et agrégée par la suite avec np.nanmean (cf. construire_configurations)."""
    indices_obs = [int(round(t * NB_PAS_AN)) for t in DATES_OBS]
    spots_obs = trajectoire_quotidienne[:, indices_obs]
    jamais_positif_ou_nul = (trajectoire_quotidienne <= 0.0).any(axis=1)
    with np.errstate(invalid="ignore"):
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
    return spots_obs, vol_par_trajectoire, valeur_terminale, jamais_positif_ou_nul


def construire_configurations():
    """Construit les 5 configurations par lots de TAILLE_LOT trajectoires
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
    mêmes chocs browniens et le même chemin de régimes de volatilité (seed de
    régimes et seed de chocs fixées par lot, réutilisées à l'identique pour
    l'indice nu et pour la jambe risquée total return -- une même seed donne
    les mêmes chocs quel que soit le drift demandé, cf. docstring de
    `simuler_indice_sous_jacent`). Les lots entre eux utilisent des seeds
    différentes (dérivées de SEED_GLOBAL), donc indépendantes.
    """
    assert NB_SIM % TAILLE_LOT == 0, "NB_SIM doit être un multiple de TAILLE_LOT"
    nb_lots = NB_SIM // TAILLE_LOT
    nb_jours = NB_PAS_AN * MATURITE
    t0 = time.time()

    accum = {nom: {"spots_obs": [], "vol": [], "terminal": [], "negatif": []} for nom in NOMS}

    def accumuler(nom, trajectoire_quotidienne):
        spots_obs, vol, terminal, negatif = extraire_obs_vol_terminal(trajectoire_quotidienne)
        accum[nom]["spots_obs"].append(spots_obs)
        accum[nom]["vol"].append(vol)
        accum[nom]["terminal"].append(terminal)
        accum[nom]["negatif"].append(negatif)

    for lot in range(nb_lots):
        t_lot = time.time()
        seed_regime = SEED + lot
        seed_choc = SEED + 100_000 + lot  # décalage arbitraire, distincte de seed_regime

        sigma_path = simuler_regimes(nb_jours, TAILLE_LOT, seed_regime,
                                      SIGMA_BAS, SIGMA_HAUT, DUREE_CALME, DUREE_STRESS)

        traj_nu = simuler_indice_sous_jacent(S0, R, Q, sigma_path, NB_PAS_AN, seed_choc)
        accumuler("nu", traj_nu)
        del traj_nu

        # Jambe risquée commune aux 4 configurations Vol Target de ce lot :
        # indice total return (q=0), MÊME seed_choc que l'indice nu ci-dessus
        # => mêmes chocs browniens, seul le drift diffère.
        traj_tr = simuler_indice_sous_jacent(S0, R, 0.0, sigma_path, NB_PAS_AN, seed_choc)
        del sigma_path

        vt15, _ = construire_indice_vt(traj_tr, R, SIGMA_CIBLE_1, L_MAX, FENETRE, NB_PAS_AN)
        accumuler("vt15", vt15)

        vt10, _ = construire_indice_vt(traj_tr, R, SIGMA_CIBLE_2, L_MAX, FENETRE, NB_PAS_AN)
        accumuler("vt10", vt10)
        del traj_tr, vt10

        t_quotidien = np.arange(vt15.shape[1]) / NB_PAS_AN
        vt15_decr_pct = indice_decrement_pourcentage(vt15, t_quotidien, D_DECREMENT)
        accumuler("vt15_decr_pct", vt15_decr_pct)
        del vt15_decr_pct

        vt15_decr_pts = appliquer_decrement_points(vt15, K_DECREMENT, NB_PAS_AN)
        accumuler("vt15_decr_pts", vt15_decr_pts)
        del vt15, vt15_decr_pts

        print(f"  lot {lot + 1}/{nb_lots} terminé en {time.time() - t_lot:.1f}s")

    configs = {}
    for nom in NOMS:
        spots_obs = np.concatenate(accum[nom]["spots_obs"], axis=0)
        vol = np.concatenate(accum[nom]["vol"])
        terminal = np.concatenate(accum[nom]["terminal"])
        negatif = np.concatenate(accum[nom]["negatif"])
        # nanmean : quelques trajectoires de 'vt15_decr_pts' passent sous 0 à
        # un moment de l'historique (cf. extraire_obs_vol_terminal) et ont
        # donc une vol réalisée NaN -- ne doit pas invalider la moyenne des
        # autres trajectoires.
        configs[nom] = (spots_obs, float(np.nanmean(vol)), float(terminal.mean()), float(negatif.mean()))
        if negatif.mean() > 0:
            print(f"  ATTENTION config '{nom}' : {negatif.mean() * 100:.2f}% des trajectoires "
                  f"passent à un niveau <= 0 à un moment de l'historique (cf. docstring du module).")

    print(f"Toutes les configurations construites en {time.time() - t0:.1f}s")
    return configs


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

    lignes = []
    resultats_figure = {}
    for nom in NOMS:
        spots_obs, vol_moyenne, forward_mc, proba_negatif = configs[nom]
        coupon_pair, resultat = resoudre_coupon_pair(
            spots_obs, S0, R, DATES_OBS, BARRIERE_AUTOCALL, BARRIERE_CAPITAL, nominal=NOMINAL
        )
        erreur_std_coupon, demi_largeur_ic95 = coupon_ic95(resultat, R)

        proba_maturite = np.isnan(resultat.dates_rappel).mean()
        proba_rappel_avant_maturite = 1.0 - proba_maturite
        proba_pdi = resultat.pdi_actif.mean()
        if resultat.pdi_actif.any():
            perte_cond = (1.0 - resultat.spot_final[resultat.pdi_actif] / S0).mean()
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
            "forward_mc_10y": forward_mc,
            "prix_verif_pct": resultat.prix * 100,
            "erreur_std_mc_pct": resultat.erreur_std * 100,
            # Diagnostic : fraction des trajectoires où l'indice décrémenté
            # passe à un niveau <= 0 à un moment de l'historique -- possible
            # uniquement pour un décrément en points, non plafonné à 0 (même
            # convention que l'indice C de la Figure B), jamais pour un
            # décrément en % (multiplicatif, toujours strictement positif)
            # ni pour l'indice nu ou le Vol Target seul. Nul pour toute
            # configuration où le phénomène ne s'applique pas.
            "proba_indice_negatif_pct": proba_negatif * 100,
        })
        print(f"  {nom:16s} coupon au pair = {coupon_pair * 100:6.2f}% "
              f"(IC95% +/-{demi_largeur_ic95 * 100:.3f} pt), "
              f"vol réalisée moy. = {vol_moyenne * 100:5.2f}%, "
              f"forward MC 10y = {forward_mc:6.1f}"
              + (f", indice <=0 : {proba_negatif * 100:.2f}%" if proba_negatif > 0 else ""))

    df = pd.DataFrame(lignes)
    ecrire_csv_et_md(df, os.path.join(REPERTOIRE_FIGURES, "figureE_resultats"), float_format="{:.3f}")

    tracer_figure(resultats_figure)
    print(f"Terminé en {time.time() - t0:.1f}s")


def tracer_figure(resultats):
    appliquer_style()
    fig, (ax_coupon, ax_risque) = plt.subplots(1, 2, figsize=(14, 6))

    noms = NOMS
    couleurs = [COULEURS[n] for n in noms]
    libelles_courts = [LIBELLES_COURTS[n] for n in noms]

    # --- Panneau principal : coupon au pair (+ IC95%) ---
    coupons = [resultats[n]["coupon_pair"] * 100 for n in noms]
    erreurs = [resultats[n]["coupon_ic95_demi_largeur"] * 100 for n in noms]
    ax_coupon.bar(libelles_courts, coupons, yerr=erreurs, color=couleurs, capsize=4)
    ax_coupon.set_ylabel("Coupon annuel au pair (%, IC95%)")
    ax_coupon.tick_params(axis="x", rotation=20)

    # --- Panneau secondaire : rappel / PDI / perte conditionnelle (barres
    # groupées, axe de pourcentage partagé -- cf. convention de la Figure B) ---
    x = np.arange(len(noms))
    largeur = 0.25
    proba_rappel = [resultats[n]["proba_rappel_avant_maturite"] * 100 for n in noms]
    proba_pdi = [resultats[n]["proba_pdi"] * 100 for n in noms]
    pertes = [resultats[n]["perte_cond"] * 100 for n in noms]
    ax_risque.bar(x - largeur, proba_rappel, width=largeur, color="#1f77b4",
                  label="Proba. rappel avant maturité")
    ax_risque.bar(x, proba_pdi, width=largeur, color="#d62728",
                  label="Proba. activation PDI")
    ax_risque.bar(x + largeur, pertes, width=largeur, color="#7f7f7f",
                  label="Perte moy. conditionnelle")
    ax_risque.set_xticks(x)
    ax_risque.set_xticklabels(libelles_courts, rotation=20)
    ax_risque.set_ylabel("Pourcentage (%)")
    ax_risque.legend(fontsize=8)

    fig.tight_layout()
    chemin = os.path.join(REPERTOIRE_FIGURES, "figureE_vol_target_decrement.png")
    fig.savefig(chemin, dpi=300)
    plt.close(fig)
    print(f"Figure enregistrée : {chemin}")


if __name__ == "__main__":
    main()
