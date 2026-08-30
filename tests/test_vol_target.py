import numpy as np
import pytest

from src.vol_target import (
    simuler_regimes,
    vol_realisee_glissante,
    construire_indice_vt,
    scenario_v_scripte,
)

R, NB_PAS_AN = 0.025, 252


def test_regimes_convergent_vers_probabilite_stationnaire():
    duree_calme, duree_stress = 60, 20
    sigma = simuler_regimes(2000, 3000, seed=123, sigma_bas=0.09, sigma_haut=0.32,
                             duree_moyenne_calme=duree_calme, duree_moyenne_stress=duree_stress)
    frac_stress = (sigma > 0.2).mean()
    # équilibre détaillé à 2 états : pi_calme * p(calme->stress) = pi_stress * p(stress->calme)
    p_stationnaire = (1 / duree_calme) / (1 / duree_calme + 1 / duree_stress)
    assert frac_stress == pytest.approx(p_stationnaire, abs=0.01)


def test_vol_realisee_nulle_sur_trajectoire_deterministe_sans_bruit():
    # rendement quotidien constant => vol réalisée exactement nulle
    n = 60
    trajectoire = 100.0 * np.exp(0.0005 * np.arange(n + 1))[None, :]
    vol = vol_realisee_glissante(trajectoire, fenetre=20, nb_pas_an=NB_PAS_AN)
    assert np.all(np.abs(vol[:, 20:]) < 1e-10)
    assert np.all(np.isnan(vol[:, :20]))


def test_exposition_plafonnee_a_l_max():
    sigma = simuler_regimes(500, 200, seed=7, sigma_bas=0.05, sigma_haut=0.35)
    from src.vol_target import simuler_indice_sous_jacent
    traj = simuler_indice_sous_jacent(100.0, R, 0.03, sigma, NB_PAS_AN, seed=8)
    _, expositions = construire_indice_vt(traj, R, sigma_cible=0.15, l_max=1.5, fenetre=20, nb_pas_an=NB_PAS_AN)
    assert np.nanmax(expositions) <= 1.5 + 1e-9
    assert np.nanmin(expositions) > 0.0


def test_indice_vt_egale_sous_jacent_si_fenetre_indisponible_toute_la_periode():
    sigma = simuler_regimes(30, 50, seed=1, sigma_bas=0.10, sigma_haut=0.30)
    from src.vol_target import simuler_indice_sous_jacent
    traj = simuler_indice_sous_jacent(100.0, R, 0.03, sigma, NB_PAS_AN, seed=2)
    # fenêtre > nb_jours => vol jamais disponible => exposition 100% partout
    vt, expositions = construire_indice_vt(traj, R, sigma_cible=0.15, l_max=1.5, fenetre=40, nb_pas_an=NB_PAS_AN)
    assert np.all(expositions == 1.0)
    np.testing.assert_allclose(vt, traj, rtol=1e-10)


def test_scenario_v_scripte_round_trip_et_creux():
    trajectoire = scenario_v_scripte(100.0, baisse_pct=0.30, n_avant=20, n_chute=20, n_rebond=20, n_apres=40)
    assert trajectoire[0] == pytest.approx(100.0)
    assert trajectoire[20] == pytest.approx(100.0)  # fin du plat avant chute
    assert trajectoire[40] == pytest.approx(70.0, rel=1e-6)  # creux
    assert trajectoire[60] == pytest.approx(100.0, rel=1e-6)  # fin du rebond
    assert trajectoire[-1] == pytest.approx(100.0, rel=1e-6)  # plat après
    assert len(trajectoire) == 20 + 20 + 20 + 40 + 1
