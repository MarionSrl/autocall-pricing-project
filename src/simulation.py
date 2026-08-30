"""Simulation Monte Carlo du sous-jacent sous Black-Scholes (portage du notebook,
avec variables antithétiques et seed exposée en paramètre)."""

import numpy as np


def generer_chocs_antithetiques(nb_sim, nb_pas, seed):
    """Tire nb_sim trajectoires de chocs gaussiens i.i.d. N(0,1) par variables
    antithétiques : nb_sim/2 tirages indépendants, complétés par leur opposé.
    nb_sim doit être pair. Ces chocs, partagés en aval par tous les sous-jacents
    comparés (cf. src/indices.py), garantissent une comparaison toutes choses
    égales par ailleurs."""
    if nb_sim % 2 != 0:
        raise ValueError("nb_sim doit être pair pour les variables antithétiques")
    rng = np.random.default_rng(seed)
    demi = nb_sim // 2
    z = rng.standard_normal((demi, nb_pas))
    return np.concatenate([z, -z], axis=0)


def simuler_trajectoires_bs(s0, drift, sigma, T, nb_pas, nb_sim, seed, antithetique=True):
    """Simule nb_sim trajectoires d'un mouvement brownien géométrique
    (dS = drift*S dt + sigma*S dW) sur une grille de nb_pas pas de temps,
    de façon vectorisée (somme cumulative des log-rendements).

    Un seul sous-jacent : utilisé pour la Figure A (PDI / autocall vanille).
    Pour comparer plusieurs indices sur les mêmes trajectoires browniennes
    (Figure B), voir src/indices.py::simuler_indices.
    """
    dt = T / nb_pas
    if antithetique:
        chocs = generer_chocs_antithetiques(nb_sim, nb_pas, seed)
    else:
        rng = np.random.default_rng(seed)
        chocs = rng.standard_normal((nb_sim, nb_pas))
    increments = (drift - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * chocs
    log_spots = np.concatenate([np.zeros((nb_sim, 1)), np.cumsum(increments, axis=1)], axis=1)
    return s0 * np.exp(log_spots)


def simuler_a_dates(s0, drift, sigma, dates, nb_sim, seed, antithetique=True):
    """Simule un GBM échantillonné uniquement aux `dates` données (à partir de
    t=0), pas nécessairement uniformément espacées -- utile quand seules les
    valeurs à des dates d'observation restantes comptent (ex. grille de delta
    de src/delta_hedging.py, où le premier pas dépend du temps courant t).

    `dates` doit être strictement croissant. Retourne un array
    (nb_sim, len(dates)+1), t=0 en première colonne.
    """
    dates = np.asarray(dates, dtype=float)
    dt = np.diff(np.concatenate([[0.0], dates]))
    nb_pas = len(dates)
    if antithetique:
        chocs = generer_chocs_antithetiques(nb_sim, nb_pas, seed)
    else:
        rng = np.random.default_rng(seed)
        chocs = rng.standard_normal((nb_sim, nb_pas))
    increments = (drift - 0.5 * sigma**2) * dt[None, :] + sigma * np.sqrt(dt)[None, :] * chocs
    log_spots = np.concatenate([np.zeros((nb_sim, 1)), np.cumsum(increments, axis=1)], axis=1)
    return s0 * np.exp(log_spots)


def erreur_standard_mc(payoffs):
    """Erreur standard de l'estimateur Monte Carlo (écart-type empirique / sqrt(n))."""
    payoffs = np.asarray(payoffs)
    return payoffs.std(ddof=1) / np.sqrt(payoffs.size)
