import numpy as np
import pytest

from src.barrier_options import (
    bs_call,
    bs_put,
    put_down_and_in,
    put_down_and_out,
    mc_put_down_and_in,
    pdi_grecques,
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


# Échelle du vega/vanna (cf. PR #13 : facteur 100 manquant, non couvert par un
# test avant cette correction -- pdi_grecques rapporte vega/vanna "pour 1
# point de vol", pas la dérivée brute dP/dsigma). Les deux tests suivants
# re-pricent indépendamment via put_down_and_in avec un bump symétrique de
# +/-0.5 point (span total = 1 point, centré sur SIGMA), sans passer par le
# code de pdi_grecques -- c'est ce contrôle qui aurait immédiatement détecté
# le bug (vega_formule aurait été ~100x plus grand que la variation de prix
# réellement observée pour un déplacement de 1 point de vol). Un bump à un
# seul côté (sigma -> sigma+0.01) ne convient pas ici : la convexité du PDI
# en sigma (vomma) le fait diverger de plusieurs % de la pente locale, ce qui
# n'a rien à voir avec le bug corrigé.
SPOTS_VEGA_TEST = np.array([65.0, 75.0, 90.0, 100.0, 110.0])


def test_vega_pdi_coherent_avec_repricing_a_plus_1pt_de_vol():
    vega_formule = pdi_grecques(SPOTS_VEGA_TEST, K, H, R, Q, SIGMA, T)["vega"]
    prix_up = put_down_and_in(SPOTS_VEGA_TEST, K, H, R, Q, SIGMA + 0.005, T)
    prix_down = put_down_and_in(SPOTS_VEGA_TEST, K, H, R, Q, SIGMA - 0.005, T)
    vega_repriced = prix_up - prix_down
    np.testing.assert_allclose(vega_formule, vega_repriced, rtol=0.01)


def test_vanna_pdi_coherent_avec_repricing_a_plus_1pt_de_vol():
    vanna_formule = pdi_grecques(SPOTS_VEGA_TEST, K, H, R, Q, SIGMA, T)["vanna"]
    hS = SPOTS_VEGA_TEST * 1e-3  # même h_spot_rel que le défaut de pdi_grecques
    delta_a_vol_haut = (
        put_down_and_in(SPOTS_VEGA_TEST + hS, K, H, R, Q, SIGMA + 0.005, T)
        - put_down_and_in(SPOTS_VEGA_TEST - hS, K, H, R, Q, SIGMA + 0.005, T)
    ) / (2 * hS)
    delta_a_vol_bas = (
        put_down_and_in(SPOTS_VEGA_TEST + hS, K, H, R, Q, SIGMA - 0.005, T)
        - put_down_and_in(SPOTS_VEGA_TEST - hS, K, H, R, Q, SIGMA - 0.005, T)
    ) / (2 * hS)
    vanna_repriced = delta_a_vol_haut - delta_a_vol_bas
    np.testing.assert_allclose(vanna_formule, vanna_repriced, rtol=0.01)


def test_vega_pdi_ordre_de_grandeur_inferieur_au_prix():
    # Un point de vol ne peut pas déplacer le prix du PDI plus que le prix
    # lui-même -- c'est justement l'incohérence qui a mis la puce à l'oreille
    # sur le bug de la PR #13 (un PDI à 1.23 affichait un vega de 39.15).
    # Restreint à spot<=125 : au-delà, le prix devient microscopique
    # (<0.003, put profondément OTM) et le ratio vega/prix cesse d'être
    # informatif (queue de distribution, pas un signe de bug).
    spots = np.linspace(40.0, 125.0, 341)
    grecques = pdi_grecques(spots, K, H, R, Q, SIGMA, T)
    assert np.all(np.abs(grecques["vega"]) < grecques["prix"])


def test_vanna_pdi_ordre_de_grandeur_inferieur_au_delta():
    # Même contrôle d'ordre de grandeur, appliqué à vanna = d(delta)/d(1pt de
    # vol) : borné par le delta lui-même sur le même domaine restreint.
    spots = np.linspace(40.0, 125.0, 341)
    grecques = pdi_grecques(spots, K, H, R, Q, SIGMA, T)
    assert np.all(np.abs(grecques["vanna"]) < np.abs(grecques["delta"]))
