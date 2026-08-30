# Inventaire du repo pour le mémoire

Document de synthèse : ce que le repo peut fournir aujourd'hui, ce qui existe mais
n'est pas exploité, et ce qu'il resterait à produire. Pas de code ici — juste un état
des lieux exploitable pour décider quoi garder, quoi couper, et où investir le temps
qui reste.

---

## 1. Inventaire des sorties graphiques existantes

### `figureA_sensibilites_pdi_autocall.png` (5 panneaux)

| Panneau | Axes / séries | Plage | Ce qu'il démontre |
|---|---|---|---|
| (a) Prix du PDI | x = spot (% niveau initial), y = prix | spot 40→130, courbe unique | Le prix du PDI décroît de ~59 (spot 40) à ~0 (spot 100+) ; niveau du prix pour situer les autres panneaux |
| (b) Delta du PDI | x = spot, y = delta | spot 40→130 | Delta ≈ −0.97 sous la barrière (60), **saut discontinu** à ≈ −2.52 juste au-dessus, puis remonte vers 0. C'est LE panneau qui porte la discontinuité de sensibilité |
| (c) Vega du PDI | x = spot, y = vega (pour 1pt de vol) | spot 40→130, vega ≈0→115 | Vega nul sous la barrière (option déjà "in", devenue put vanille profondément ITM), pic ~115 vers spot 70-75, puis décroît — **jamais négatif** sur toute la grille |
| (d) Vanna du PDI | x = spot, y = vanna | spot 40→130 | Saut à la barrière (≈+15 juste au-dessus), signe qui change ensuite (creux négatif vers spot 80) |
| (e) Vega de l'autocall complet | x = spot (40→130, pas 5), y = vega total (%, pour 1pt de vol), 3 courbes (total, jambe sans PDI, −jambe PDI) | vega total de +48 (spot 40) à −68 (spot 100) puis remonte | Le vega total **change de signe** (zéro à spot≈71.05), contrairement au panneau (c) — démontre l'opposition des deux jambes |

**Redondance avec `RESULTATS.md`** : seuls 3 chiffres du panneau (b) et (e) sont repris en table (delta juste sous/sur la barrière, spot où le vega s'annule). Les courbes complètes (361 points pour a-d, 19 points pour e) ne sont nulle part ailleurs sous forme de table lisible — **ce sont les panneaux qui portent le plus d'information non dupliquée**.

### `figureB_autocall_vs_decrement.png` (4 panneaux, 6 cas : A, B, B′, C, C′, A+dégressive)

| Panneau | Axes / séries | Ce qu'il démontre |
|---|---|---|
| (a) Coupon au pair | x = 6 cas, y = coupon (%), barres | Classement visuel des 6 coupons (6.68% à 26.45%) |
| (b) Distribution des dates de rappel | x = t=1...t=10 + "maturité" (11 groupes), y = probabilité (%), 6 séries de barres groupées | Le décrément (B, C) décale la masse de probabilité vers "maturité" ; la barrière dégressive (A+dégr., C′) la ramène vers les premières dates |
| (c) Probabilité d'activation du PDI | x = 6 cas, y = proba (%), barres | Classement visuel du risque de perte en capital par cas |
| (d) Perte moyenne conditionnelle | x = 6 cas, y = perte (%), barres | Sévérité de la perte quand le PDI est activé, par cas |

**Redondance avec `RESULTATS.md`** : les panneaux (a), (c) et (d) sont **chacun une simple mise en barres d'une colonne déjà présente telle quelle dans la table `RESULTATS.md`** (coupon_pair, proba_pdi_actif, perte_moyenne_cond) — value ajoutée = lisibilité comparative, pas d'information nouvelle. Le panneau (b), en revanche, est **la seule sortie graphique ou tabulaire qui montre la répartition par date** (t1...t10) : le CSV complet a ces colonnes, mais `RESULTATS.md` n'affiche que l'agrégat "proba rappel avant maturité". Si un panneau doit être coupé pour gagner de la place, (a), (c) ou (d) sont les candidats naturels ; (b) est le plus informatif.

### `figureC_volatility_target.png` (3 panneaux)

| Panneau | Axes / séries | Plage | Ce qu'il démontre |
|---|---|---|---|
| Trajectoire type | x = années (0→5), y gauche = niveau (base 100), y droite = exposition e_t (%) ; 3 séries (sous-jacent, indice VT, exposition) | niveau ~80-150, exposition ~35%-150% | L'exposition oscille nettement entre le plafond (150%) en régime calme et ~35-40% en stress, au gré des changements de régime |
| Distribution vol réalisée | x = vol réalisée annualisée de l'indice VT (%), y = nombre de trajectoires (histogramme, 5000 tirages) + ligne cible 15% + ligne moyenne | vol ~12%-21% | La distribution est centrée sur 16.0%, **pas sur la cible 15%** — biais asymétrique vers le haut |
| Scénario V | x = jours (0→185), y = niveau (base 100), 3 courbes (nu, VT 20j, VT 60j) | creux ~64-70, plateau final ~82 | Sur-réaction à la chute (VT tombe sous le nu) puis sous-participation persistante au rebond |

**Redondance avec `RESULTATS.md`** : la moyenne de vol réalisée, la sous-participation (20j/60j) et l'écart en fin de scénario sont repris en table — mais **la forme des courbes** (trajectoire type sur 5 ans, forme de la distribution, dynamique jour par jour du scénario V) n'est disponible nulle part ailleurs que dans le graphique ou le CSV brut (1261 et 187 lignes respectivement). Aucun panneau candidat à la coupe ici : les trois portent une information distincte et aucune n'est un simple doublon de table.

### Synthèse — que couper si besoin de place

Par ordre de "coupable sans perte d'information" : Figure B (a) > Figure B (c)/(d) > rien d'autre. Tous les autres panneaux (Figure A en totalité, Figure B(b), Figure C en totalité) portent une information que aucune table ne reproduit.

---

## 2. Inventaire des sorties chiffrées (CSV / MD)

| Fichier | Colonnes | Reprises dans `RESULTATS.md` ? | Chiffres calculés mais inaccessibles ailleurs qu'au fichier ou au log |
|---|---|---|---|
| `figureA_pdi_formule_fermee.csv` (361 lignes) | spot, prix, delta, vega, vanna | Non (sauf 2 points de delta, cités séparément) | Toute la courbe : ex. le pic de vega (~115, vers spot 72), le creux de vanna (~−5.4 vers spot 80) ne sont cités nulle part en texte |
| `figureA_pdi_formule_fermee_resume.csv` (47 lignes) | idem, sous-échantillon à spots ronds | Non | Table de référence prête à copier (spots 40,50,...,130 + H, K) — jamais citée |
| `figureA_delta_discontinuite.csv` | spot, position, delta | Oui (les 2 valeurs) | — |
| `figureA_spot_zero_vega.csv` | spot_zero_vega, vega_pct, erreur_std_pct | Oui | — |
| `figureA_autocall_vega.csv` (19 lignes) | spot, prix, erreur_std_prix_pct, vega_total_pct, erreur_std_vega_total_pct, vega_leg_sans_pdi_pct, vega_leg_pdi_pct | Non (seul le zéro dérivé séparément) | Le prix de l'autocall par spot (colonne `prix`, ex. 34.46 à spot 40, 108.07 à spot 130) et la décomposition complète des deux jambes par spot ne sont citées nulle part |
| `figureA_validations.csv` (7 lignes) | validation, resultat, reference, ecart_relatif_pct | Non | Les écarts KI+KO (nuls) et l'écart MC vs formule fermée (0.25%) ne figurent plus dans le README depuis sa simplification — disponibles seulement ici |
| `figureB_resultats.csv` (6 lignes) | cas, forward_theorique_10y, coupon_pair_pct, prix_verif_pct, erreur_std_mc_pct, proba_maturite_pct, proba_pdi_actif_pct, perte_moyenne_cond_pct, proba_rappel_t1...t10_pct | Partiellement (6 des ~17 colonnes) | **Les 10 colonnes `proba_rappel_t1...t10`** (probabilité de rappel à *chaque* date d'observation, par cas) ne sont reprises ni en table ni en texte — seul le graphique (b) les montre visuellement |
| `figureC_distribution_vol_realisee.csv` | sigma_cible_pct, vol_realisee_moyenne_pct, vol_realisee_mediane_pct, vol_realisee_ecart_type_pct, proba_dans_plus_ou_moins_2pt_pct | Partiellement (1 des 5) | La **médiane** (16.03%), l'**écart-type** (1.31 pt) et la **probabilité d'être dans ±2pt de la cible** (76%) sont calculés mais ne sont dans aucune table du mémoire |
| `figureC_scenario_v.csv` (187 lignes) | jour, indice_nu, indice_vt_20j, exposition_20j_pct, indice_vt_60j, exposition_60j_pct | Non (le résumé seul l'est) | Le **creux minimal** de l'indice VT pendant la chute (visible dans le graphique, ~64-67 selon la fenêtre) n'est calculé nulle part comme chiffre isolé — il faudrait l'extraire de ce CSV (`.min()`) |
| `figureC_scenario_v_resume.csv` | fenetre_jours, niveau_indice_nu_fin_rebond, niveau_indice_vt_fin_rebond, sous_participation_pts, niveau_indice_vt_fin_episode | Oui (sous_participation + écart fin épisode) | — |
| `figureC_trajectoire_type.csv` (1261 lignes) | annee, indice_sous_jacent, indice_vt, exposition_pct | Non | Aucune statistique de synthèse n'est calculée sur cette trajectoire (ex. % du temps à l'exposition plafond, écart final indice nu vs VT sur 5 ans) — tout est dans le graphique uniquement |

### Chiffres disponibles auxquels tu n'as pas accès aujourd'hui (hors CSV/graphique)

Ce sont des nombres déjà calculés par les scripts, visibles seulement dans les logs de `run_all.py` ou dans les CSV bruts, et absents de tout document de synthèse actuel :

1. **Les 10 probabilités de rappel par date, par cas** (Figure B) — 60 chiffres au total, seulement visualisés, jamais tabulés en dehors du CSV brut.
2. **Validations de la Figure A** (KI+KO=vanille, convergence MC à 0.25%) — disponibles dans `figureA_validations.md` mais plus citées dans le README depuis sa simplification.
3. **Médiane et écart-type de la vol réalisée VT**, et **probabilité d'être proche de la cible** (Figure C).
4. **Le creux exact de l'indice VT pendant le scénario V** (utile pour quantifier l'effet de sur-exposition avant le choc, actuellement seulement qualitatif dans le texte).
5. **Le prix complet de l'autocall par spot** (panneau e de la Figure A) — seule la localisation du zéro de vega est citée, pas le niveau de prix associé.

---

## 3. Le gisement inexploité : le notebook d'origine

Vérification technique effectuée dans cette session (exécution complète du notebook,
19 cellules de code) : le notebook est **totalement indépendant de `src/`** (aucun
`import` depuis les modules refactorés — il redéfinit ses propres fonctions), donc le
refactor n'a **aucun impact** dessus. En revanche, il contient **2 bugs de dérive de
version de bibliothèque**, tous les deux triviaux à corriger :

- Cellule 45 (`simuler_delta_hedging`) : `float(interp(...))` échoue sous NumPy 2.x
  (`TypeError: only 0-dimensional arrays can be converted to Python scalars`) —
  NumPy a durci le comportement de `float()` sur un array à un seul élément. Correctif :
  `float(interp(...)[0])`.
- Cellule 56 (boxplot de synthèse) : `ax.boxplot(..., labels=...)` échoue sous
  Matplotlib récent (le paramètre a été renommé `tick_labels`). Correctif : renommer
  le paramètre.

**Ces deux corrections suffisent** : le notebook complet (100 000 trajectoires pour le
pricer principal, grille de delta, 1 100 simulations de hedging) s'exécute alors de
bout en bout sans erreur, en **4 min 43 s** dans cet environnement. Tous les résultats
ci-dessous ont été obtenus par cette exécution réelle (pas des valeurs de mémoire).

**Point d'attention important** : le produit utilisé par le notebook est **différent**
de celui des 3 figures du mémoire — maturité 5 ans (pas 10), coupon fixe à 7% (pas
résolu au pair), volatilité 20% (pas 18%), pas de dividende `q`. Les chiffres ci-dessous
illustrent la mécanique, mais ne sont pas directement comparables aux résultats de
Figure B.

### 3.1 Delta hedging — PnL principal

**Ce qu'elle produit** : simule 500 trajectoires de delta hedging (rebalancement tous
les 5 jours, delta interpolé sur une grille pré-calculée 40 pas de temps × 25 pas de
spot) et calcule la distribution du PnL de couverture.

**Résultat obtenu** : PnL moyen = **+0.51** (nominal 100), écart-type = **5.87**,
min/max = **[−23.86 ; +45.72]**. PnL centré près de zéro (couverture non biaisée) mais
dispersion large — cohérent avec un produit à payoff discontinu.

**Exécutable en l'état** : oui, après le correctif d'une ligne ci-dessus.

**Effort pour figure propre (sur le produit du notebook)** : faible — reformatage aux
standards du repo (style, 300 dpi, labels déjà en français, export CSV/MD des
statistiques). Quelques heures.

**Effort pour la porter sur le produit du mémoire** (10 ans, coupon au pair, avec `q`,
éventuellement comparée entre indices A/B/C) : plus substantiel — il faut reconstruire
la grille de delta et le simulateur de hedging pour qu'ils utilisent la convention de
payoff et les paramètres actuels de `src/pricer_autocall.py` (le calcul du delta par
bump-and-reprice existe déjà en embryon dans `figA_sensibilites_pdi_autocall.py`
pour le vega — le même principe s'applique au delta, mais la boucle de simulation du
hedging path-dépendant avec rebalancement est un module entièrement nouveau). Ordre de
grandeur : comparable à la construction d'une des 3 figures existantes (nouveau module
`src/`, script, tests, CSV) — pas une extension à coût marginal nul.

### 3.2 PnL par fréquence de rebalancement

**Ce qu'elle produit** : le même hedging que 3.1, répété pour 4 fréquences de
rebalancement (1, 5, 10, 20 jours), 300 simulations chacune.

**Résultat obtenu** :

| Fréquence | PnL moyen | Écart-type |
|---|---|---|
| 1 jour | +0.23 | 5.83 |
| 5 jours | +0.39 | 5.96 |
| 10 jours | +0.36 | 6.10 |
| 20 jours | +0.19 | 5.89 |

L'écart-type est **quasiment plat** entre 1 et 20 jours de fréquence — augmenter la
fréquence de rebalancement n'améliore quasiment pas la couverture. C'est un résultat
quantitatif directement exploitable pour III.2 : le risque résiduel du hedging vient
des discontinuités de payoff aux barrières (gap risk), pas de la granularité du
rebalancement.

**Exécutable en l'état / effort** : identique à 3.1 (même infrastructure).

### 3.3 Mismatch volatilité réalisée vs volatilité de couverture

**Ce qu'elle produit** : hedging avec une grille de delta calculée à vol modèle 20%,
appliquée à des trajectoires simulées à vol réalisée 15%, 20%, 25%, 30% (300
simulations chacune) — teste l'impact d'une mauvaise estimation de la vol par le
trader.

**Résultat obtenu** :

| Vol réalisée | PnL moyen | Écart-type |
|---|---|---|
| 15% | −2.15 | 5.98 |
| 20% (= vol modèle) | +1.61 | 7.07 |
| 25% | +4.69 | 8.01 |
| 30% | +7.88 | 10.15 |

Relation quasi linéaire et monotone entre vol réalisée et PnL moyen, cohérente avec
`PnL ≈ ½Γ(σ_réal² − σ_modèle²)` — c'est **la meilleure figure candidate pour III.2** :
elle quantifie directement le risque de gamma/vol résiduel non couvert par le delta
hedging, avec un lien explicite à la formule théorique.

**Exécutable en l'état / effort** : identique à 3.1/3.2.

### 3.4 Taux stochastiques (Vasicek)

**Ce qu'elle produit** : compare le prix et la probabilité d'autocall sous taux
constant vs modèle de Vasicek (`a=0.5, b=3%, σ_r=1%, ρ=−0.2`), puis fait varier `σ_r`
(5 valeurs, 0.5% à 5%) et `ρ` (7 valeurs, −0.5 à +0.5).

**Résultat obtenu** : écart de prix taux constant vs Vasicek = **4.6 bps** (quasi
négligeable) ; sensibilité à `σ_r` de 6.4 à 19.2 bps sur la plage testée ; sensibilité à
`ρ` de −0.0796 (ρ=−0.5) à −0.0011 (ρ=+0.5) en écart au prix de référence — la
corrélation spot/taux a plus d'impact que la vol du taux elle-même.

**Exécutable en l'état** : oui, sans aucun correctif — cette section n'est **pas**
affectée par les 2 bugs (qui n'apparaissent qu'en cellule 45, section hedging).

**Effort pour figure propre** : faible, même remarque que 3.1 (reformatage seul). Hors
sujet direct des sections III.1-III.3 identifiées, mais mobilisable si le mémoire
aborde la robustesse de l'hypothèse de taux constant.

### 3.5 Grille de delta pré-calculée

**Ce qu'elle produit** : une heatmap delta(temps, spot) sur une grille 40×25,
construite en 1.1 s, qui sert d'input à 3.1-3.3.

**Résultat obtenu** : delta fortement instable près des deux barrières (100% et 60%),
confirmé visuellement (carte de chaleur avec fortes variations locales) — utile comme
figure d'appui pour expliquer *pourquoi* le hedging est difficile, avant de montrer le
PnL qui en résulte.

**Exécutable en l'état** : oui.

**Effort pour figure propre** : faible sur le produit du notebook ; nécessite la même
reconstruction que 3.1 si portée sur le produit du mémoire.

---

## 4. Ce qui serait peu coûteux à ajouter

Classement par rapport effort/intérêt, en réutilisant uniquement les briques déjà en
place (`simuler_indices`, `pricer_autocall`, `coupon_solver`, `barrier_options`,
`vol_target`) — aucun nouveau moteur de simulation.

| Idée | Effort | Intérêt pour le mémoire | Verdict |
|---|---|---|---|
| **Vega/delta de l'autocall à plusieurs maturités résiduelles** (rejouer le panneau (e) de la Figure A en tronquant `dates_obs`, ex. 10 ans à l'origine vs 5 ans vs 1 an restant) | Faible — boucle autour du code déjà écrit | Élevé — démontre explicitement le point non montré à ce jour : le vega change de signe *aussi* selon la maturité résiduelle (mentionné dans le README mais jamais illustré) | **À faire** |
| **Sensibilité du coupon au pair (cas A/B/C) à σ et r** (reboucler `coupon_solver` + `simuler_indices` sur une grille de volatilités/taux) | Faible-moyen — code identique, juste répété sur une grille de paramètres marché ; coût de calcul cumulé notable (chaque point ≈ 50s à pleine précision, réductible avec moins de trajectoires pour une sensibilité) | Moyen-élevé — robustesse de la thèse de la Figure B face à l'hypothèse de marché | **À faire si le temps le permet** |
| **Sensibilité du coupon à la pente/plancher de la barrière dégressive** (reboucler `barriere_degressive` + `coupon_solver`) | Faible | Moyen — approfondit la comparaison C′ vs A+dégressive déjà présente | Optionnel |
| **PDI fermé à plusieurs maturités** (courbes delta/vega du panneau (a)-(d) pour T=0.5/1/2/5 ans) | Faible — un paramètre à boucler dans `pdi_grecques` | Moyen — illustre la structure par terme des sensibilités du PDI | Optionnel |
| **Sensibilité de l'indice C au paramètre K** (décrément en points) | Faible | Moyen — approfondit le point de vigilance déjà démontré (K=5 donne un coupon extrême) | Optionnel |
| **Sensibilité de l'indice VT à σ_cible et L_max** (rejouer sortie 2/3 de la Figure C avec d'autres valeurs) | Faible-moyen | Moyen — renforce III.3.2 (le biais dépend des paramètres de construction, pas seulement du mécanisme) | Optionnel |
| **Statistique de synthèse manquantes du §2** (creux du scénario V, % de temps au plafond L_max sur la trajectoire type, médiane/écart-type de la vol réalisée) | Très faible — extraction directe des CSV déjà produits, aucune nouvelle simulation | Faible-moyen — complète `RESULTATS.md` sans nouveau calcul | **À faire, c'est gratuit** |
| **Delta hedging sur le produit du mémoire** (cf. §3.1) | Élevé — nouveau module de simulation path-dépendante | Élevé — répond directement à III.2 | Voir §3, ce n'est pas "peu coûteux" |
| **Modèle de smile / skew de volatilité** | Élevé — nouveau moteur (vol locale ou stochastique calibrée) | — | **Pas rentable** dans le temps restant |
| **Produit worst-of multi-actifs** | Élevé — nouveau moteur (corrélation, plusieurs sous-jacents) | — | **Pas rentable** |
| **Pricer EDP** | Élevé — nouvelle méthode numérique complète | Faible (le MC suffit à démontrer les points du mémoire) | **Pas rentable** |

---

## 5. Tableau de correspondance final

| Élément disponible | Ce qu'il démontre | Section du mémoire | Statut |
|---|---|---|---|
| Figure A, panneaux (a)-(d) — PDI fermé | Discontinuité de delta/vanna à la barrière ; vega de signe constant | III.1.1 | **Exploité** |
| Figure A, panneau (e) — vega autocall | Vega change de signe (jambes opposées) | III.1.1 | **Exploité** |
| `figureA_validations.csv` (KI+KO, convergence MC) | Rigueur de la formule fermée | III.1.1 (annexe méthodo) | Disponible, non cité dans le README actuel |
| Vega/delta à plusieurs maturités résiduelles | Le vega change de signe *aussi* selon la maturité | III.1.1 | À produire (effort faible, §4) |
| Figure B, panneaux (a)(c)(d) — coupon, PDI, perte | Classement des 6 cas | III.1.3 | **Exploité** (redondant avec `RESULTATS.md`) |
| Figure B, panneau (b) — dates de rappel | Le décrément retarde le rappel | III.1.3 | **Exploité** |
| Colonnes `proba_rappel_t1...t10` | Détail par date, par cas | III.1.3 | Disponible, non tabulé (§2) |
| Sensibilité coupon à σ/r | Robustesse de la thèse décrément | III.1.3 | À produire (effort moyen, §4) |
| Delta hedging PnL (notebook, produit 5 ans) | Couverture non biaisée mais dispersée | III.2 | Disponible après correctif 1 ligne, produit non conforme au mémoire |
| PnL vs fréquence de rebalancement | Fréquence ≈ sans effet, le gap risk domine | III.2 | Disponible après correctif 1 ligne, idem |
| PnL vs vol réalisée (mismatch) | `PnL ≈ ½Γ(σ_réal²−σ_modèle²)`, quantifié | III.2 | Disponible après correctif 1 ligne, idem — **meilleur candidat pour III.2** |
| Grille de delta (heatmap) | Delta instable près des barrières | III.2 | Disponible après correctif, idem |
| Delta hedging sur le produit du mémoire (10 ans, coupon au pair) | Idem, mais chiffres directement comparables à Figure B | III.2 | **À produire, effort élevé** (§3.1) |
| Figure C, trajectoire type | Exposition oscille entre plafond et désensibilisation | III.3.1 | **Exploité** |
| Figure C, scénario V | Sur-réaction à la chute + sous-participation au rebond | III.3.1 | **Exploité** |
| Creux exact du scénario V | Quantifie la sur-exposition avant le choc | III.3.1 | Disponible, non calculé comme chiffre isolé (§2, effort quasi nul) |
| Figure C, distribution vol réalisée | La vol réalisée VT ≠ la cible, biais asymétrique | III.3.2 | **Exploité** |
| Médiane / écart-type / proba ±2pt de la distribution | Précision du biais | III.3.2 | Disponible, non tabulé (§2, effort quasi nul) |
| Sensibilité VT à σ_cible / L_max | Le biais dépend des paramètres de construction | III.3.2 | À produire (effort faible-moyen, §4) |
