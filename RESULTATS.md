# Résultats numériques du mémoire

Généré automatiquement par `scripts/generer_resultats.py` à partir des CSV produits par `scripts/figA_sensibilites_pdi_autocall.py`, `figB_autocall_vs_decrement.py`, `figC_volatility_target.py` et `figD_hedging_produit_notebook.py` (seed globale unique, `src/marche.py::SEED_GLOBAL`). **Ne pas éditer à la main** : relancer `python scripts/run_all.py` pour tout régénérer si un paramètre ou une seed change.

## Figure A — Sensibilités du PDI et de l'autocall

| Grandeur | Valeur |
|---|---|
| Delta du PDI juste sous la barrière (spot=59.99) | -0.97 |
| Delta du PDI juste au-dessus de la barrière (spot=60.01) | -2.52 |
| Spot où le vega total de l'autocall s'annule | 71.05 |
| Vega total à ce spot (résiduel MC, erreur std 0.02 pt) | -0.00 % |

## Figure B — Autocall classique vs décrément

| Cas | Coupon au pair (%) | Erreur std MC (%) | Forward théorique 10 ans | Proba. rappel avant maturité (%) | Proba. activation PDI (%) | Perte moy. conditionnelle (%) |
|---|---|---|---|---|---|---|
| A — Indice classique | 11.83 | 0.08 | 95.12 | 74.59 | 16.75 | 58.57 |
| B — Décrément % (D=5 %/an) | 17.92 | 0.10 | 77.88 | 66.51 | 24.78 | 60.94 |
| B′ — Décrément % (D=q=3 %, contrôle) | 11.83 | 0.08 | 95.12 | 74.59 | 16.75 | 58.57 |
| C — Décrément points (K=5) | 26.45 | 0.14 | 71.60 | 63.42 | 31.78 | 73.94 |
| C′ — Décrément points + barrière dégressive | 15.22 | 0.10 | 71.60 | 79.64 | 19.99 | 79.27 |
| A — Barrière dégressive | 6.68 | 0.05 | 95.12 | 90.08 | 9.13 | 61.60 |

## Figure C — Indice Volatility Target

| Grandeur | Valeur |
|---|---|
| Vol réalisée moyenne de l'indice VT (cible 15.00 %) | 16.01 % |
| Sous-participation au rebond, fenêtre 20j | 17.55 pts |
| Sous-participation au rebond, fenêtre 60j | 18.27 pts |
| Écart indice nu − indice VT en fin de scénario, fenêtre 20j | 17.83 pts |
| Écart indice nu − indice VT en fin de scénario, fenêtre 60j | 18.31 pts |

## Figure D — Delta hedging et risques résiduels de couverture

*Porte sur le produit du notebook (5 ans, coupon fixe 7%, vol modèle 20%), distinct du produit de référence des Figures A-C -- voir le README.*

| Grandeur | Valeur |
|---|---|
| Gamma moyen du portefeuille (dollar-gamma, scénario de référence) | -0.02605 |
| Temps de sortie moyen (rappel ou maturité), scénario de référence | 2.35 ans |
| Prix initial (modèle) | 98.09 % |
| Trajectoires de la grille delta/gamma | 10000 |
| Trajectoires de couverture par scénario | 2000 |

| Vol réalisée (%) | PnL moyen | PnL théorique (gamma-trading) |
|---|---|---|
| 15.00 | -2.52 | -3.94 |
| 20.00 | 1.16 | -0.00 |
| 25.00 | 5.02 | 5.07 |
| 30.00 | 8.34 | 11.27 |

| Fréquence de rebalancement | PnL moyen | Écart-type du PnL |
|---|---|---|
| 1j | 0.93 | 7.68 |
| 5j | 0.84 | 7.50 |
| 10j | 1.29 | 8.05 |
| 20j | 1.19 | 8.22 |
