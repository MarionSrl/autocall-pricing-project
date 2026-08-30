"""Formule fermée du put down-and-in (PDI) sous Black-Scholes, et vanille associée.

Référence : Bouzoubaa & Osseiran, *Exotic Options and Hybrids*, §10.2.2, cas H < K
(barrière sous le strike) ; formule équivalente dans Hull, *Options, Futures and
Other Derivatives*, chapitre sur les options exotiques (« down-and-in put »).

Convention : H = niveau de la barrière, K = strike, S = spot courant. Valable
uniquement pour H <= K, qui est notre cas d'usage (PDI 100/60 : K=100, H=60).

Le down-and-out est obtenu par parité (put_do = put_vanille - put_di) : c'est
l'usage standard (dériver une des deux jambes par la formule de réflexion, puis
l'autre par parité) plutôt que deux formules indépendantes. La validation
indépendante de la formule de down-and-in vient de la convergence Monte Carlo
(voir tests/test_barrier_options.py), pas de la parité elle-même.
"""

import numpy as np
from scipy.stats import norm

from .simulation import simuler_trajectoires_bs, erreur_standard_mc

N = norm.cdf


def bs_call(S, K, r, q, sigma, T):
    S, K = np.asarray(S, dtype=float), np.asarray(K, dtype=float)
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return S * np.exp(-q * T) * N(d1) - K * np.exp(-r * T) * N(d2)


def bs_put(S, K, r, q, sigma, T):
    S, K = np.asarray(S, dtype=float), np.asarray(K, dtype=float)
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return K * np.exp(-r * T) * N(-d2) - S * np.exp(-q * T) * N(-d1)


def put_down_and_in(S, K, H, r, q, sigma, T):
    """Prix fermé du put down-and-in, cas H <= K.

    La formule de réflexion n'est valable que pour S > H (barrière pas encore
    touchée) : elle est dérivée sous cette hypothèse et ne s'extrapole pas
    correctement à S <= H. Si la barrière est déjà franchie (S <= H), l'option
    est certainement "in" et vaut alors exactement le put vanille — c'est géré
    explicitement ci-dessous plutôt que laissé à la formule.

    Vérifié analytiquement sur ses cas limites (voir tests) : H -> 0 (barrière
    inatteignable) => prix -> 0 ; H -> S⁻ (barrière quasiment déjà touchée)
    => prix -> put vanille.
    """
    S = np.asarray(S, dtype=float)
    if np.any(H > K):
        raise ValueError("put_down_and_in n'est valable que pour H <= K")

    S_domaine = np.where(S > H, S, H * (1.0 + 1e-12))  # évite log(1)=0 exact, écrasé ensuite
    racine_T = np.sqrt(T)
    lam = (r - q + 0.5 * sigma**2) / sigma**2
    x1 = np.log(S_domaine / H) / (sigma * racine_T) + lam * sigma * racine_T
    y = np.log(H**2 / (S_domaine * K)) / (sigma * racine_T) + lam * sigma * racine_T
    y1 = np.log(H / S_domaine) / (sigma * racine_T) + lam * sigma * racine_T

    terme1 = -S_domaine * np.exp(-q * T) * N(-x1) + K * np.exp(-r * T) * N(-x1 + sigma * racine_T)
    terme2 = S_domaine * np.exp(-q * T) * (H / S_domaine) ** (2 * lam) * (N(y) - N(y1))
    terme3 = -K * np.exp(-r * T) * (H / S_domaine) ** (2 * lam - 2) * (
        N(y - sigma * racine_T) - N(y1 - sigma * racine_T)
    )
    prix_si_pas_touchee = terme1 + terme2 + terme3
    prix_si_deja_touchee = bs_put(S, K, r, q, sigma, T)
    return np.where(S > H, prix_si_pas_touchee, prix_si_deja_touchee)


def put_down_and_out(S, K, H, r, q, sigma, T):
    """Par parité : down-and-out = vanille - down-and-in (cas H <= K)."""
    return bs_put(S, K, r, q, sigma, T) - put_down_and_in(S, K, H, r, q, sigma, T)


def pdi_grecques(S, K, H, r, q, sigma, T, h_spot_rel=1e-3, h_vol=1e-3):
    """Prix, delta, vega et vanna du PDI par différences finies centrées sur la
    formule fermée (vanna = dérivée croisée ∂²P/∂S∂σ).

    Convention vega/vanna (à ne pas casser) : sigma est en décimal (0.18 =
    18 %). `h_vol` n'est qu'un pas de différenciation numérique (petit, pour
    la précision de la dérivée) -- vega et vanna sont ensuite mis à l'échelle
    par 0.01 (= 1 point de vol) pour représenter la variation de prix pour un
    déplacement de 1 point de vol (convention desk), et non la dérivée brute
    ∂P/∂σ extrapolée sur un déplacement complet de sigma de 0 à 1 (100
    points), qui serait 100x trop grande."""
    S = np.asarray(S, dtype=float)
    hS = S * h_spot_rel
    hv = h_vol

    prix = put_down_and_in(S, K, H, r, q, sigma, T)
    delta = (
        put_down_and_in(S + hS, K, H, r, q, sigma, T) - put_down_and_in(S - hS, K, H, r, q, sigma, T)
    ) / (2 * hS)
    vega = 0.01 * (
        put_down_and_in(S, K, H, r, q, sigma + hv, T) - put_down_and_in(S, K, H, r, q, sigma - hv, T)
    ) / (2 * hv)
    vanna = 0.01 * (
        put_down_and_in(S + hS, K, H, r, q, sigma + hv, T)
        - put_down_and_in(S + hS, K, H, r, q, sigma - hv, T)
        - put_down_and_in(S - hS, K, H, r, q, sigma + hv, T)
        + put_down_and_in(S - hS, K, H, r, q, sigma - hv, T)
    ) / (4 * hS * hv)

    return {"prix": prix, "delta": delta, "vega": vega, "vanna": vanna}


def mc_put_down_and_in(S0, K, H, r, q, sigma, T, nb_sim, seed, nb_pas_an=252):
    """Prix Monte Carlo du put down-and-in à barrière CONTINUE, pour valider la
    formule fermée par une méthode indépendante.

    Un simple test « min(trajectoire quotidienne) <= H » sous-estime fortement
    la vraie probabilité de franchissement continu (biais de discrétisation
    documenté dans le README, cf. Broadie-Glasserman-Kou) : avec un monitoring
    quotidien seul, l'écart à la formule fermée dépasse largement 0.5%, même
    à 200k trajectoires. On utilise donc la probabilité exacte (pont brownien)
    qu'un mouvement brownien géométrique ait touché la barrière entre deux
    dates de simulation consécutives, sachant les deux extrémités simulées :

        P(touché sur [t_i, t_i+1] | S_i, S_i+1) = exp(-2 ln(S_i/H) ln(S_i+1/H) / (sigma^2 dt))

    (Karatzas & Shreve). Cette probabilité sert de poids continu (Rao-
    Blackwellisation) plutôt qu'un indicateur 0/1 : estimateur non biaisé et à
    variance réduite, qui approxime la barrière continue même avec un nombre
    modéré de pas de simulation.
    """
    nb_pas = int(round(nb_pas_an * T))
    dt = T / nb_pas
    trajectoires = simuler_trajectoires_bs(S0, r - q, sigma, T, nb_pas, nb_sim, seed)

    S_gauche = trajectoires[:, :-1]
    S_droite = trajectoires[:, 1:]
    log_dist_gauche = np.log(np.maximum(S_gauche, H) / H)
    log_dist_droite = np.log(np.maximum(S_droite, H) / H)
    p_touche_intervalle = np.exp(-2.0 * log_dist_gauche * log_dist_droite / (sigma**2 * dt))
    p_touche_intervalle = np.where((S_gauche <= H) | (S_droite <= H), 1.0, p_touche_intervalle)

    p_touche = 1.0 - np.prod(1.0 - p_touche_intervalle, axis=1)
    payoffs = np.exp(-r * T) * np.maximum(K - trajectoires[:, -1], 0.0) * p_touche
    return payoffs.mean(), erreur_standard_mc(payoffs)
