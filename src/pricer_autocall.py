"""Pricer Monte Carlo de l'autocall (portage de pricer_autocall_mc du notebook),
adapté pour consommer directement une matrice de spots déjà extraits aux dates
d'observation (produite par src/simulation.py ou src/indices.py), et pour
supporter une barrière de rappel dégressive.

Convention du produit (cf. SPEC §1, validée) :
    - Coupon conditionnel « à mémoire » : au rappel à la date t_obs, on verse
      (1 + coupon * t_obs), c'est-à-dire tous les coupons annuels cumulés
      depuis l'origine (effet mémoire).
    - Si le produit va à maturité sans jamais être rappelé, AUCUN coupon
      n'est versé : seul le capital (protégé ou non) est remboursé. C'est
      une conséquence directe de la convention "Athena" retenue : la seule
      barrière du produit sert à la fois de trigger de rappel et de trigger
      de coupon (pas de barrière coupon indépendante). Voir le README pour
      l'interprétation de cette convention vis-à-vis des indices à décrément.
    - PDI (barrière 60% par défaut) observé uniquement à maturité
      (convention européenne).
"""

from dataclasses import dataclass

import numpy as np


@dataclass
class ResultatAutocall:
    prix: float
    erreur_std: float
    payoffs: np.ndarray
    dates_rappel: np.ndarray   # NaN si jamais rappelé
    pdi_actif: np.ndarray      # bool ; valable seulement pour les trajectoires allées à maturité
    spot_final: np.ndarray


def pricer_autocall(spots_obs, s0, r, dates_obs, barriere_ac, coupon, barriere_cap):
    """
    spots_obs : array (nb_sim, n_obs), valeurs du sous-jacent aux dates
        d'observation dates_obs (sans t=0).
    barriere_ac : scalaire (barrière plate) ou array de taille n_obs
        (barrière dégressive), en fraction de s0.
    """
    dates_obs = np.asarray(dates_obs, dtype=float)
    nb_sim, n_obs = spots_obs.shape
    barriere_ac = np.broadcast_to(np.atleast_1d(barriere_ac).astype(float), (n_obs,))

    payoffs = np.zeros(nb_sim)
    dates_rappel = np.full(nb_sim, np.nan)
    vivantes = np.ones(nb_sim, dtype=bool)

    for k, t_obs in enumerate(dates_obs):
        spots = spots_obs[vivantes, k]
        ac_mask = spots >= barriere_ac[k] * s0
        idx_viv = np.where(vivantes)[0]
        idx_ac = idx_viv[ac_mask]

        payoffs[idx_ac] = (1.0 + coupon * t_obs) * np.exp(-r * t_obs)
        dates_rappel[idx_ac] = t_obs
        vivantes[idx_ac] = False

    spot_final = spots_obs[:, -1]
    pdi_actif = np.zeros(nb_sim, dtype=bool)

    if vivantes.any():
        idx_viv = np.where(vivantes)[0]
        s_fin = spot_final[idx_viv]
        disc = np.exp(-r * dates_obs[-1])
        protege = s_fin >= barriere_cap * s0
        payoffs[idx_viv[protege]] = 1.0 * disc
        payoffs[idx_viv[~protege]] = (s_fin[~protege] / s0) * disc
        pdi_actif[idx_viv[~protege]] = True

    prix = payoffs.mean()
    erreur_std = payoffs.std(ddof=1) / np.sqrt(nb_sim)

    return ResultatAutocall(prix, erreur_std, payoffs, dates_rappel, pdi_actif, spot_final)


def decomposer_legs_pdi(resultat, s0, r, maturite):
    """Décompose le payoff total en deux jambes (Figure 1, panneau b) :

        payoff_total = jambe_autocall_sans_pdi - jambe_pdi

    où jambe_autocall_sans_pdi est le même produit mais avec un capital
    toujours intégralement protégé à maturité (équivalent à barriere_cap=0),
    et jambe_pdi est le manque à gagner actualisé (1 - S_T/s0), non nul
    uniquement si le produit est allé à maturité avec le PDI actif. Ce n'est
    pas un vrai put down-and-in (le PDI du produit n'est observé qu'à
    maturité, cf. README) : c'est un payoff terminal conditionnel au fait de
    ne pas avoir été rappelé plus tôt.

    Retourne (payoffs_jambe_sans_pdi, payoffs_jambe_pdi), vecteurs (nb_sim,).
    """
    disc = np.exp(-r * maturite)
    payoffs_jambe_pdi = np.where(
        resultat.pdi_actif, disc * (1.0 - resultat.spot_final / s0), 0.0
    )
    payoffs_jambe_sans_pdi = resultat.payoffs + payoffs_jambe_pdi
    return payoffs_jambe_sans_pdi, payoffs_jambe_pdi
