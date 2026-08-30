import numpy as np
import pytest

from src.simulation import simuler_trajectoires_bs, simuler_a_dates
from src.delta_hedging import construire_grille_delta_gamma, simuler_couverture

S0, R, Q, SIGMA = 100.0, 0.03, 0.0, 0.20
MATURITE = 5
DATES_OBS = np.arange(1, MATURITE + 1)
BARRIERE_AC, COUPON, BARRIERE_CAP = 1.0, 0.07, 0.60
NB_PAS_AN = 252


def test_simuler_a_dates_egale_simuler_trajectoires_bs_sur_grille_uniforme():
    # dates régulièrement espacées : mêmes chocs (même seed), donc résultat
    # rigoureusement identique à simuler_trajectoires_bs
    dates = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    a = simuler_a_dates(S0, R - Q, SIGMA, dates, 200, seed=7)
    b = simuler_trajectoires_bs(S0, R - Q, SIGMA, MATURITE, len(dates), 200, seed=7)
    np.testing.assert_allclose(a, b, rtol=1e-12)


def test_grille_delta_gamma_finie_et_forme_correcte():
    spots_grid = np.linspace(40.0, 200.0, 6)
    temps_grid = np.linspace(0.0, MATURITE - 0.01, 5)
    delta_grid, gamma_grid, interp_d, interp_g = construire_grille_delta_gamma(
        S0, R, Q, SIGMA, DATES_OBS, BARRIERE_AC, COUPON, BARRIERE_CAP,
        spots_grid, temps_grid, nb_sim_mc=2_000, seed=42,
    )
    assert delta_grid.shape == (5, 6)
    assert gamma_grid.shape == (5, 6)
    assert np.all(np.isfinite(delta_grid))
    assert np.all(np.isfinite(gamma_grid))
    # le delta doit rester dans un ordre de grandeur raisonnable (pas de divergence)
    assert np.all(np.abs(delta_grid) < 50)


def test_simuler_couverture_sans_gamma_retourne_un_scalaire():
    spots_grid = np.linspace(40.0, 200.0, 6)
    temps_grid = np.linspace(0.0, MATURITE - 0.01, 5)
    _, _, interp_d, _ = construire_grille_delta_gamma(
        S0, R, Q, SIGMA, DATES_OBS, BARRIERE_AC, COUPON, BARRIERE_CAP,
        spots_grid, temps_grid, nb_sim_mc=2_000, seed=42,
    )
    trajectoire = simuler_trajectoires_bs(S0, R - Q, SIGMA, MATURITE, NB_PAS_AN * MATURITE, 2, seed=1)[0]
    pnl = simuler_couverture(trajectoire, S0, R, interp_d, DATES_OBS, BARRIERE_AC, COUPON, BARRIERE_CAP,
                              prix_initial=0.98, nb_pas_an=NB_PAS_AN, freq_rebal=5)
    assert isinstance(pnl, float)
    assert np.isfinite(pnl)


def test_simuler_couverture_avec_gamma_retourne_un_triplet():
    spots_grid = np.linspace(40.0, 200.0, 6)
    temps_grid = np.linspace(0.0, MATURITE - 0.01, 5)
    _, _, interp_d, interp_g = construire_grille_delta_gamma(
        S0, R, Q, SIGMA, DATES_OBS, BARRIERE_AC, COUPON, BARRIERE_CAP,
        spots_grid, temps_grid, nb_sim_mc=2_000, seed=42,
    )
    trajectoire = simuler_trajectoires_bs(S0, R - Q, SIGMA, MATURITE, NB_PAS_AN * MATURITE, 2, seed=1)[0]
    pnl, points_gamma, temps_sortie = simuler_couverture(
        trajectoire, S0, R, interp_d, DATES_OBS, BARRIERE_AC, COUPON, BARRIERE_CAP,
        prix_initial=0.98, nb_pas_an=NB_PAS_AN, freq_rebal=5, interp_gamma=interp_g,
    )
    assert np.isfinite(pnl)
    assert len(points_gamma) > 0
    for spot, gamma in points_gamma:
        assert np.isfinite(spot) and np.isfinite(gamma)
    assert 0.0 < temps_sortie <= MATURITE


def test_rappel_immediat_si_spot_franchit_la_barriere_a_t1():
    # trajectoire déterministe (plate à 150, largement au-dessus de la
    # barrière de rappel 100) : sortie garantie dès la première date
    # d'observation (t=1), quel que soit le delta utilisé entre-temps.
    spots_grid = np.linspace(40.0, 200.0, 6)
    temps_grid = np.linspace(0.0, MATURITE - 0.01, 5)
    _, _, interp_d, interp_g = construire_grille_delta_gamma(
        S0, R, Q, SIGMA, DATES_OBS, BARRIERE_AC, COUPON, BARRIERE_CAP,
        spots_grid, temps_grid, nb_sim_mc=2_000, seed=42,
    )
    trajectoire = np.full(NB_PAS_AN * MATURITE + 1, 150.0)
    pnl, points_gamma, temps_sortie = simuler_couverture(
        trajectoire, S0, R, interp_d, DATES_OBS, BARRIERE_AC, COUPON, BARRIERE_CAP,
        prix_initial=0.98, nb_pas_an=NB_PAS_AN, freq_rebal=5, interp_gamma=interp_g,
    )
    assert temps_sortie == pytest.approx(1.0)
    assert np.isfinite(pnl)
