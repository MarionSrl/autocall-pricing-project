"""Indice à Volatility Target (VT), section III.3.1 du mémoire.

Modèle de volatilité sous-jacent : à 2 régimes (calme / stress), plutôt que
Heston -- choix justifié ci-dessous (spec §3 : "justifie ton choix").

Pourquoi un modèle à 2 régimes plutôt que Heston :
  - L'exigence de la spec est seulement que la vol réalisée ne soit pas
    constante (sinon le mécanisme VT n'a aucun intérêt) : un modèle à
    régimes suffit amplement, avec seulement 4 paramètres interprétables
    (deux niveaux de vol, deux durées moyennes de régime) contre 5 paramètres
    couplés et peu intuitifs pour Heston (kappa, theta, xi, rho, v0).
  - Heston impose de gérer la condition de Feller (2*kappa*theta > xi²) et
    un schéma de discrétisation qui évite les variances négatives (Euler
    plein tronqué, QE de Andersen...) : complexité numérique superflue ici,
    le mémoire n'ayant pas besoin de la dynamique fine de la vol implicite
    que Heston est censé capturer (smile, structure par terme).
  - Le modèle à régimes produit nativement de la persistance (vol
    clustering), ce qui est precisément ce qui compte pour un indice VT à
    fenêtre glissante : c'est la persistance d'un régime de vol qui rend le
    mécanisme pertinent (et son décalage structurel visible), pas la forme
    exacte de la distribution de la vol.
"""

import numpy as np


def simuler_regimes(nb_jours, nb_sim, seed, sigma_bas=0.09, sigma_haut=0.32,
                     duree_moyenne_calme=60, duree_moyenne_stress=20):
    """Chaîne de Markov à 2 états (calme / stress) sur nb_jours pas quotidiens,
    en partant du régime calme. Probabilités de transition dérivées des
    durées moyennes de régime (durée ~ loi géométrique) : p_quitter = 1/durée.

    Retourne sigma, array (nb_sim, nb_jours).
    """
    rng = np.random.default_rng(seed)
    p_calme_vers_stress = 1.0 / duree_moyenne_calme
    p_stress_vers_calme = 1.0 / duree_moyenne_stress

    en_stress = np.zeros((nb_sim, nb_jours), dtype=bool)
    etat_courant = np.zeros(nb_sim, dtype=bool)  # False = calme
    for t in range(nb_jours):
        en_stress[:, t] = etat_courant
        u = rng.random(nb_sim)
        p_bascule = np.where(etat_courant, p_stress_vers_calme, p_calme_vers_stress)
        bascule = u < p_bascule
        etat_courant = np.where(bascule, ~etat_courant, etat_courant)

    return np.where(en_stress, sigma_haut, sigma_bas)


def simuler_indice_sous_jacent(s0, r, q, sigma_path, nb_pas_an, seed):
    """GBM à volatilité variable dans le temps, sigma_path de forme (nb_sim, nb_jours)."""
    nb_sim, nb_jours = sigma_path.shape
    dt = 1.0 / nb_pas_an
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((nb_sim, nb_jours))
    increments = (r - q - 0.5 * sigma_path**2) * dt + sigma_path * np.sqrt(dt) * z
    log_s = np.concatenate([np.zeros((nb_sim, 1)), np.cumsum(increments, axis=1)], axis=1)
    return s0 * np.exp(log_s)


def vol_realisee_glissante(trajectoire, fenetre, nb_pas_an):
    """Vol réalisée annualisée sur une fenêtre glissante de `fenetre` jours de
    rendements. vol[:, t] est calculée sur les rendements [t-fenetre, t-1]
    (connue à la clôture du jour t, donc utilisable sans anticipation pour
    décider l'exposition du jour t vers t+1). NaN tant que l'historique est
    insuffisant (t < fenetre).
    """
    log_rendements = np.diff(np.log(trajectoire), axis=1)
    nb_sim, nb_rendements = log_rendements.shape
    vol = np.full((nb_sim, nb_rendements + 1), np.nan)
    for t in range(fenetre, nb_rendements + 1):
        vol[:, t] = log_rendements[:, t - fenetre:t].std(axis=1, ddof=1) * np.sqrt(nb_pas_an)
    return vol


def construire_indice_vt(trajectoire_sous_jacent, r, sigma_cible, l_max, fenetre, nb_pas_an):
    """Construit l'indice Volatility Target : e_t = min(l_max, sigma_cible / vol_t),
    rebalancement quotidien entre le sous-jacent (fraction e_t) et le cash au
    taux sans risque (fraction 1-e_t), sans coût de transaction (limite
    documentée dans le README). Tant que la fenêtre glissante n'est pas
    disponible (t < fenetre), exposition par défaut 100% (faute d'estimateur).

    Retourne (indice_vt, expositions), chacun de forme (nb_sim, nb_jours+1).
    """
    nb_sim, nb_jours_p1 = trajectoire_sous_jacent.shape
    dt = 1.0 / nb_pas_an
    vol = vol_realisee_glissante(trajectoire_sous_jacent, fenetre, nb_pas_an)

    with np.errstate(divide="ignore", invalid="ignore"):
        expositions = np.minimum(l_max, sigma_cible / vol)
    # vol NaN (historique insuffisant) => 100% par défaut ; vol nulle (trajectoire
    # localement sans variation, ex. scénario scripté plat) => plafond L_max
    expositions = np.where(np.isnan(vol), 1.0, expositions)
    expositions = np.where(vol == 0.0, l_max, expositions)

    rendements_sj = trajectoire_sous_jacent[:, 1:] / trajectoire_sous_jacent[:, :-1] - 1.0
    taux_cash = np.exp(r * dt) - 1.0

    indice_vt = np.empty((nb_sim, nb_jours_p1))
    indice_vt[:, 0] = trajectoire_sous_jacent[:, 0]
    for t in range(nb_jours_p1 - 1):
        e_t = expositions[:, t]
        rendement_vt = e_t * rendements_sj[:, t] + (1.0 - e_t) * taux_cash
        indice_vt[:, t + 1] = indice_vt[:, t] * (1.0 + rendement_vt)

    return indice_vt, expositions


def scenario_v_scripte(s0, baisse_pct, n_avant, n_chute, n_rebond, n_apres):
    """Trajectoire déterministe (pas aléatoire) : plat, chute linéaire en
    log-prix de baisse_pct, rebond symétrique en durée jusqu'au niveau
    initial, puis plat. Retourne un array 1D de longueur
    n_avant+n_chute+n_rebond+n_apres+1.
    """
    log_s0 = np.log(s0)
    log_bas = np.log(s0 * (1.0 - baisse_pct))

    plat_avant = np.full(n_avant, log_s0)
    chute = np.linspace(log_s0, log_bas, n_chute + 1)[1:]
    rebond = np.linspace(log_bas, log_s0, n_rebond + 1)[1:]
    plat_apres = np.full(n_apres, log_s0)

    log_trajectoire = np.concatenate([[log_s0], plat_avant, chute, rebond, plat_apres])
    return np.exp(log_trajectoire)
