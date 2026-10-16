# Résultats numériques du mémoire

Généré automatiquement par `scripts/generer_resultats.py` à partir des CSV produits par `scripts/figA_sensibilites_pdi_autocall.py`, `figB_autocall_vs_decrement.py`, `figC_hedging_produit_notebook.py`, `figD_volatility_target.py` et `figE_vol_target_decrement.py` (seed globale unique, `src/marche.py::SEED_GLOBAL`). **Ne pas éditer à la main** : relancer `python scripts/run_all.py` pour tout régénérer si un paramètre ou une seed change.

## Figure A — Sensibilités du PDI et de l'autocall

| Grandeur | Valeur |
|---|---|
| Delta du PDI juste sous la barrière (spot=59.99) | -0.97 |
| Delta du PDI juste au-dessus de la barrière (spot=60.01) | -2.52 |
| Spot où le vega total de l'autocall s'annule | 71.05 |
| Vega total à ce spot (résiduel MC, erreur std 0.02 pt) | -0.00 % |
| Validation formule fermée : parité KI+KO=vanille (écart max sur 6 spots) | 0.00 % |
| Validation formule fermée : convergence MC (spot=70, 200 000 traj.) | 0.25 % |

## Figure B — Autocall classique vs décrément

| Cas | Coupon au pair (%) | Erreur std MC (%) | Forward théorique 10 ans | Proba. rappel avant maturité (%) | Proba. activation PDI (%) | Perte moy. conditionnelle (%) |
|---|---|---|---|---|---|---|
| A — Indice classique | 11.83 | 0.08 | 95.12 | 74.59 | 16.75 | 58.57 |
| B — Décrément % (D=5 %/an) | 17.92 | 0.10 | 77.88 | 66.51 | 24.78 | 60.94 |
| B′ — Décrément % (D=q=3 %, contrôle) | 11.83 | 0.08 | 95.12 | 74.59 | 16.75 | 58.57 |
| C — Décrément points (K=5) | 26.45 | 0.14 | 71.60 | 63.42 | 31.78 | 73.94 |
| C′ — Décrément points + barrière dégressive | 15.22 | 0.10 | 71.60 | 79.64 | 19.99 | 79.27 |
| A — Barrière dégressive | 6.68 | 0.05 | 95.12 | 90.08 | 9.13 | 61.60 |

## Figure C — Delta hedging et risques résiduels de couverture

*Porte sur le produit du notebook (5 ans, coupon fixe 7%, vol modèle 20%), distinct du produit de référence des Figures A, B et D -- voir le README.*

| Grandeur | Valeur |
|---|---|
| Gamma moyen du portefeuille (dollar-gamma, scénario de référence) | -0.02605 |
| Gamma×spot² moyen réalisé (utilisé pour la courbe théorique) | -191.57418 |
| Temps de sortie moyen (rappel ou maturité), scénario de référence | 2.35 ans |
| Prix initial (modèle) | 98.09 % |
| Trajectoires de la grille delta/gamma | 10000 |
| Trajectoires de couverture par scénario | 2000 |

| Vol réalisée (%) | PnL moyen | Erreur std | PnL théorique (gamma-trading) |
|---|---|---|---|
| 15.00 | -2.52 | 0.14 | -3.94 |
| 20.00 | 1.16 | 0.17 | -0.00 |
| 25.00 | 5.02 | 0.24 | 5.07 |
| 30.00 | 8.34 | 0.30 | 11.27 |

| Fréquence de rebalancement | PnL moyen | Écart-type du PnL | Erreur std |
|---|---|---|---|
| 1j | 0.93 | 7.68 | 0.17 |
| 5j | 0.84 | 7.50 | 0.17 |
| 10j | 1.29 | 8.05 | 0.18 |
| 20j | 1.19 | 8.22 | 0.18 |

## Figure D — Indice Volatility Target

| Grandeur | Valeur |
|---|---|
| Vol réalisée moyenne de l'indice VT (cible 15.00 %) | 16.01 % |
| Vol réalisée médiane de l'indice VT | 16.03 % |
| Écart-type de la vol réalisée de l'indice VT | 1.31 pt |
| Proportion de trajectoires dans ±2 pt de la cible | 76.00 % |
| Temps passé à l'exposition plafond (L_max) sur la trajectoire type | 29.82 % |
| Sous-participation au rebond, fenêtre 20j | 17.55 pts |
| Sous-participation au rebond, fenêtre 60j | 18.27 pts |
| Écart indice nu − indice VT en fin de scénario, fenêtre 20j | 17.83 pts |
| Écart indice nu − indice VT en fin de scénario, fenêtre 60j | 18.31 pts |
| Niveau plancher (creux) de l'indice nu dans le scénario V | 70.00 |
| Niveau plancher (creux) de l'indice VT dans le scénario V, fenêtre 20j | 63.79 |
| Niveau plancher (creux) de l'indice VT dans le scénario V, fenêtre 60j | 61.17 |

## Figure E — Indice Volatility Target et décrément

| Configuration | Coupon au pair (%) | IC95 (demi-largeur, %) | Vol réalisée moy. (%) | Proba. rappel avant maturité (%) | Proba. activation PDI (%) | Perte moy. conditionnelle (%) | Forward MC 10 ans | Proba. indice négatif (%) |
|---|---|---|---|---|---|---|---|---|
| Indice nu (price return) | 11.46 | 0.10 | 17.71 | 75.03 | 16.07 | 58.26 | 95.27 | 0.00 |
| Vol Target 15% | 5.89 | 0.05 | 16.17 | 86.59 | 5.94 | 53.50 | 128.49 | 0.00 |
| Vol Target 10% | 4.35 | 0.03 | 11.86 | 90.06 | 2.00 | 48.58 | 128.46 | 0.00 |
| Vol Target 15% + décrément 5%/an | 17.42 | 0.16 | 16.17 | 65.96 | 23.73 | 58.60 | 77.93 | 0.00 |
| Vol Target 15% + décrément points (K=5) | 25.62 | 0.24 | 16.18 | 63.01 | 31.18 | 70.64 | 71.64 | 0.86 |
