"""Génère RESULTATS.md à la racine du repo : tous les chiffres cités dans le
mémoire, regroupés par figure, à partir des CSV déjà produits par les scripts
de figure (fig1_*.py, fig2_*.py, fig3_*.py).

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


def section_figure2():
    df = _lire("figure2_resultats.csv")
    lignes = [
        "## Figure 2 — Autocall classique vs décrément",
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


def section_figure1():
    df_delta = _lire("figure1_delta_discontinuite.csv")
    df_zero = _lire("figure1_spot_zero_vega.csv")

    delta_bas = df_delta.loc[df_delta["position"].str.contains("sous"), "delta"].iloc[0]
    delta_haut = df_delta.loc[df_delta["position"].str.contains("dessus"), "delta"].iloc[0]
    spot_zero = df_zero["spot_zero_vega"].iloc[0]
    vega_zero = df_zero["vega_pct"].iloc[0]
    erreur_std_zero = df_zero["erreur_std_pct"].iloc[0]

    lignes = [
        "## Figure 1 — Sensibilités du PDI et de l'autocall",
        "",
        "| Grandeur | Valeur |",
        "|---|---|",
        f"| Delta du PDI juste sous la barrière (spot=59.99) | {_fmt(delta_bas)} |",
        f"| Delta du PDI juste au-dessus de la barrière (spot=60.01) | {_fmt(delta_haut)} |",
        f"| Spot où le vega total de l'autocall s'annule | {_fmt(spot_zero)} |",
        f"| Vega total à ce spot (résiduel MC, erreur std {_fmt(erreur_std_zero)} pt) | {_fmt(vega_zero)} % |",
    ]
    return "\n".join(lignes)


def section_figure3():
    df_vol = _lire("figure3_distribution_vol_realisee.csv")
    df_v = _lire("figure3_scenario_v_resume.csv")

    lignes = [
        "## Figure 3 — Indice Volatility Target",
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


def main():
    contenu = "\n\n".join([
        "# Résultats numériques du mémoire",
        "Généré automatiquement par `scripts/generer_resultats.py` à partir des CSV produits par "
        "`scripts/fig1_sensibilites_pdi_autocall.py`, `fig2_autocall_vs_decrement.py` et "
        "`fig3_volatility_target.py` (seed globale unique, `src/marche.py::SEED_GLOBAL`). "
        "**Ne pas éditer à la main** : relancer `python scripts/run_all.py` pour tout régénérer "
        "si un paramètre ou une seed change.",
        section_figure1(),
        section_figure2(),
        section_figure3(),
    ])
    chemin = os.path.join(REPERTOIRE_RACINE, "RESULTATS.md")
    with open(chemin, "w") as f:
        f.write(contenu + "\n")
    print(f"Résultats consolidés écrits : {chemin}")


if __name__ == "__main__":
    main()
