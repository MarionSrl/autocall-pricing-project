"""Construction des 3 sous-jacents comparés (indice classique, décrément en %,
décrément en points) sur des trajectoires browniennes communes, et barrière
d'autocall dégressive.

Convention des drifts risque-neutres (à ne pas mélanger — cf. SPEC §2) :

    - Indice A (« price return », classique)
          drift = r - q            (dividendes détachés, non réinvestis)

    - Indice U (« total return », sous-jacent de B et C)
          drift = r                 (dividendes réinvestis)

    - Indice B (décrément en % continu D, construit sur U)
          B_t = U_t * exp(-D * t)  =>  drift effectif = r - D
          (multiplicateur déterministe appliqué à U : pas besoin de q ici,
          le décrément D remplace le rôle du dividende)

    - Indice C (décrément en points K, construit sur U par récurrence)
          I_t = I_{t-1} * (U_t / U_{t-1}) - K * d(t-1,t) / 365
          path-dépendant : pas de drift constant fermé. Le prélèvement K
          devient proportionnellement plus lourd quand l'indice baisse
          (contrairement à B) : c'est le comportement que la Figure 2
          doit mettre en évidence.

A, U et C sont simulés au pas quotidien (nb_pas_an pas/an) à partir des MÊMES
chocs gaussiens antithétiques, pour que la comparaison soit toutes choses
égales par ailleurs. La grille journalière est nécessaire à la récurrence
de C (path-dépendante), mais n'est pas conservée en mémoire au-delà des
valeurs courantes : seules les valeurs aux dates d'observation sont conservées
en sortie (200 000 trajectoires x 10 ans x 252 pas représenteraient plusieurs
Go par indice si elles étaient stockées intégralement).
"""

import numpy as np

from .simulation import generer_chocs_antithetiques


def simuler_indices(s0, r, q, sigma, D, K, T, nb_pas_an, dates_obs, nb_sim, seed,
                     jours_par_an=365.0):
    """Simule A, U, B, C au pas quotidien et renvoie leurs valeurs aux dates
    d'observation (t=0 inclus en première colonne).

    Retourne un dict {"t_obs": array(n_obs+1), "A":..., "U":..., "B":..., "C":...},
    chaque matrice de forme (nb_sim, n_obs+1).
    """
    dates_obs = np.asarray(dates_obs, dtype=float)
    nb_pas_total = int(round(nb_pas_an * T))
    dt = T / nb_pas_total
    # d(t-1,t)/365 pour un pas quotidien uniforme : dt_jours/jours_par_an = 1/nb_pas_an = dt
    dt_jours = jours_par_an / nb_pas_an
    decrement_par_pas = K * dt_jours / jours_par_an

    chocs = generer_chocs_antithetiques(nb_sim, nb_pas_total, seed)
    racine_dt = np.sqrt(dt)

    idx_obs = {int(round(t * nb_pas_an)): k for k, t in enumerate(dates_obs)}
    n_obs = len(dates_obs)

    A_obs = np.empty((nb_sim, n_obs + 1))
    U_obs = np.empty((nb_sim, n_obs + 1))
    C_obs = np.empty((nb_sim, n_obs + 1))
    A_obs[:, 0] = s0
    U_obs[:, 0] = s0
    C_obs[:, 0] = s0

    log_A = np.zeros(nb_sim)
    log_U = np.zeros(nb_sim)
    U_prev = np.full(nb_sim, s0)
    C_cur = np.full(nb_sim, s0)

    for pas in range(nb_pas_total):
        z = chocs[:, pas]
        log_A += (r - q - 0.5 * sigma**2) * dt + sigma * racine_dt * z
        log_U += (r - 0.5 * sigma**2) * dt + sigma * racine_dt * z
        U_cur = s0 * np.exp(log_U)

        C_cur = C_cur * (U_cur / U_prev) - decrement_par_pas
        U_prev = U_cur

        k = idx_obs.get(pas + 1)
        if k is not None:
            A_obs[:, k + 1] = s0 * np.exp(log_A)
            U_obs[:, k + 1] = U_cur
            C_obs[:, k + 1] = C_cur

    t_obs_complet = np.concatenate([[0.0], dates_obs])
    B_obs = U_obs * np.exp(-D * t_obs_complet)[None, :]

    return {"t_obs": t_obs_complet, "A": A_obs, "U": U_obs, "B": B_obs, "C": C_obs}


def forward_theorique_decrement_points(s0, r, K, T, nb_pas_an):
    """Forward théorique E[C_T] de l'indice à décrément en points.

    U_t/U_{t-1} est indépendant de C_{t-1} (accroissement GBM i.i.d.) et
    d'espérance exp(r*dt), donc E[C_t] = exp(r*dt) * E[C_{t-1}] - K*dt vérifie
    une récurrence linéaire exacte (aucune approximation), de solution :

        E[C_n] = m^n * s0 - K*dt * (m^n - 1) / (m - 1),   m = exp(r*dt)

    avec dt = 1/nb_pas_an, n = nb_pas_an * T.
    """
    n = int(round(nb_pas_an * T))
    dt = T / n
    m = np.exp(r * dt)
    if abs(m - 1.0) < 1e-12:
        return s0 - K * dt * n
    return m**n * s0 - K * dt * (m**n - 1.0) / (m - 1.0)


def barriere_degressive(dates_obs, niveau_initial=1.0, baisse_annuelle=0.05, plancher=0.70):
    """Barrière de rappel dégressive : niveau_initial - baisse_annuelle * t,
    plafonnée à plancher. dates_obs en années (t=1..T)."""
    dates_obs = np.asarray(dates_obs, dtype=float)
    return np.maximum(plancher, niveau_initial - baisse_annuelle * dates_obs)
