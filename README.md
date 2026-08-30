# Pricing et Hedging d’un Produit Autocallable

## Objectif du projet

Ce projet consiste à développer un **pricer Monte Carlo d’un produit autocallable** sous le modèle de Black-Scholes, puis à analyser :

- La sensibilité aux paramètres de marché (volatilité, taux)
- L’impact de l’introduction de taux stochastiques (modèle de Vasicek)
- La performance d’une stratégie de couverture (delta hedging)
- La distribution du PnL résiduel

---

## Description du produit

Produit autocallable avec :

- Maturité : 5 ans  
- Dates d’observation : annuelles  
- Barrière autocall : 100% du spot initial  
- Coupon : 7% par an (cumulé si rappel anticipé)  
- Barrière de protection : 60%  

### Structure du payoff :

- Si \(S_t >= 100% \) → remboursement anticipé + coupon  
- Sinon → le produit continue  
- À maturité :
  - Si \(S_T >= 60% \) → remboursement du capital  
  - Sinon → perte proportionnelle au sous-jacent  

---

## Méthodologie

### 1. Simulation Monte Carlo

- Simulation du sous-jacent sous Black-Scholes :
  
\[
dS_t = r S_t dt + \sigma S_t dW_t
\]

- Implémentation vectorisée pour améliorer la performance

---

### 2. Pricing

- Évaluation du payoff path-dependent  
- Actualisation des flux  
- Estimation du prix par moyenne Monte Carlo  

---

### 3. Analyse de sensibilité

Étude de l’impact de :

- La volatilité (σ)
- Le taux d’intérêt (r)

Résultats :

- La volatilité réduit la probabilité d’autocall  
- Le taux impacte le prix via le drift et l’actualisation  

---

### 4. Calcul des grecs

Calcul par différences finies :

- Delta  
- Gamma  
- Vega  

Observations :

- Delta fortement non-linéaire autour des barrières  
- Gamma concentré → zones difficiles à hedger  
- Vega négatif (produit short vol)  

---

### 5. Taux stochastiques (Vasicek)

Modèle utilisé :

\[
dr_t = a(b - r_t)dt + \sigma_r dW_t
\]

- Simulation conjointe spot + taux  
- Actualisation stochastique  
- Analyse de l’impact de :
  - la volatilité du taux
  - la corrélation spot/taux  

---

### 6. Delta Hedging

- Estimation du delta par bump & reprice  
- Construction d’une grille de delta  
- Interpolation pour le hedging dynamique  

Simulation du PnL :

\[
PnL = portefeuille de couverture - payoff
\]

---

### 7. Analyse du PnL

Étude de :

- La distribution du PnL  
- L’impact de la fréquence de rebalancement  
- L’impact de la volatilité réalisée  

Résultats :

- Le PnL dépend fortement de la trajectoire (path-dependence)  
- Le gamma génère un PnL résiduel  
- Le mismatch vol implicite / vol réalisée est clé  

---

## Résultats clés

- Plus la volatilité est élevée, plus la probabilité d’autocall diminue  
- Le produit est globallement **short vega**  
- Le hedging n’est pas parfait (risque gamma)  
- Les taux stochastiques ont un impact non négligeable  
- Le PnL de hedging dépend fortement des conditions de marché  

---

## Installation
Pour exécuter le projet, il est recommandé de créer un environnement virtuel afin d’isoler les dépendances :

python3 -m venv venv


source venv/bin/activate


pip install -r requirements.txt

---

## Bibilothèque nécessaire
- Python  
- NumPy  
- Matplotlib  
- SciPy  

---

## Structure du projet
- notebooks : Analyse et visualisations
- src : Fonctions de pricing et simulation
- results : Graphiques et résultats
- README.md : Explication du projet
- requirements.txt : Bibilothèque nécessaire


---

## Figures quantitatives du mémoire (`src/`, `scripts/`, `tests/`, `figures/`)

En complément du notebook d'exploration ci-dessus, le repo contient un module Python
autonome qui reproduit les figures quantitatives insérées dans le mémoire (produit
autocall 10 ans, sous-jacents à décrément, indice Volatility Target), avec leurs tests
et leurs sorties chiffrées réutilisables directement dans le texte.

- `src/` : `marche.py` (paramètres marché), `simulation.py` (GBM générique, variables
  antithétiques), `indices.py` (indices A/B/C construits sur les mêmes chocs gaussiens,
  barrière dégressive), `pricer_autocall.py` (pricer MC de l'autocall), `coupon_solver.py`
  (coupon au pair par dichotomie de Brent), `style_graphique.py` / `reporting.py` (rendu).
- `scripts/` : un script par figure, qui écrit son PNG (300 dpi, `figures/`) et ses
  résultats numériques (`figures/*.csv` et `.md`).
- `tests/` : pytest (convergence, parités, cas limites — voir plus bas).
- Le notebook `notebooks/Pricer_Autocall_MC.ipynb` reste indépendant de `src/` et
  continue de fonctionner tel quel (taux de Vasicek, delta hedging, etc., hors périmètre
  des figures du mémoire).

Pour reproduire une figure : `pip install -r requirements.txt` puis, par exemple,
`python scripts/fig2_autocall_vs_decrement.py`.

### Convention du coupon — à lire avant d'interpréter les résultats

Le produit est un autocall « à mémoire » au sens suivant : à la date de rappel `t_obs`,
le porteur reçoit `1 + coupon × t_obs`, c'est-à-dire l'ensemble des coupons annuels
cumulés depuis l'origine (effet mémoire). **Si le produit atteint la maturité sans
jamais avoir été rappelé, aucun coupon n'est versé** — seul le capital est remboursé
(intégralement si le PDI n'est pas activé, sinon proportionnellement au sous-jacent).
Cette convention correspond à un autocall à barrière unique (le même niveau déclenche
à la fois le rappel et l'accumulation du coupon), sans barrière de coupon indépendante.

Cette convention n'est pas neutre pour la comparaison des sous-jacents de la Figure 2 :
les indices à décrément retardent mécaniquement le rappel (la barrière de 100 % est plus
difficile à atteindre), ce qui **augmente la probabilité d'aller à maturité sans jamais
toucher de coupon**. Une partie de la hausse du coupon facial affichée par les indices à
décrément compense donc explicitement ce risque de ne rien percevoir, et pas seulement
le risque de perte en capital — c'est un point de lecture essentiel pour l'interprétation
de la Figure 2, distinct de la seule probabilité d'activation du PDI.

### Hypothèses de modélisation et leurs limites

- **Barrières observées discrètement** (annuellement pour le rappel, à maturité pour le
  PDI), conformément au produit décrit. Le pricer Monte Carlo observe donc les barrières
  aux dates de la grille de simulation et non en continu ; aucun ajustement de type
  Broadie–Glasserman–Kou (correction du niveau de barrière pour un monitoring discret)
  n'est appliqué à ce stade — il n'est pertinent que pour une barrière **continue** que
  le mémoire n'évalue pas ici (le PDI, en particulier, est explicitement à maturité
  uniquement, donc sans ambiguïté de monitoring).
- **Volatilité constante et absence de skew** : tous les sous-jacents (A, B, C) sont
  modélisés sous Black-Scholes avec une volatilité unique et constante (18 %). En
  pratique, un smile/skew de volatilité affecterait différemment les zones proches des
  barrières (rappel comme PDI) ; son absence est une simplification qui **sous-estime
  probablement** l'ampleur des sensibilités mises en évidence dans les Figures 1 et 3.
- **Pas de coûts de transaction ni de frais de gestion** : ni sur la réplication du
  décrément (indices B et C), ni sur un éventuel rebalancement dynamique (Figure 3,
  indice Volatility Target). Les mécanismes étudiés sont donc présentés dans leur version
  la plus favorable ; en pratique les coûts réduiraient les niveaux de coupon atteignables
  et amplifieraient la sous-performance des indices Volatility Target au rebalancement.
- **Corrélation parfaite entre A, B, C** : les trois sous-jacents comparés partagent les
  mêmes trajectoires browniennes (même graine, mêmes chocs gaussiens), afin d'isoler
  strictement l'effet du mécanisme de décrément (« toutes choses égales par ailleurs »).
  Ce n'est pas une hypothèse de marché (des indices décrément réels n'évoluent pas de
  façon parfaitement corrélée à leur indice de référence) mais un choix méthodologique
  de comparaison contrôlée.
- **Convention du coupon à mémoire sans barrière de coupon indépendante** : voir le
  paragraphe dédié ci-dessus.

## Extensions possibles

- Modèle de volatilité stochastique (Heston)  
- Smile de volatilité  
- Produits multi-sous-jacents (Worst-of autocall)  
- Pricer en EDP

---

## Auteur

Projet réalisé dans le cadre du **cours Produits Structurés — M2 BFA (Dauphine) par Juliette Colombani, Violaine Mencke, Mathilde Largarde, Marion Sirol**.
