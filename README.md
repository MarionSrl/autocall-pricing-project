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
- Le produit est **short vega**  
- Le hedging n’est pas parfait (risque gamma)  
- Les taux stochastiques ont un impact non négligeable  
- Le PnL de hedging dépend fortement des conditions de marché  

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

## Extensions possibles

- Modèle de volatilité stochastique (Heston)  
- Smile de volatilité  
- Produits multi-sous-jacents (Worst-of autocall)  
- Pricer en EDP

---

## Auteur

Projet réalisé dans le cadre du **cours Produits Structurés — M2 BFA (Dauphine) par Juliette Colombani, Violaine Mencke, Mathilde Largarde, Marion Sirol**.
