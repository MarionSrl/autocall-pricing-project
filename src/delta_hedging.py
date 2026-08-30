"""Grille de delta/gamma et simulation de couverture en delta hedging
(Figure D, section III.2 du mémoire).

Porte le moteur de couverture du notebook (`construire_grille_delta` /
`simuler_delta_hedging`) en module réutilisable, en s'appuyant sur le pricer
partagé `src/pricer_autocall.py::pricer_autocall` plutôt que de dupliquer la
logique de payoff.

Convention d'échelle (dollar delta / dollar gamma), à ne pas casser :
`pricer_autocall` renvoie un prix en fraction du nominal (ex. 0.98 pour un
nominal de 100). En notant f(S) cette fraction-prix et S0 le nominal fixe de
référence, le prix en cash est V(S) = S0 * f(S), d'où :

    delta_$ = dV/dS = S0 * f'(S)   (nombre de "parts" à détenir, sans unité)
    gamma_$ = d²V/dS² = S0 * f''(S)   (unité : 1 / $)

Une seule puissance de S0 dans les deux cas (pas S0² pour le gamma) : c'est ce
qui rend `delta_$` directement utilisable comme quantité de sous-jacent dans
`cash -= (delta - position) * spot`, et `gamma_$` directement substituable
dans la formule de P&L de gamma-trading standard.

Convention de signe (à ne pas inverser) : la simulation représente un
émetteur qui vend le produit (encaisse `prix_initial * s0`) et le couvre en
delta au prix modèle -- il est donc "short" l'option, c'est-à-dire short
gamma au sens de sa propre position de couverture. Par un argument de
réplication standard (Itô sur le portefeuille couvert), son P&L résiduel de
gamma-trading est :

    dPnL ≈ ½ · gamma_$ · S² · (σ_modèle² − σ_réalisée²) · dt

(σ_modèle² en premier, pas σ_réalisée² -- c'est l'inverse de la formule
souvent citée de façon informelle pour un *acheteur* d'option). Vérifié
empiriquement dans scripts/figD_hedging_produit_notebook.py : avec cette
convention, la prédiction théorique reproduit bien le signe et l'ordre de
grandeur du P&L simulé pour les 4 niveaux de volatilité réalisée testés.

Point de vue et signe de gamma_$ (à ne pas confondre) : gamma_$ = S0*f''(S)
est le gamma de f(S), la valeur actualisée du flux versé A L'INVESTISSEUR --
exactement la même fonction, et la même convention (aucun changement de
perspective), que celle utilisée pour le vega de l'autocall en Figure A. Ce
n'est PAS le gamma "de position" de l'émetteur. Sur le produit de la Figure D,
gamma_$ est négatif (f est concave près du spot initial : l'investisseur est
structurellement "court" l'optionalité de barrière -- le put down-and-in --
cédée à l'émetteur en échange du coupon), tout comme le vega de l'autocall en
Figure A est négatif au spot initial du produit de référence (-68.40 pt de %,
cf. figures/figureA_autocall_vega.csv) : même sous-jacent économique, même
signe, deux figures cohérentes. Avec gamma_$ négatif, la formule ci-dessus
prédit -- et la simulation confirme -- un P&L de couverture CROISSANT avec la
volatilité réalisée : à l'inverse de l'intuition usuelle "vendeur d'option =
short gamma" (vraie pour une option vanille, toujours convexe), l'émetteur de
ce produit se retrouve net LONG gamma sur son livre couvert une fois delta-
hedgé, parce que la fonction qu'il vend (et doit répliquer) est concave, pas
convexe.
"""

import numpy as np
from scipy.interpolate import RegularGridInterpolator

from .simulation import simuler_a_dates
from .pricer_autocall import pricer_autocall


def construire_grille_delta_gamma(s0, r, q, sigma, dates_obs, barriere_ac, coupon, barriere_cap,
                                   spots_grid, temps_grid, nb_sim_mc, seed):
    """Grilles delta_$(temps, spot) et gamma_$(temps, spot) par différences
    finies (bump ±1% du spot pour delta, + valeur centrale pour gamma), à
    trajectoires communes (même seed => mêmes chocs pour up/mid/down à un
    point de grille donné), en ne simulant que les dates d'observation
    restantes (via `simuler_a_dates`, pas de grille quotidienne : inutile ici,
    l'indice sous-jacent n'est pas path-dépendant)."""
    dates_obs = np.asarray(dates_obs, dtype=float)
    delta_grid = np.zeros((len(temps_grid), len(spots_grid)))
    gamma_grid = np.zeros((len(temps_grid), len(spots_grid)))

    for i, t in enumerate(temps_grid):
        dates_restantes = dates_obs[dates_obs > t + 1e-9] - t
        if len(dates_restantes) == 0:
            continue
        seed_ligne = seed + i

        for j, s in enumerate(spots_grid):
            ds = s * 0.01
            prix = {}
            for label, s_test in (("haut", s + ds), ("milieu", s), ("bas", s - ds)):
                spots_obs = simuler_a_dates(s_test, r - q, sigma, dates_restantes, nb_sim_mc, seed_ligne)[:, 1:]
                prix[label] = pricer_autocall(spots_obs, s0, r, dates_restantes, barriere_ac, coupon, barriere_cap).prix

            delta_grid[i, j] = (prix["haut"] - prix["bas"]) / (2 * ds) * s0
            gamma_grid[i, j] = (prix["haut"] - 2 * prix["milieu"] + prix["bas"]) / (ds**2) * s0

    kwargs_interp = dict(method="linear", bounds_error=False, fill_value=0.0)
    interp_delta = RegularGridInterpolator((temps_grid, spots_grid), delta_grid, **kwargs_interp)
    interp_gamma = RegularGridInterpolator((temps_grid, spots_grid), gamma_grid, **kwargs_interp)
    return delta_grid, gamma_grid, interp_delta, interp_gamma


def simuler_couverture(trajectoire, s0, r, interp_delta, dates_obs, barriere_ac, coupon, barriere_cap,
                        prix_initial, nb_pas_an, freq_rebal, interp_gamma=None):
    """Simule le PnL de couverture en delta hedging le long d'UNE trajectoire
    quotidienne (rebalancement tous les `freq_rebal` jours, delta interpolé
    sur la grille pré-calculée). Si `interp_gamma` est fourni, retourne aussi
    la liste des couples (spot, gamma_$) observés à chaque date de
    rebalancement (utilisée pour estimer, hors de cette fonction, le gamma
    moyen -- ou le gamma·S² moyen -- réalisé le long des trajectoires
    couvertes) et le temps de sortie (rappel ou maturité).

    Retourne pnl si interp_gamma est None, sinon (pnl, points_gamma, temps_sortie)
    avec points_gamma = liste de tuples (spot, gamma_$).
    """
    nb_pas = len(trajectoire) - 1
    dt = 1.0 / nb_pas_an
    cash = prix_initial * s0
    position = 0.0
    idx_obs = {int(round(t * nb_pas_an)): t for t in dates_obs}
    points_gamma = []

    for j in range(nb_pas):
        t_courant = j * dt
        spot_j = trajectoire[j]

        if j in idx_obs:
            t_obs = idx_obs[j]
            if spot_j >= barriere_ac * s0:
                payoff = (1.0 + coupon * t_obs) * s0
                cash += position * spot_j
                pnl = cash - payoff
                return (pnl, points_gamma, t_obs) if interp_gamma is not None else pnl

        if j % freq_rebal == 0:
            point = np.array([[t_courant, spot_j]])
            delta_new = float(interp_delta(point)[0])
            if interp_gamma is not None:
                points_gamma.append((spot_j, float(interp_gamma(point)[0])))
            cash -= (delta_new - position) * spot_j
            position = delta_new

        cash *= np.exp(r * dt)

    spot_final = trajectoire[-1]
    cash += position * spot_final
    payoff = s0 if spot_final >= barriere_cap * s0 else spot_final
    pnl = cash - payoff
    return (pnl, points_gamma, dates_obs[-1]) if interp_gamma is not None else pnl
