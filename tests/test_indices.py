import numpy as np
import pytest

from src.indices import (
    simuler_indices,
    forward_theorique_decrement_points,
    barriere_degressive,
    indice_decrement_pourcentage,
)

S0, R, Q, SIGMA, D, K = 100.0, 0.025, 0.03, 0.18, 0.05, 5.0
T = 10
DATES_OBS = np.arange(1, T + 1)


def _simuler(nb_sim=40_000, nb_pas_an=12, K_local=K, seed=123):
    return simuler_indices(S0, R, Q, SIGMA, D, K_local, T, nb_pas_an, DATES_OBS, nb_sim, seed)


def test_forward_indice_A_price_return():
    res = _simuler()
    A_T = res["A"][:, -1]
    forward_theorique = S0 * np.exp((R - Q) * T)
    erreur_std = A_T.std(ddof=1) / np.sqrt(A_T.size)
    assert abs(A_T.mean() - forward_theorique) < 5 * erreur_std


def test_forward_indice_U_total_return():
    res = _simuler()
    U_T = res["U"][:, -1]
    forward_theorique = S0 * np.exp(R * T)
    erreur_std = U_T.std(ddof=1) / np.sqrt(U_T.size)
    assert abs(U_T.mean() - forward_theorique) < 5 * erreur_std


def test_forward_indice_B_decrement_pourcentage():
    res = _simuler()
    B_T = res["B"][:, -1]
    forward_theorique = S0 * np.exp((R - D) * T)
    erreur_std = B_T.std(ddof=1) / np.sqrt(B_T.size)
    assert abs(B_T.mean() - forward_theorique) < 5 * erreur_std


def test_forward_indice_C_decrement_points_formule_exacte():
    res = _simuler(nb_pas_an=52)
    C_T = res["C"][:, -1]
    forward_theorique = forward_theorique_decrement_points(S0, R, K, T, nb_pas_an=52)
    erreur_std = C_T.std(ddof=1) / np.sqrt(C_T.size)
    assert abs(C_T.mean() - forward_theorique) < 5 * erreur_std


def test_decrement_points_K_zero_egale_indice_total_return():
    res = _simuler(nb_sim=2_000, nb_pas_an=4, K_local=0.0, seed=7)
    np.testing.assert_allclose(res["C"], res["U"], rtol=1e-10, atol=1e-8)


def test_barriere_degressive_decroissante_et_plafonnee():
    b = barriere_degressive(DATES_OBS, niveau_initial=1.0, baisse_annuelle=0.05, plancher=0.70)
    assert b[0] == pytest.approx(0.95)
    assert b[-1] == pytest.approx(0.70)
    assert np.all(np.diff(b) <= 0)
    assert np.all(b >= 0.70)


def test_decrement_pourcentage_egal_dividende_redonne_indice_classique():
    # Cas de contrôle B' de la Figure B : quand D = q, l'indice à décrément en %
    # est identique, trajectoire par trajectoire, à l'indice classique A (même
    # construction : mêmes chocs, même drift effectif r - q). Isole l'effet du
    # mécanisme de décrément de l'effet "D > q".
    res = _simuler(nb_sim=2_000, nb_pas_an=12)
    B_prime = indice_decrement_pourcentage(res["U"], res["t_obs"], D=Q)
    np.testing.assert_allclose(B_prime, res["A"], rtol=1e-9, atol=1e-9)


def test_memes_chocs_partages_entre_A_et_U():
    # A et U doivent être corrélés à 1 en log-rendement (mêmes chocs, drift différent)
    res = _simuler(nb_sim=2_000, nb_pas_an=12)
    log_rendement_A = np.diff(np.log(res["A"]), axis=1)
    log_rendement_U = np.diff(np.log(res["U"]), axis=1)
    difference = log_rendement_A - log_rendement_U
    # la différence de drift (r-q) - r = -q est déterministe : la variance de la différence
    # doit être quasi nulle si les mêmes chocs ont bien été utilisés
    assert difference.std() < 1e-8
