import numpy as np
import pytest

from src.indices import simuler_indices, barriere_degressive, indice_decrement_pourcentage
from src.pricer_autocall import pricer_autocall
from src.coupon_solver import resoudre_coupon_pair

S0, R, Q, SIGMA, D, K = 100.0, 0.025, 0.03, 0.18, 0.05, 5.0
T = 10
DATES_OBS = np.arange(1, T + 1)
BARRIERE_CAP = 0.60


def _indices(nb_sim=20_000, nb_pas_an=52, seed=99):
    return simuler_indices(S0, R, Q, SIGMA, D, K, T, nb_pas_an, DATES_OBS, nb_sim, seed)


def test_prix_croissant_avec_le_coupon():
    res = _indices()
    spots_A = res["A"][:, 1:]
    prix_bas = pricer_autocall(spots_A, S0, R, DATES_OBS, 1.0, coupon=0.02, barriere_cap=BARRIERE_CAP).prix
    prix_haut = pricer_autocall(spots_A, S0, R, DATES_OBS, 1.0, coupon=0.10, barriere_cap=BARRIERE_CAP).prix
    assert prix_haut > prix_bas


def test_prix_decroissant_avec_barriere_autocall_plus_haute():
    res = _indices()
    spots_A = res["A"][:, 1:]
    prix_barriere_basse = pricer_autocall(spots_A, S0, R, DATES_OBS, 0.90, coupon=0.06, barriere_cap=BARRIERE_CAP).prix
    prix_barriere_haute = pricer_autocall(spots_A, S0, R, DATES_OBS, 1.10, coupon=0.06, barriere_cap=BARRIERE_CAP).prix
    assert prix_barriere_haute < prix_barriere_basse


def test_barriere_degressive_facilite_le_rappel():
    res = _indices()
    spots_A = res["A"][:, 1:]
    barriere_plate = np.full(T, 1.0)
    barriere_deg = barriere_degressive(DATES_OBS)
    r_plate = pricer_autocall(spots_A, S0, R, DATES_OBS, barriere_plate, coupon=0.06, barriere_cap=BARRIERE_CAP)
    r_deg = pricer_autocall(spots_A, S0, R, DATES_OBS, barriere_deg, coupon=0.06, barriere_cap=BARRIERE_CAP)
    proba_maturite_plate = np.isnan(r_plate.dates_rappel).mean()
    proba_maturite_deg = np.isnan(r_deg.dates_rappel).mean()
    assert proba_maturite_deg < proba_maturite_plate


def test_coupon_solver_converge_au_pair():
    res = _indices(nb_sim=40_000)
    spots_A = res["A"][:, 1:]
    coupon_pair, resultat = resoudre_coupon_pair(spots_A, S0, R, DATES_OBS, 1.0, BARRIERE_CAP, nominal=1.0)
    assert 0.0 < coupon_pair < 0.20
    assert abs(resultat.prix - 1.0) < 5 * resultat.erreur_std


def test_coupon_pair_identique_entre_A_et_B_prime_cas_de_controle():
    # Cas de contrôle B' (D=q) : même sous-jacent qu'A trajectoire par trajectoire,
    # donc même coupon au pair (aux résidus numériques du solveur près, pas un
    # écart Monte Carlo puisque ce sont les mêmes trajectoires).
    res = _indices(nb_sim=40_000)
    spots_A = res["A"][:, 1:]
    B_prime_obs = indice_decrement_pourcentage(res["U"], res["t_obs"], D=Q)[:, 1:]

    coupon_A, _ = resoudre_coupon_pair(spots_A, S0, R, DATES_OBS, 1.0, BARRIERE_CAP)
    coupon_B_prime, _ = resoudre_coupon_pair(B_prime_obs, S0, R, DATES_OBS, 1.0, BARRIERE_CAP)

    assert coupon_A == pytest.approx(coupon_B_prime, abs=1e-6)


def test_pdi_actif_seulement_a_maturite_sous_la_barriere():
    res = _indices()
    spots_A = res["A"][:, 1:]
    resultat = pricer_autocall(spots_A, S0, R, DATES_OBS, 1.0, coupon=0.06, barriere_cap=BARRIERE_CAP)
    rappelees = ~np.isnan(resultat.dates_rappel)
    assert not resultat.pdi_actif[rappelees].any()
    non_rappelees = ~rappelees
    assert np.array_equal(
        resultat.pdi_actif[non_rappelees],
        resultat.spot_final[non_rappelees] < BARRIERE_CAP * S0,
    )
