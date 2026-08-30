"""Génère RESULTATS.md à la racine du repo : tous les chiffres cités dans le
mémoire, regroupés par figure, à partir des CSV déjà produits par les scripts
de figure (figA_*.py, figB_*.py, figC_*.py, figD_*.py).

Ne relance aucune simulation : suppose que figures/*.csv existent déjà. Pour
tout régénérer depuis zéro (figures + ce fichier), utiliser scripts/run_all.py.

Décimales homogènes (2 partout) pour recopie directe dans le mémoire.
"""

import os

import pandas as pd

REPERTOIRE_RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPERTOIRE_FIGURES = os.path.join(REPERTOIRE_RACINE, "figures")
DECIMALES = "{:.2f}"


def _lire(nom_fichier):
    chemin = os.path.join(REPERTOIRE_FIGURES, nom_fichier)
    if not os.path.exists(chemin):
        raise FileNotFoundError(
            f"{chemin} introuvable -- lancer d'abord les scripts de figure "
            "(ou scripts/run_all.py pour tout régénérer)."
        )
    return pd.read_csv(chemin)


def _fmt(valeur):
    return DECIMALES.format(valeur)


def section_figureB():
    df = _lire("figureB_resultats.csv")
    lignes = [
        "## Figure B — Autocall classique vs décrément",
        "",
        "| Cas | Coupon au pair (%) | Erreur std MC (%) | Forward théorique 10 ans | "
        "Proba. rappel avant maturité (%) | Proba. activation PDI (%) | Perte moy. conditionnelle (%) |",
        "|---|---|---|---|---|---|---|",
    ]
    for _, ligne in df.iterrows():
        proba_rappel_avant_maturite = 100.0 - ligne["proba_maturite_pct"]
        lignes.append(
            f"| {ligne['cas']} | {_fmt(ligne['coupon_pair_pct'])} | {_fmt(ligne['erreur_std_mc_pct'])} | "
            f"{_fmt(ligne['forward_theorique_10y'])} | {_fmt(proba_rappel_avant_maturite)} | "
            f"{_fmt(ligne['proba_pdi_actif_pct'])} | {_fmt(ligne['perte_moyenne_cond_pct'])} |"
        )
    return "\n".join(lignes)


def section_figureA():
    df_delta = _lire("figureA_delta_discontinuite.csv")
    df_zero = _lire("figureA_spot_zero_vega.csv")

    delta_bas = df_delta.loc[df_delta["position"].str.contains("sous"), "delta"].iloc[0]
    delta_haut = df_delta.loc[df_delta["position"].str.contains("dessus"), "delta"].iloc[0]
    spot_zero = df_zero["spot_zero_vega"].iloc[0]
    vega_zero = df_zero["vega_pct"].iloc[0]
    erreur_std_zero = df_zero["erreur_std_pct"].iloc[0]

    lignes = [
        "## Figure A — Sensibilités du PDI et de l'autocall",
        "",
        "| Grandeur | Valeur |",
        "|---|---|",
        f"| Delta du PDI juste sous la barrière (spot=59.99) | {_fmt(delta_bas)} |",
        f"| Delta du PDI juste au-dessus de la barrière (spot=60.01) | {_fmt(delta_haut)} |",
        f"| Spot où le vega total de l'autocall s'annule | {_fmt(spot_zero)} |",
        f"| Vega total à ce spot (résiduel MC, erreur std {_fmt(erreur_std_zero)} pt) | {_fmt(vega_zero)} % |",
    ]
    return "\n".join(lignes)


def section_figureC():
    df_vol = _lire("figureC_distribution_vol_realisee.csv")
    df_v = _lire("figureC_scenario_v_resume.csv")

    lignes = [
        "## Figure C — Indice Volatility Target",
        "",
        "| Grandeur | Valeur |",
        "|---|---|",
        f"| Vol réalisée moyenne de l'indice VT (cible {_fmt(df_vol['sigma_cible_pct'].iloc[0])} %) | "
        f"{_fmt(df_vol['vol_realisee_moyenne_pct'].iloc[0])} % |",
    ]
    for _, ligne in df_v.iterrows():
        fenetre = int(ligne["fenetre_jours"])
        lignes.append(
            f"| Sous-participation au rebond, fenêtre {fenetre}j | {_fmt(ligne['sous_participation_pts'])} pts |"
        )
    for _, ligne in df_v.iterrows():
        fenetre = int(ligne["fenetre_jours"])
        ecart_fin = 100.0 - ligne["niveau_indice_vt_fin_episode"]
        lignes.append(
            f"| Écart indice nu − indice VT en fin de scénario, fenêtre {fenetre}j | {_fmt(ecart_fin)} pts |"
        )
    return "\n".join(lignes)


def section_figureD():
    df_vol = _lire("figureD_pnl_vs_vol_realisee.csv")
    df_resume = _lire("figureD_resume.csv")
    df_freq = _lire("figureD_pnl_vs_frequence.csv")
    resume = df_resume.iloc[0]

    lignes = [
        "## Figure D — Delta hedging et risques résiduels de couverture",
        "",
        "*Porte sur le produit du notebook (5 ans, coupon fixe 7%, vol modèle 20%), "
        "distinct du produit de référence des Figures A-C -- voir le README.*",
        "",
        "| Grandeur | Valeur |",
        "|---|---|",
        f"| Gamma moyen du portefeuille (dollar-gamma, scénario de référence) | {resume['gamma_moyen_dollar']:.5f} |",
        f"| Temps de sortie moyen (rappel ou maturité), scénario de référence | {_fmt(resume['temps_sortie_moyen_annees'])} ans |",
        f"| Prix initial (modèle) | {_fmt(resume['prix_initial_pct'])} % |",
        f"| Trajectoires de la grille delta/gamma | {int(resume['nb_trajectoires_grille_delta'])} |",
        f"| Trajectoires de couverture par scénario | {int(resume['nb_trajectoires_couverture_par_scenario'])} |",
        "",
        "| Vol réalisée (%) | PnL moyen | PnL théorique (gamma-trading) |",
        "|---|---|---|",
    ]
    for _, ligne in df_vol.iterrows():
        lignes.append(
            f"| {_fmt(ligne['vol_realisee_pct'])} | {_fmt(ligne['pnl_moyen'])} | {_fmt(ligne['pnl_theorique'])} |"
        )
    lignes += [
        "",
        "| Fréquence de rebalancement | PnL moyen | Écart-type du PnL |",
        "|---|---|---|",
    ]
    for _, ligne in df_freq.iterrows():
        lignes.append(
            f"| {int(ligne['freq_rebal_jours'])}j | {_fmt(ligne['pnl_moyen'])} | {_fmt(ligne['pnl_ecart_type'])} |"
        )
    return "\n".join(lignes)


def main():
    contenu = "\n\n".join([
        "# Résultats numériques du mémoire",
        "Généré automatiquement par `scripts/generer_resultats.py` à partir des CSV produits par "
        "`scripts/figA_sensibilites_pdi_autocall.py`, `figB_autocall_vs_decrement.py`, "
        "`figC_volatility_target.py` et `figD_hedging_produit_notebook.py` "
        "(seed globale unique, `src/marche.py::SEED_GLOBAL`). "
        "**Ne pas éditer à la main** : relancer `python scripts/run_all.py` pour tout régénérer "
        "si un paramètre ou une seed change.",
        section_figureA(),
        section_figureB(),
        section_figureC(),
        section_figureD(),
    ])
    chemin = os.path.join(REPERTOIRE_RACINE, "RESULTATS.md")
    with open(chemin, "w") as f:
        f.write(contenu + "\n")
    print(f"Résultats consolidés écrits : {chemin}")


if __name__ == "__main__":
    main()
