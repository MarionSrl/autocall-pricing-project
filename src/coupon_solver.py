"""Solveur de coupon au pair : cherche le coupon annuel c tel que prix(c) = nominal."""

from scipy.optimize import brentq

from .pricer_autocall import pricer_autocall


def resoudre_coupon_pair(spots_obs, s0, r, dates_obs, barriere_ac, barriere_cap,
                          nominal=1.0, bracket=(0.0, 0.20), xtol=1e-6,
                          facteur_extension=2.0, borne_max=5.0):
    """
    Résout prix(coupon) - nominal = 0 par dichotomie de Brent.

    Les trajectoires (spots_obs) sont générées une seule fois en amont et
    réutilisées telles quelles à chaque évaluation du solveur (pas de
    rebruitage Monte Carlo d'un essai à l'autre) : le prix est monotone
    croissant en coupon (chaque paiement conditionnel n'est que revalorisé
    à la hausse), donc la recherche par dichotomie est stable.

    Le bracket par défaut [0%, 20%] suffit pour un autocall usuel, mais un
    sous-jacent très pénalisant (fort décrément) peut demander un coupon
    largement supérieur pour revenir au pair : si le bracket ne s'encadre
    pas, la borne haute est doublée (jusqu'à borne_max) plutôt que d'échouer
    silencieusement — sans jamais régénérer les trajectoires.

    Retourne (coupon_pair, ResultatAutocall au coupon trouvé).
    """
    def ecart(coupon):
        resultat = pricer_autocall(spots_obs, s0, r, dates_obs, barriere_ac, coupon, barriere_cap)
        return resultat.prix - nominal

    borne_basse, borne_haute = bracket
    while ecart(borne_basse) * ecart(borne_haute) > 0:
        if borne_haute >= borne_max:
            raise RuntimeError(
                f"Coupon au pair introuvable dans [{borne_basse*100:.0f}%, {borne_max*100:.0f}%] : "
                "le produit ne semble pas pouvoir revenir au pair sur cette plage."
            )
        borne_haute = min(borne_haute * facteur_extension, borne_max)

    coupon_pair = brentq(ecart, borne_basse, borne_haute, xtol=xtol)
    resultat = pricer_autocall(spots_obs, s0, r, dates_obs, barriere_ac, coupon_pair, barriere_cap)
    return coupon_pair, resultat
