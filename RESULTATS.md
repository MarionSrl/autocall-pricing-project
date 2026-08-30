# Résultats numériques du mémoire

Généré automatiquement par `scripts/generer_resultats.py` à partir des CSV produits par `scripts/figA_sensibilites_pdi_autocall.py`, `figB_autocall_vs_decrement.py` et `figC_volatility_target.py` (seed globale unique, `src/marche.py::SEED_GLOBAL`). **Ne pas éditer à la main** : relancer `python scripts/run_all.py` pour tout régénérer si un paramètre ou une seed change.

## Figure A — Sensibilités du PDI et de l'autocall

| Grandeur | Valeur |
|---|---|
| Delta du PDI juste sous la barrière (spot=59.99) | -0.97 |
| Delta du PDI juste au-dessus de la barrière (spot=60.01) | -2.52 |
| Spot où le vega total de l'autocall s'annule | 71.05 |
| Vega total à ce spot (résiduel MC, erreur std 1.65 pt) | -0.00 % |

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
