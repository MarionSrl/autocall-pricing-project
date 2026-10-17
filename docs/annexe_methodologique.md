# Annexe – Note méthodologique

## Architecture générale

Les figures A, B, B bis, C et D et l'ensemble des résultats chiffrés de ce mémoire proviennent d'un outil de calcul développé spécifiquement pour ce travail. Il combine deux approches : des formules fermées lorsqu'elles existent (options à barrière), et des simulations de Monte Carlo pour les produits et mécanismes sans solution analytique simple (autocall à observations discrètes, indice Volatility Target, couverture dynamique).

Au sein de chaque figure, toutes les configurations comparées partagent exactement les mêmes trajectoires simulées, grâce à une graine aléatoire fixe. Un écart observé entre deux configurations ne provient donc que du mécanisme étudié, et non du bruit statistique. L'ensemble des calculs peut être relancé en une seule commande (run_all.py), qui régénère les cinq figures et le tableau des résultats à l'identique.

## Les cinq figures

| Figure | Objectif | Produit | Paramètres | Modèle de volatilité | Trajectoires |
|---|---|---|---|---|---|
| A | Sensibilités (delta, vega, vanna) à l'approche de la barrière | PDI strike 100%, barrière 60% ; autocall de référence | S₀ = 100, r = 2.5%, q = 3%, σ = 18% | Constante ; formule fermée pour le PDI | 200 000 |
| B | Effet du décrément sur le coupon au pair | Autocall de référence, six sous-jacents | Idem A ; décrément 3% (cas neutre) et 5% en pourcentage ou en points | Constante | 200 000 |
| B bis | Effet du Volatility Target sur le coupon au pair, à forward identique | Autocall de référence, huit sous-jacents | Idem B ; cibles 15% et 10% ; décrément 0%, 3% et 5% | Deux régimes, identique à D | 200 000 |
| C | Risque résiduel d'une couverture en delta | Autocall 5 ans, coupon fixe 7% | Volatilité modèle 20% ; volatilité réalisée de 15% à 30% | Constante | 2 000 par scénario |
| D | Fonctionnement et limites d'un indice Volatility Target | Indice seul | Cible 15%, levier plafonné à 150%, fenêtres de 20 et 60 jours | Deux régimes | 5 000 + un scénario de choc |

L'autocall de référence est un Athena de maturité dix ans, à observations annuelles, avec une barrière de rappel à 100%, un coupon à mémoire et un Put Down-and-In de barrière 60% observée à maturité. Son coupon est résolu de sorte que le prix du produit égale 100% du nominal.

Le modèle à deux régimes des figures B bis et D alterne des périodes de volatilité faible et des périodes de stress, chacune avec une durée moyenne propre. Il suffit à l'objectif poursuivi, puisque le mécanisme Volatility Target ne réagit qu'à la persistance de la volatilité réalisée dans le temps.

## Contrôles de validation

- Parité des formules fermées : une option activée et une option désactivée à la même barrière redonnent exactement l'option sans barrière.
- Convergence : lorsque les deux méthodes existent, le prix simulé converge vers le prix de la formule fermée, à l'erreur statistique près.
- Neutralité du décrément : un indice à décrément fixé au niveau du dividende anticipé (D = q) donne, trajectoire par trajectoire, le même coupon que l'indice Price Return.
- Absence d'arbitrage : la valeur actualisée moyenne de l'indice Volatility Target sans décrément est égale à sa valeur initiale. Les forwards simulés coïncident avec les forwards théoriques.
- Bornes : l'indice à décrément en points est planché à zéro (0.86% des trajectoires l'atteignent), et la perte de l'investisseur est plafonnée à 100% du nominal.
- Comparaisons appariées : les écarts de coupon entre configurations sont estimés sur les mêmes trajectoires, ce qui réduit fortement leur intervalle de confiance.

Ces contrôles, avec d'autres plus techniques, sont automatisés : 42 tests sont vérifiés à chaque régénération des résultats.

## Limites

- Figures A à C : volatilité constante, sans smile ni dynamique de volatilité. La valeur de la protection, et avec elle le coupon au pair, est probablement sous-estimée. Les niveaux absolus diffèrent donc de ceux d'un modèle de desk, mais les comparaisons entre configurations restent valides, puisqu'elles reposent sur les mêmes hypothèses et les mêmes trajectoires.
- Figures B bis et D : le modèle à deux régimes est plus simple qu'un modèle à volatilité stochastique ou locale-stochastique. Il suffit à illustrer le mécanisme sans prétendre reproduire un marché réel.
- Observation de la barrière : la protection du produit est observée à maturité, alors que la formule fermée de la figure A suppose une barrière observée en continu.
- Coûts de transaction : ils ne sont pas pris en compte, ni pour la couverture en delta (figure C) ni pour le rééquilibrage de l'indice Volatility Target. Les mécanismes sont donc présentés dans leur configuration la plus favorable.

## Code source

https://github.com/MarionSrl/autocall-pricing-project
