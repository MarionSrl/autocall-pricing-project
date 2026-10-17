"""Tests pour la Figure E (extension : impact d'un indice Volatility Target
sur le coupon au pair, à forward contrôlé, seul puis combiné à un décrément).

Échelles réduites par rapport au script de figure (200 000 trajectoires) pour
rester rapides en suite de tests, tout en gardant assez de trajectoires pour
que les propriétés statistiques testées (martingale, vol réalisée, monotonie)
soient significatives au-delà du bruit Monte Carlo.
"""

import numpy as np
import pytest

from src.vol_target import simuler_regimes, simuler_indice_sous_jacent, construire_indice_vt
from src.indices import indice_decrement_pourcentage, appliquer_decrement_points
from src.coupon_solver import resoudre_coupon_pair

R, NB_PAS_AN = 0.025, 252
SIGMA_BAS, SIGMA_HAUT = 0.09, 0.32
DUREE_CALME, DUREE_STRESS = 60, 20


def test_vol_target_levier_force_a_1_reproduit_indice_total_return():
    # l_max=1.0 et sigma_cible très élevée => min(l_max, sigma_cible/vol) = 1.0
    # partout (y compris pendant les 20 premiers jours sans historique, où la
    # convention par défaut est déjà 100%) : la construction se réduit à
    # "100% investi dans le sous-jacent, jamais en cash" = le sous-jacent lui-même.
    sigma = simuler_regimes(500, 200, seed=11, sigma_bas=0.10, sigma_haut=0.30)
    traj = simuler_indice_sous_jacent(100.0, R, 0.0, sigma, NB_PAS_AN, seed=12)
    vt, expositions = construire_indice_vt(
        traj, R, sigma_cible=10.0, l_max=1.0, fenetre=20, nb_pas_an=NB_PAS_AN
    )
    assert np.all(expositions == 1.0)
    np.testing.assert_allclose(vt, traj, rtol=1e-10)


def test_indice_vt_martingale_sous_q():
    # Jambe risquée = indice total return (q=0, drift r) : driftless une fois
    # actualisée à r. Le Vol Target rebalance à poids prévisibles (connus à
    # t-1, cf. vol_realisee_glissante) entre cette jambe et le cash (aussi
    # driftless une fois actualisé) : la valeur actualisée de l'indice VT
    # doit donc rester une martingale sous Q, en particulier
    # E[exp(-rT) * VT_T] = VT_0 = S0, à l'erreur Monte Carlo près. C'est cette
    # propriété -- pas un "effet du cash en période de stress" -- qui explique
    # le forward élevé (~S0*exp(rT)) d'un indice Vol Target sans décrément :
    # voir la docstring de scripts/figE_vol_target_decrement.py.
    nb_sim, T = 40_000, 2
    nb_jours = NB_PAS_AN * T
    sigma = simuler_regimes(nb_jours, nb_sim, seed=21, sigma_bas=SIGMA_BAS, sigma_haut=SIGMA_HAUT,
                             duree_moyenne_calme=DUREE_CALME, duree_moyenne_stress=DUREE_STRESS)
    traj = simuler_indice_sous_jacent(100.0, R, 0.0, sigma, NB_PAS_AN, seed=22)
    vt, _ = construire_indice_vt(traj, R, sigma_cible=0.15, l_max=1.5, fenetre=20, nb_pas_an=NB_PAS_AN)

    valeur_actualisee = vt[:, -1] * np.exp(-R * T)
    moyenne = valeur_actualisee.mean()
    erreur_std = valeur_actualisee.std(ddof=1) / np.sqrt(nb_sim)

    assert moyenne == pytest.approx(100.0, abs=4 * erreur_std)


def test_vol_target_vol_realisee_proche_de_la_cible():
    nb_sim, T = 20_000, 2
    sigma_cible = 0.15
    nb_jours = NB_PAS_AN * T
    sigma = simuler_regimes(nb_jours, nb_sim, seed=31, sigma_bas=SIGMA_BAS, sigma_haut=SIGMA_HAUT,
                             duree_moyenne_calme=DUREE_CALME, duree_moyenne_stress=DUREE_STRESS)
    traj = simuler_indice_sous_jacent(100.0, R, 0.0, sigma, NB_PAS_AN, seed=32)
    vt, _ = construire_indice_vt(traj, R, sigma_cible, l_max=1.5, fenetre=20, nb_pas_an=NB_PAS_AN)

    log_rendements = np.diff(np.log(vt), axis=1)
    vol_par_trajectoire = log_rendements.std(axis=1, ddof=1) * np.sqrt(NB_PAS_AN)

    # Tolérance large (3 pts) : la Figure D documente déjà un biais structurel
    # (~1 pt, moyenne au-dessus de la cible) lié au plafond L_max et au retard
    # de la fenêtre glissante -- ce test vérifie l'ordre de grandeur, pas une
    # égalité exacte.
    assert vol_par_trajectoire.mean() == pytest.approx(sigma_cible, abs=0.03)


def test_coupon_pair_monotone_en_decrement():
    # Même indice Vol Target (mêmes trajectoires), décrément % croissant :
    # le coupon au pair doit augmenter pour compenser le prélèvement de plus
    # en plus lourd sur l'indice.
    nb_sim, maturite = 40_000, 10
    dates_obs = np.arange(1, maturite + 1)
    nb_jours = NB_PAS_AN * maturite
    sigma = simuler_regimes(nb_jours, nb_sim, seed=41, sigma_bas=SIGMA_BAS, sigma_haut=SIGMA_HAUT,
                             duree_moyenne_calme=DUREE_CALME, duree_moyenne_stress=DUREE_STRESS)
    traj = simuler_indice_sous_jacent(100.0, R, 0.0, sigma, NB_PAS_AN, seed=42)
    vt, _ = construire_indice_vt(traj, R, sigma_cible=0.15, l_max=1.5, fenetre=20, nb_pas_an=NB_PAS_AN)

    indices_obs = [int(round(t * NB_PAS_AN)) for t in dates_obs]
    t_quotidien = np.arange(vt.shape[1]) / NB_PAS_AN

    coupons = []
    for D in (0.0, 0.03, 0.06):
        indice_decr = indice_decrement_pourcentage(vt, t_quotidien, D)
        spots_obs = indice_decr[:, indices_obs]
        coupon, _ = resoudre_coupon_pair(spots_obs, 100.0, R, dates_obs, 1.0, 0.60)
        coupons.append(coupon)

    assert coupons[0] < coupons[1] < coupons[2]


def test_coupon_pair_identique_nu_decrement3_vs_price_return():
    # Cas de contrôle, généralisation à la vol à 2 régimes du cas B' de la
    # Figure B : l'indice nu construit en Figure E (jambe total return
    # décrémentée à D=3%=q) doit être identique, TRAJECTOIRE PAR TRAJECTOIRE,
    # à l'indice "price return" simulé directement avec dividende q=3%, dès
    # lors que les deux partagent la même seed de chocs et le même chemin de
    # volatilité -- indice_decrement_pourcentage(U, D=q) == A, que sigma soit
    # constante (déjà vérifié par test_indices.py) ou stochastique (ici).
    # Même coupon au pair en conséquence (pas un hasard Monte Carlo : mêmes
    # trajectoires exactement).
    nb_sim, maturite = 40_000, 10
    dates_obs = np.arange(1, maturite + 1)
    nb_jours = NB_PAS_AN * maturite
    sigma = simuler_regimes(nb_jours, nb_sim, seed=51, sigma_bas=SIGMA_BAS, sigma_haut=SIGMA_HAUT,
                             duree_moyenne_calme=DUREE_CALME, duree_moyenne_stress=DUREE_STRESS)
    traj_tr = simuler_indice_sous_jacent(100.0, R, 0.0, sigma, NB_PAS_AN, seed=52)
    traj_price_return = simuler_indice_sous_jacent(100.0, R, 0.03, sigma, NB_PAS_AN, seed=52)

    t_quotidien = np.arange(traj_tr.shape[1]) / NB_PAS_AN
    nu_decr3 = indice_decrement_pourcentage(traj_tr, t_quotidien, 0.03)

    np.testing.assert_allclose(nu_decr3, traj_price_return, rtol=1e-9, atol=1e-9)

    indices_obs = [int(round(t * NB_PAS_AN)) for t in dates_obs]
    coupon_decr, _ = resoudre_coupon_pair(nu_decr3[:, indices_obs], 100.0, R, dates_obs, 1.0, 0.60)
    coupon_direct, _ = resoudre_coupon_pair(traj_price_return[:, indices_obs], 100.0, R, dates_obs, 1.0, 0.60)
    assert coupon_decr == pytest.approx(coupon_direct, abs=1e-6)


def test_appliquer_decrement_points_recurrence_correcte():
    # Trajectoire quotidienne déterministe (pas de Monte Carlo) : la
    # récurrence I_t = max(I_{t-1}*(X_t/X_{t-1}) - K*dt_jours/jours_par_an, 0)
    # est vérifiable à la main, indépendamment de tout appel à simuler_indices.
    # K choisi modéré ici : le plancher n'est jamais atteint (cf. le test
    # dédié ci-dessous pour le cas où il l'est).
    traj = np.array([[100.0, 101.0, 99.0, 100.5]])
    nb_pas_an, jours_par_an = 365.0, 365.0  # dt_jours = 1 jour exactement
    K = 36.5  # decrement_par_pas = 36.5 * 1 / 365 = 0.1 / jour

    decr = appliquer_decrement_points(traj, K, nb_pas_an, jours_par_an=jours_par_an)

    attendu = [100.0]
    valeur = 100.0
    for t in range(1, traj.shape[1]):
        ratio = traj[0, t] / traj[0, t - 1]
        valeur = max(valeur * ratio - 0.1, 0.0)
        attendu.append(valeur)

    np.testing.assert_allclose(decr[0], attendu, rtol=1e-10)


def test_decrement_points_plancher_absorbant_et_perte_plafonnee():
    # 1) Cas déterministe : un décrément délibérément énorme (60/jour) fait
    #    passer l'indice sous 0 dès le premier pas -- avec le plancher,
    #    l'indice doit tomber exactement à 0 et y rester (barrière absorbante),
    #    même quand les ratios suivants sont > 1 (0*ratio - décrément <= 0
    #    toujours, donc max(..., 0) = 0 indéfiniment).
    traj = np.array([[100.0, 50.0, 80.0, 120.0]])
    K = 21_900.0  # decrement_par_pas = 21900 * (365/365) / 365 = 60 / jour
    decr = appliquer_decrement_points(traj, K, nb_pas_an=365.0, jours_par_an=365.0)
    np.testing.assert_allclose(decr[0], [100.0, 0.0, 0.0, 0.0])

    # 2) Cas Monte Carlo (indice Vol Target), même K que la Figure E (K=5) :
    #    déjà suffisant pour qu'une fraction de trajectoires touche le
    #    plancher (cf. figures/figureE_resultats.csv, ~0.9% à 200 000
    #    trajectoires -- un K plus agressif ferait tomber la quasi-totalité
    #    des trajectoires à 0 bien avant maturité et empêcherait le solveur
    #    de coupon de converger). Vérifie, à travers le pricer complet, que
    #    ni le payoff ni la perte conditionnelle individuelle ne peuvent
    #    dépasser 100% du nominal -- c'est le plancher sur l'indice
    #    (spot_final >= 0) qui le garantit mécaniquement (cf.
    #    src/pricer_autocall.py).
    nb_sim, maturite = 20_000, 10
    dates_obs = np.arange(1, maturite + 1)
    nb_jours = NB_PAS_AN * maturite
    sigma = simuler_regimes(nb_jours, nb_sim, seed=61, sigma_bas=SIGMA_BAS, sigma_haut=SIGMA_HAUT,
                             duree_moyenne_calme=DUREE_CALME, duree_moyenne_stress=DUREE_STRESS)
    traj_tr = simuler_indice_sous_jacent(100.0, R, 0.0, sigma, NB_PAS_AN, seed=62)
    vt, _ = construire_indice_vt(traj_tr, R, sigma_cible=0.15, l_max=1.5, fenetre=20, nb_pas_an=NB_PAS_AN)
    vt_decr_pts = appliquer_decrement_points(vt, K=5.0, nb_pas_an=NB_PAS_AN)
    assert (vt_decr_pts == 0.0).any(), "le plancher doit être atteint par au moins une trajectoire"

    indices_obs = [int(round(t * NB_PAS_AN)) for t in dates_obs]
    spots_obs = vt_decr_pts[:, indices_obs]
    _, resultat = resoudre_coupon_pair(spots_obs, 100.0, R, dates_obs, 1.0, 0.60)

    assert resultat.spot_final.min() >= 0.0
    assert resultat.payoffs.min() >= 0.0
    pertes_individuelles = 1.0 - resultat.spot_final[resultat.pdi_actif] / 100.0
    assert pertes_individuelles.max() <= 1.0 + 1e-9
