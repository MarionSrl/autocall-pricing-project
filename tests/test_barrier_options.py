import numpy as np
import pytest

from src.barrier_options import (
    bs_call,
    bs_put,
    put_down_and_in,
    put_down_and_out,
    mc_put_down_and_in,
)

S0, K, H = 100.0, 100.0, 60.0
R, Q, SIGMA, T = 0.025, 0.03, 0.18, 1.0


def test_parite_put_call():
    call = bs_call(S0, K, R, Q, SIGMA, T)
    put = bs_put(S0, K, R, Q, SIGMA, T)
    parite = S0 * np.exp(-Q * T) - K * np.exp(-R * T)
    assert (call - put) == pytest.approx(parite, rel=1e-9)


def test_ki_ko_egale_vanille():
    spots = np.linspace(61.0, 130.0, 25)  # H<S pour rester dans le domaine du PDI
    di = put_down_and_in(spots, K, H, R, Q, SIGMA, T)
    do = put_down_and_out(spots, K, H, R, Q, SIGMA, T)
    vanille = bs_put(spots, K, R, Q, SIGMA, T)
    np.testing.assert_allclose(di + do, vanille, rtol=1e-10, atol=1e-10)


def test_limite_barriere_inatteignable_prix_nul():
    # H -> 0 : la barrière ne peut quasiment jamais être touchée, le PDI -> 0
    prix = put_down_and_in(S0, K, 1e-6, R, Q, SIGMA, T)
    assert prix < 1e-6


def test_prix_egale_vanille_quand_barriere_deja_franchie():
    # S <= H : la barrière est déjà touchée, l'option est certainement "in"
    spots_sous_barriere = np.array([30.0, 45.0, 55.0, 59.9, 60.0])
    prix_di = put_down_and_in(spots_sous_barriere, K, H, R, Q, SIGMA, T)
    prix_vanille = bs_put(spots_sous_barriere, K, R, Q, SIGMA, T)
    np.testing.assert_allclose(prix_di, prix_vanille, rtol=1e-9)


def test_limite_barriere_egale_spot_prix_vanille():
    # H = S : la barrière est déjà touchée, le PDI vaut le put vanille
    prix_di = put_down_and_in(S0, K, S0, R, Q, SIGMA, T)
    prix_vanille = bs_put(S0, K, R, Q, SIGMA, T)
    assert prix_di == pytest.approx(prix_vanille, rel=1e-8)


def test_convergence_mc_vers_formule_fermee():
    # Spot proche de la barrière (70, entre H=60 et K=100) : le PDI y est
    # suffisamment "actif" (probabilité de franchissement non négligeable)
    # pour que la comparaison à la formule fermée soit statistiquement
    # significative avec 200k trajectoires (loin de la barrière, S=100, le
    # franchissement est un évènement rare et le test devient peu informatif).
    spot_test = 70.0
    prix_ferme = put_down_and_in(spot_test, K, H, R, Q, SIGMA, T)
    prix_mc, erreur_std = mc_put_down_and_in(
        spot_test, K, H, R, Q, SIGMA, T, nb_sim=200_000, seed=2026
    )
    ecart_relatif = abs(prix_mc - prix_ferme) / prix_ferme
    assert ecart_relatif < 0.005
    # cohérence supplémentaire : l'écart doit rester dans un ordre de grandeur
    # raisonnable par rapport au bruit MC (quelques erreurs standard)
    assert abs(prix_mc - prix_ferme) < 8 * erreur_std
