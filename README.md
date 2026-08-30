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
  cas de contrôle B′, barrière dégressive), `barrier_options.py` (formule fermée du PDI,
  validation MC), `pricer_autocall.py` (pricer MC de l'autocall, décomposition en jambes),
  `coupon_solver.py` (coupon au pair par dichotomie de Brent), `vol_target.py` (modèle de
  vol à 2 régimes, indice Volatility Target), `style_graphique.py` / `reporting.py`
  (rendu).
- `scripts/` : un script par figure, qui écrit son PNG (300 dpi, `figures/`) et ses
  résultats numériques (`figures/*.csv` et `.md`).
- `tests/` : pytest (convergence, parités, cas limites — voir plus bas).
- Le notebook `notebooks/Pricer_Autocall_MC.ipynb` reste indépendant de `src/` et
  continue de fonctionner tel quel (taux de Vasicek, delta hedging, etc., hors périmètre
  des figures du mémoire).

Pour reproduire une figure : `pip install -r requirements.txt` puis, par exemple,
`python scripts/fig2_autocall_vs_decrement.py`.

### Figure 1 — le PDI en formule fermée, et le vega de l'autocall complet

**Panneau (a)** trace, en formule fermée (`src/barrier_options.py::put_down_and_in`,
Bouzoubaa & Osseiran §10.2.2 / Hull ch.26, cas H<K), le prix, le delta, le vega et la
vanna d'un put down-and-in 100/60 à 1 an, pour un spot de 40 % à 130 % du niveau
initial. **Point de méthode important, corrigé en cours de développement** : la formule
de réflexion n'est valable que pour spot > barrière (elle est dérivée sous l'hypothèse
que la barrière n'a pas encore été touchée). Pour spot ≤ barrière, l'option est
certainement « in » et vaut alors exactement le put vanille — ce cas est traité
explicitement dans le code plutôt que laissé à une extrapolation incorrecte de la
formule (qui donnait, avant correction, des prix supérieurs au put vanille sous la
barrière — impossible économiquement). C'est précisément ce recollement qui produit la
**discontinuité de delta à la barrière** (delta ≈ −0.97 juste sous 60, saut à ≈ −2.52
juste au-dessus) que le panneau doit démontrer. Sur tout le domaine spot > barrière, le
**vega du PDI reste strictement positif** (jamais négatif, vérifié numériquement sur
2000 points de la grille) — conforme à l'attendu.

**Panneau (b)** reprend le produit de référence (10 ans, section 1) avec son coupon
résolu au pair pour un spot de 100. Ce coupon est calculé **exactement** comme dans la
Figure 2 (même fonction `simuler_indices`, même seed, même grille quotidienne, indice A
extrait de la même façon) plutôt que par une simulation indépendante à pas annuel : la
spec impose une seule seed globale, donc une même quantité (le coupon au pair de
l'indice classique à spot=100) doit ressortir au même chiffre partout dans le mémoire —
**11.83 %** dans les deux figures (voir `resoudre_coupon_reference` dans le script :
une simulation séparée à seed identique mais à un nombre de pas différent tire une
suite de gaussiennes différente et ne reproduit donc pas les mêmes trajectoires, d'où
l'écart de 2 points de base observé avant cette correction).

Le vega total est tracé par Monte Carlo (bump ±1pt de vol, differencing commun),
décomposé en jambe « autocall sans PDI » et jambe « PDI » (`decomposer_legs_pdi`).
Contrairement au PDI isolé, **le vega total change de signe** : positif pour un spot
faible (jambe sans-PDI dominante), il devient négatif au-delà d'un spot d'environ
**71,05** (`trouver_spot_zero_vega`, dichotomie de Brent à seed MC fixe — à lire comme
une estimation ponctuelle : l'erreur standard du vega au voisinage du zéro est d'environ
1,6 point, ce qui, compte tenu de la pente locale, revient à une incertitude d'environ
±0,4 sur ce spot). La jambe PDI, dont le poids relatif augmente avec le spot à mesure
que la probabilité de rappel précoce diminue, finit par dominer en signe opposé. C'est
le résultat que la spec demandait de démontrer : le vega du PDI seul est de signe
constant, celui de l'autocall complet ne l'est pas, parce que ses deux jambes ont des
expositions vega opposées.

**Validations obligatoires** (voir `tests/test_barrier_options.py`) : KI + KO = vanille
sur la formule fermée (écart nul à la précision machine) ; convergence de la formule
fermée vers un prix Monte Carlo indépendant, écart obtenu **0,25 %** à 200 000
trajectoires (spot=70). Cette convergence MC porte sur le put down-and-in **à barrière
continue** du panneau (a) — un objet différent du PDI du produit autocall (barrière
observée à maturité uniquement, cf. section suivante) — et sa méthode est détaillée
juste en dessous.

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

### Le coupon de 26,45 % du cas C n'est pas un niveau de marché

Le coupon au pair obtenu pour l'indice à décrément en points (cas C, D implicite très
supérieur à 5 % en fin de période) est de **26,45 %** — un niveau qui ne se rencontre pas
en pratique sur ce type de produit. Ce n'est pas une anomalie du pricer : c'est la
conséquence directe et attendue de la combinaison **décrément de 5 % + barrière de
rappel constante à 100 %** sur 10 ans. Avec cette combinaison, le rappel devient de plus
en plus improbable au fil des années (l'indice décroche mécaniquement de la barrière), le
produit va très souvent jusqu'à maturité — et, du fait de la convention « à mémoire sans
barrière de coupon indépendante » ci-dessus, ne verse alors aucun coupon. Le coupon
facial doit donc devenir extrême pour compenser, sur les scénarios où le rappel a
effectivement lieu, la probabilité élevée de n'en toucher aucun. **Ce chiffre est un
résultat de démonstration, pas une proposition de structuration réaliste.**

Deux cas supplémentaires isolent chacun un aspect de cette lecture :

- **B′ — décrément en % avec D = q = 3 %** (cas de contrôle). En fixant le décrément
  exactement au niveau du dividende réel de l'indice A, B′ est — trajectoire par
  trajectoire, pas seulement en espérance — **identique à A** (voir
  `src/indices.py::indice_decrement_pourcentage` et le test associé). Le coupon au pair
  obtenu est rigoureusement le même que celui d'A (11,83 %). Cela isole l'effet du
  *mécanisme* de décrément de l'effet « le décrément excède le dividende réel » : tout
  l'écart entre B (17,92 %) et A vient des 2 points de décrément en trop (5 % contre 3 %
  de dividende réel), pas du mécanisme en tant que tel.
- **C′ — décrément en points + barrière dégressive** (−5 %/an, plancher 70 %), qui
  correspond à la configuration réellement commercialisée en retail : le décrément seul
  (cas C) rend le rappel trop improbable pour être vendable, la barrière dégressive le
  compense en facilitant le rappel anticipé. Le coupon au pair retombe à **15,2 %**, à la
  limite haute d'une fourchette de marché plausible (8–15 %), contre 26,45 % pour C seul.
  La probabilité d'activation du PDI redescend également, de 31,8 % (C) à 20,0 % (C′),
  mais reste supérieure à celle d'A (16,8 %) : la barrière dégressive atténue l'effet du
  décrément sur le risque de perte en capital, elle ne l'annule pas. Fait notable, la
  perte moyenne *conditionnelle* sachant activation du PDI est en revanche légèrement
  plus élevée pour C′ (79,3 %) que pour C (73,9 %) : en rappelant plus tôt les scénarios
  favorables, la barrière dégressive concentre les trajectoires survivant jusqu'à
  maturité sur les scénarios les plus dégradés.

**C′ vs A + barrière dégressive : isoler l'effet du décrément seul.** Ces deux cas
partagent exactement la même barrière de rappel dégressive (−5 %/an, plancher 70 %) ;
seul le sous-jacent diffère (indice à décrément en points pour C′, indice classique pour
A + barrière dégressive). À structure de rappel strictement identique, l'écart de coupon
au pair entre les deux — **15,2 % contre 6,7 %, soit environ 8,5 points** — est donc
attribuable au seul mécanisme de décrément en points, sans effet confondu par un
changement de barrière. C'est la comparaison la plus propre du jeu de résultats pour
quantifier l'effet du décrément indépendamment de la barrière.

### Figure 3 — indice Volatility Target

Indice VT construit sur l'indice A, mécanique `e_t = min(L_max, sigma_cible /
sigma_réalisée_t)` avec `sigma_cible = 15 %`, `L_max = 150 %`, fenêtre glissante de 20
jours ouvrés, rebalancement quotidien.

**Modèle de volatilité — Heston vs 2 régimes.** Choix : un modèle à 2 régimes (calme
9 %, stress 32 %, durées moyennes 60j / 20j, cf. `src/vol_target.py` pour la
justification complète). La seule exigence de la spec est que la vol réalisée ne soit
pas constante ; un modèle à régimes l'obtient avec 4 paramètres directement
interprétables et sans les difficultés numériques de Heston (condition de Feller,
schéma de discrétisation évitant les variances négatives), pour un mécanisme qui
n'a de toute façon besoin que de la **persistance** de la vol (clustering), pas de sa
forme fine.

**Sortie 1 (trajectoire type, 5 ans).** L'indice VT suit l'indice sous-jacent en
l'amplifiant dans les phases calmes (exposition plafonnée à 150 %) et en le désamplifiant
dans les phases de stress (exposition tombant jusqu'à ~35-40 %) — l'exposition e_t
oscille nettement entre les deux bornes au gré des changements de régime.

**Sortie 2 (distribution de la vol réalisée, 5000 trajectoires, 1 an).** La vol réalisée
de l'indice VT n'égale pas la cible : moyenne **16,0 %** et médiane **16,0 %** contre une
cible de 15 %, écart-type **1,3 point**, et seulement **76 %** des trajectoires dans
`[13 %, 17 %]`. Le biais est asymétrique vers le haut : le plafond `L_max` empêche
l'indice de compenser pleinement en période calme (l'exposition ne peut pas dépasser
150 % même si `cible/vol` le voudrait), alors que rien ne borne la désensibilisation en
période de stress — d'où une vol réalisée en moyenne au-dessus, pas en dessous, de la
cible. C'est l'argument central de la section III.3.2 : le mécanisme ne délivre pas la
vol cible, par construction.

**Sortie 3 (scénario V scripté : chute de 30 % puis rebond symétrique, déterministe).**
Deux effets se combinent, tous deux défavorables à l'indice VT :
- **Avant le choc** : la période précédente est plate (vol réalisée nulle), donc
  l'exposition est bloquée au plafond de 150 % au moment où le choc survient — l'indice
  VT chute donc *plus* que l'indice nu pendant la phase de baisse (creux à ~64-67 selon
  la fenêtre, contre 70 pour l'indice nu, cf. `figure3_scenario_v.csv`).
- **Après le choc** : la fenêtre glissante intègre les rendements du crash avec retard,
  l'exposition ne se réduit qu'une fois la vol réalisée montée — trop tard pour profiter
  pleinement du rebond. **Sous-participation au rebond : 17,5 points (fenêtre 20j) et
  18,3 points (fenêtre 60j)** — l'indice nu revient exactement à 100 (par construction du
  scénario), l'indice VT plafonne autour de 82.
- **Bonus fenêtre 20j vs 60j** : la fenêtre plus longue (60j) fait pire, pas mieux, sur
  ce scénario précis — elle réagit plus lentement à la hausse de vol, reste donc
  surexposée plus longtemps pendant la chute (creux plus bas) et désamorce l'exposition
  avec un délai plus long, d'où une sous-participation légèrement supérieure. Ce
  résultat n'est pas généralisable à tout scénario (une fenêtre plus longue lisse aussi
  davantage les faux signaux sur un chemin bruité) ; il montre seulement que "plus
  longue" n'est pas synonyme de "plus prudente" face à un choc rapide et isolé.

**Limite de méthode propre à ce scénario** : la période "avant" est délibérément
parfaitement plate (vol nulle) pour isoler l'effet du choc dans un scénario scripté —
en réalité la vol réalisée n'est jamais exactement nulle, donc le plafond `L_max` ne
serait pas aussi systématiquement atteint juste avant un choc réel. L'effet de
sur-exposition au moment du choc est donc probablement exagéré par construction du
scénario ; l'effet de sous-participation au rebond (piloté par le retard structurel de
la fenêtre glissante, pas par le niveau de vol pré-choc) est en revanche robuste à cette
simplification.

### Hypothèses de modélisation et leurs limites

- **Barrières observées discrètement** (annuellement pour le rappel, à maturité pour le
  PDI), conformément au produit décrit. **Deux conventions de barrière distinctes
  coexistent dans le repo, à ne pas confondre :**

  1. **Le PDI du produit autocall** (Figures 2 et panneau b de la Figure 1) est
     observé **à maturité uniquement** (cf. section 1 de la spec / section dédiée
     ci-dessus) : ce n'est pas un monitoring discret d'une barrière continue, c'est une
     condition terminale, sans aucune ambiguïté de fréquence d'observation. Aucun
     ajustement de type Broadie–Glasserman–Kou ne s'applique à ce PDI, et il n'y en a
     pas dans le pricer MC du produit (`src/pricer_autocall.py`).
  2. **Le PDI générique du panneau (a) de la Figure 1** est un objet différent : une
     illustration autonome, indépendante du produit, d'un **vrai** put down-and-in à
     barrière **continûment observée** (la formule fermée de Bouzoubaa & Osseiran /
     Hull suppose un franchissement à tout instant, pas seulement aux dates
     d'observation du produit). Pour valider cette formule fermée par un Monte Carlo
     indépendant (`src/barrier_options.py::mc_put_down_and_in`), il faut donc que le MC
     lui-même approxime une barrière continue malgré une simulation à pas discret : on
     y applique une **correction de continuité par pont brownien** (probabilité exacte
     de franchissement de la barrière *entre* deux pas de simulation consécutifs,
     sachant les valeurs simulées à ces deux pas — cf. docstring de la fonction),
     conceptuellement proche de l'ajustement Broadie–Glasserman–Kou. **Cette correction
     ne concerne que cette validation MC du panneau (a) ; elle n'intervient nulle part
     dans le pricing du produit autocall lui-même.**
- **Volatilité constante et absence de skew** : tous les sous-jacents (A, B, C) sont
  modélisés sous Black-Scholes avec une volatilité unique et constante (18 %). En
  pratique, un smile/skew de volatilité affecterait différemment les zones proches des
  barrières (rappel comme PDI) ; son absence est une simplification qui **sous-estime
  probablement** l'ampleur des sensibilités mises en évidence dans les Figures 1 et 3.
- **Pas de coûts de transaction ni de frais de gestion** : ni sur la réplication du
  décrément (indices B et C), ni sur le rebalancement **quotidien** de l'indice
  Volatility Target (Figure 3) entre le sous-jacent et le cash. Les mécanismes étudiés
  sont donc présentés dans leur version la plus favorable ; en pratique les coûts
  réduiraient les niveaux de coupon atteignables, et pèseraient d'autant plus sur
  l'indice VT que l'exposition varie fréquemment (justement les phases où le mécanisme
  est le plus actif, cf. Figure 3, sortie 1) — un rebalancement quotidien sans coût est
  une hypothèse particulièrement favorable pour ce mécanisme.
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
