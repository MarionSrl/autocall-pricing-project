# Inventaire du repo pour le mémoire

Document de synthèse : ce que le repo peut fournir aujourd'hui, ce qui existe mais
n'est pas exploité, et ce qu'il resterait à produire. Pas de code ici — juste un état
des lieux exploitable pour décider quoi garder, quoi couper, et où investir le temps
qui reste.

---

## 1. Inventaire des sorties graphiques existantes

### `figureA_sensibilites_pdi_autocall.png` (4 panneaux)

Fusionnée depuis la version à 5 panneaux (prix et vega du PDI étaient deux
panneaux séparés) à la demande explicite de l'utilisatrice, une fois le
panneau vanna confirmé comme cité dans le mémoire (III.1.1, changement de
signe au voisinage de 73 % et lien avec le forward) — donc conservé, pas coupé.

| Panneau | Axes / séries | Plage | Ce qu'il démontre |
|---|---|---|---|
| (a) Prix + vega du PDI (deux échelles) | x = spot (% niveau initial), y gauche = prix, y droite = vega (pour 1pt de vol) | prix ~59→0, vega ≈0→1.15 | Le prix du PDI décroît de ~59 (spot 40) à ~0 (spot 100+) ; le vega, nul sous la barrière (option déjà "in", devenue put vanille profondément ITM), culmine ~1.15 vers spot 70-75 puis décroît — **jamais négatif** sur toute la grille |
| (b) Delta du PDI | x = spot, y = delta | spot 40→130 | Delta ≈ −0.97 sous la barrière (60), **saut discontinu** à ≈ −2.52 juste au-dessus, puis remonte vers 0. C'est LE panneau qui porte la discontinuité de sensibilité |
| (c) Vanna du PDI | x = spot, y = vanna | spot 40→130 | Saut à la barrière (≈+0.15 juste au-dessus), signe qui change ensuite (creux négatif vers spot 80) |
| (d) Vega de l'autocall complet | x = spot (40→130, pas 5), y = vega total (%, pour 1pt de vol), 3 courbes (total, jambe sans PDI, −jambe PDI) | vega total de +0.48 (spot 40) à −0.68 (spot 100) puis remonte | Le vega total **change de signe** (zéro à spot≈71.05), contrairement au panneau (a) — démontre l'opposition des deux jambes |

**Redondance avec `RESULTATS.md`** : seuls le delta juste sous/sur la barrière, le spot où le vega s'annule, et les deux validations de la formule fermée (parité KI+KO, convergence MC) sont repris en table. Les courbes complètes (361 points pour a-c, 19 points pour d) ne sont nulle part ailleurs sous forme de table lisible — **ce sont les panneaux qui portent le plus d'information non dupliquée**.

### `figureB_autocall_vs_decrement.png` (3 panneaux, 6 cas : A, B, B′, C, C′, A+dégressive)

Fusionnée depuis la version à 4 panneaux (probabilité PDI et perte
conditionnelle étaient deux panneaux séparés) à la demande explicite de
l'utilisatrice — barres groupées sur un axe de pourcentage partagé (les deux
grandeurs sont déjà des %, un double axe aurait été moins honnête qu'un axe
commun).

| Panneau | Axes / séries | Ce qu'il démontre |
|---|---|---|
| (a) Coupon au pair | x = 6 cas, y = coupon (%), barres | Classement visuel des 6 coupons (6.68% à 26.45%) |
| (b) Distribution des dates de rappel | x = t=1...t=10 + "maturité" (11 groupes), y = probabilité (%), 6 séries de barres groupées | Le décrément (B, C) décale la masse de probabilité vers "maturité" ; la barrière dégressive (A+dégr., C′) la ramène vers les premières dates |
| (c) Risque : probabilité d'activation du PDI + perte moyenne conditionnelle | x = 6 cas, y = pourcentage, barres groupées (2 séries) | Le décrément augmente aussi le risque de perte en capital (9.1%→31.8% de probabilité) et sa sévérité (58.6%→79.3% de perte conditionnelle) — la hausse de coupon n'est pas gratuite |

**Redondance avec `RESULTATS.md`** : les panneaux (a) et (c) sont **chacun une mise en barres de colonnes déjà présentes telles quelles dans la table `RESULTATS.md`** (coupon_pair, proba_pdi_actif, perte_moyenne_cond) — valeur ajoutée = lisibilité comparative, pas d'information nouvelle. Le panneau (b), en revanche, est **la seule sortie graphique ou tabulaire qui montre la répartition par date** (t1...t10) : le CSV complet a ces colonnes, mais `RESULTATS.md` n'affiche que l'agrégat "proba rappel avant maturité".

### `figureC_volatility_target.png` (3 panneaux)

| Panneau | Axes / séries | Plage | Ce qu'il démontre |
|---|---|---|---|
| Trajectoire type | x = années (0→5), y gauche = niveau (base 100), y droite = exposition e_t (%) ; 3 séries (sous-jacent, indice VT, exposition) | niveau ~80-150, exposition ~35%-150% | L'exposition oscille nettement entre le plafond (150%) en régime calme et ~35-40% en stress, au gré des changements de régime |
| Distribution vol réalisée | x = vol réalisée annualisée de l'indice VT (%), y = nombre de trajectoires (histogramme, 5000 tirages) + ligne cible 15% + ligne moyenne | vol ~12%-21% | La distribution est centrée sur 16.0%, **pas sur la cible 15%** — biais asymétrique vers le haut |
| Scénario V | x = jours (0→185), y = niveau (base 100), 3 courbes (nu, VT 20j, VT 60j) | creux ~64-70, plateau final ~82 | Sur-réaction à la chute (VT tombe sous le nu) puis sous-participation persistante au rebond |

**Redondance avec `RESULTATS.md`** : la moyenne de vol réalisée, la sous-participation (20j/60j) et l'écart en fin de scénario sont repris en table — mais **la forme des courbes** (trajectoire type sur 5 ans, forme de la distribution, dynamique jour par jour du scénario V) n'est disponible nulle part ailleurs que dans le graphique ou le CSV brut (1261 et 187 lignes respectivement). Aucun panneau candidat à la coupe ici : les trois portent une information distincte et aucune n'est un simple doublon de table.

### `figureD_hedging.png` (2 panneaux) — ajoutée depuis la première version de cet inventaire

| Panneau | Axes / séries | Plage | Ce qu'il démontre |
|---|---|---|---|
| (a) PnL vs vol réalisée | x = vol réalisée (%), y = PnL de couverture (base nominal 100) ; points empiriques ± erreur std + courbe théorique de gamma-trading | vol 15→30%, PnL −2.5→+8.3 | Le PnL de couverture croît avec l'écart entre vol réalisée et vol modèle (20%), et la prédiction théorique reproduit le signe et l'ordre de grandeur (validation quantitative, pas seulement qualitative) |
| (b) Dispersion PnL vs fréquence | x = fréquence de rebalancement (1j/5j/10j/20j), y = PnL de couverture, boxplot (2000 trajectoires chacun) | médiane et IQR quasi identiques d'une fréquence à l'autre | Confirme le résultat du notebook : la dispersion ne se réduit quasiment pas avec un rebalancement plus fréquent — le risque résiduel vient des discontinuités de payoff (gap risk), pas de la granularité |

**Redondance avec `RESULTATS.md`** : le gamma moyen, le temps de sortie moyen, et les 4+4 points (PnL moyen par vol/fréquence) sont repris en table. Les courbes/distributions complètes (grille delta/gamma 40×25×3, 2000 trajectoires brutes par scénario) ne le sont pas — cohérent avec le reste du repo, aucune redondance à signaler.

**Porte sur un produit distinct** (5 ans, coupon fixe 7%, vol modèle 20%, sans dividende) des Figures A-C (10 ans, coupon au pair, q=3%) — voir le README pour la justification. Les niveaux de PnL ne sont donc pas directement comparables aux coupons de la Figure B.

### Synthèse — que couper si besoin de place

Les deux fusions à faible coût identifiées ont été appliquées à la demande de l'utilisatrice : Figure A (prix+vega du PDI sur un même panneau à deux échelles, 5→4 panneaux) et Figure B (probabilité PDI + perte conditionnelle en barres groupées, 4→3 panneaux). Le vanna (Figure A) est conservé : cité dans le mémoire (III.1.1). Au-delà de ces deux fusions déjà faites, aucun panneau restant n'est identifié comme candidat à la coupe : chacun porte une information que aucune table ne reproduit.

---

## 2. Inventaire des sorties chiffrées (CSV / MD)

| Fichier | Colonnes | Reprises dans `RESULTATS.md` ? | Chiffres calculés mais inaccessibles ailleurs qu'au fichier ou au log |
|---|---|---|---|
| `figureA_pdi_formule_fermee.csv` (361 lignes) | spot, prix, delta, vega, vanna | Non (sauf 2 points de delta, cités séparément) | Toute la courbe : ex. le pic de vega (~1.15, vers spot 72), le creux de vanna (~−0.056 vers spot 80) ne sont cités nulle part en texte |
| `figureA_pdi_formule_fermee_resume.csv` (47 lignes) | idem, sous-échantillon à spots ronds | Non | Table de référence prête à copier (spots 40,50,...,130 + H, K) — jamais citée |
| `figureA_delta_discontinuite.csv` | spot, position, delta | Oui (les 2 valeurs) | — |
| `figureA_spot_zero_vega.csv` | spot_zero_vega, vega_pct, erreur_std_pct | Oui | — |
| `figureA_autocall_vega.csv` (19 lignes) | spot, prix, erreur_std_prix_pct, vega_total_pct, erreur_std_vega_total_pct, vega_leg_sans_pdi_pct, vega_leg_pdi_pct | Non (seul le zéro dérivé séparément) | Le prix de l'autocall par spot (colonne `prix`, ex. 34.46 à spot 40, 108.07 à spot 130) et la décomposition complète des deux jambes par spot ne sont citées nulle part |
| `figureA_validations.csv` (7 lignes) | validation, resultat, reference, ecart_relatif_pct | Oui (résumé : écart max parité KI+KO, écart MC vs formule fermée) | Le détail des 6 écarts de parité individuels (tous nuls) reste seulement dans ce fichier — RESULTATS.md n'en cite que le max |
| `figureB_resultats.csv` (6 lignes) | cas, forward_theorique_10y, coupon_pair_pct, prix_verif_pct, erreur_std_mc_pct, proba_maturite_pct, proba_pdi_actif_pct, perte_moyenne_cond_pct, proba_rappel_t1...t10_pct | Partiellement (6 des ~17 colonnes) | **Les 10 colonnes `proba_rappel_t1...t10`** (probabilité de rappel à *chaque* date d'observation, par cas) ne sont reprises ni en table ni en texte — seul le graphique (b) les montre visuellement |
| `figureC_distribution_vol_realisee.csv` | sigma_cible_pct, vol_realisee_moyenne_pct, vol_realisee_mediane_pct, vol_realisee_ecart_type_pct, proba_dans_plus_ou_moins_2pt_pct | Oui (5 des 5) | — |
| `figureC_scenario_v.csv` (187 lignes) | jour, indice_nu, indice_vt_20j, exposition_20j_pct, indice_vt_60j, exposition_60j_pct | Non (le résumé seul l'est) | La trajectoire jour par jour reste seulement dans ce fichier / le graphique — le creux (niveau_plancher_*) est désormais calculé dans `figureC_scenario_v_resume.csv` et cité |
| `figureC_scenario_v_resume.csv` | fenetre_jours, niveau_indice_nu_fin_rebond, niveau_indice_vt_fin_rebond, sous_participation_pts, niveau_indice_vt_fin_episode, niveau_plancher_indice_nu, niveau_plancher_indice_vt | Oui (sous_participation, écart fin épisode, et désormais les 2 planchers) | — |
| `figureC_trajectoire_type.csv` (1261 lignes) | annee, indice_sous_jacent, indice_vt, exposition_pct | Non | La trajectoire jour par jour reste seulement dans ce fichier / le graphique — le % de temps au plafond est désormais calculé dans `figureC_trajectoire_type_resume.csv` et cité ; l'écart final indice nu vs VT n'est pas repris (chiffre à un seul chemin, moins généralisable que les moyennes de la sortie 2) |
| `figureC_trajectoire_type_resume.csv` (nouveau) | pct_temps_exposition_plafond | Oui | — |
| `figureD_pnl_vs_vol_realisee.csv` (4 lignes) | vol_realisee_pct, pnl_moyen, pnl_erreur_std, nb_trajectoires, pnl_theorique | Oui (pnl_moyen, pnl_erreur_std, pnl_theorique) | — |
| `figureD_resume.csv` | gamma_moyen_dollar, gamma_s2_moyen, temps_sortie_moyen_annees, prix_initial_pct, nb_trajectoires_grille_delta, nb_trajectoires_couverture_par_scenario, coupon_pct, maturite_annees, vol_modele_pct | Oui (gamma_moyen_dollar, gamma_s2_moyen, temps_sortie_moyen_annees, prix_initial_pct, les 2 nb_trajectoires) | — |
| `figureD_pnl_vs_frequence.csv` (4 lignes) | freq_rebal_jours, pnl_moyen, pnl_ecart_type, pnl_erreur_std, nb_trajectoires | Oui (pnl_moyen, pnl_ecart_type, pnl_erreur_std) | — |
| `figureD_pnl_vs_frequence_brut.csv` (8000 lignes) | freq_rebal_jours, pnl | Non (résumé seul) | La distribution complète (asymétrie, queues épaisses visibles sur le boxplot) n'est décrite que visuellement, jamais quantifiée (skewness, quantiles) |

### Chiffres disponibles auxquels tu n'as pas accès aujourd'hui (hors CSV/graphique)

Ce sont des nombres déjà calculés par les scripts, visibles seulement dans les logs de `run_all.py` ou dans les CSV bruts, et absents de tout document de synthèse actuel :

1. **Les 10 probabilités de rappel par date, par cas** (Figure B) — 60 chiffres au total, seulement visualisés, jamais tabulés en dehors du CSV brut.
2. **Le prix complet de l'autocall par spot** (panneau d de la Figure A) — seule la localisation du zéro de vega est citée, pas le niveau de prix associé.

Les autres éléments listés dans une version antérieure de cet inventaire (validations de la Figure A, médiane/écart-type/proba ±2pt de la vol réalisée VT, creux du scénario V, % de temps à l'exposition plafond, `gamma_s2_moyen`, erreurs std du PnL de la Figure D) sont désormais dans `RESULTATS.md`.

---

## 3. Le gisement du notebook d'origine — état après intervention

Vérification technique effectuée dans une session antérieure (exécution complète du
notebook, 19 cellules de code) : le notebook est **totalement indépendant de `src/`**
(aucun `import` depuis les modules refactorés — il redéfinit ses propres fonctions),
donc le refactor n'a **aucun impact** dessus. Il contenait **2 bugs de dérive de
version de bibliothèque, tous les deux corrigés depuis** (voir le commit sur
`notebooks/Pricer_Autocall_MC.ipynb`) :

- Cellule 45 (`simuler_delta_hedging`) : `float(interp(...))` échouait sous NumPy 2.x
  (`TypeError: only 0-dimensional arrays can be converted to Python scalars`).
  **Corrigé** : `float(interp(...)[0])`.
- Cellule 56 (boxplot de synthèse) : `ax.boxplot(..., labels=...)` échouait sous
  Matplotlib récent (paramètre renommé `tick_labels`). **Corrigé**.

Le notebook complet (100 000 trajectoires pour le pricer principal, grille de delta,
1 100 simulations de hedging) s'exécute désormais de bout en bout sans erreur, en
4 min 43 s.

**Point d'attention important, toujours valable** : le produit utilisé par le notebook
est **différent** de celui des Figures A-C — maturité 5 ans (pas 10), coupon fixe à 7%
(pas résolu au pair), volatilité 20% (pas 18%), pas de dividende `q`.

**Mise à jour majeure : les sections 3.1 à 3.3 sont maintenant exploitées.** Plutôt que
de laisser ces analyses dans le notebook, elles ont été portées en module réutilisable
(`src/delta_hedging.py` : grille delta/gamma par bump-and-reprice réutilisant
`pricer_autocall`, simulateur de couverture path-dépendant) et publiées comme
**Figure D** (`figD_hedging_produit_notebook.py`, panneaux "PnL vs vol réalisée +
prédiction théorique" et "dispersion PnL vs fréquence de rebalancement"), sur le
produit du notebook (le choix de ne pas porter vers le produit à 10 ans est resté celui
retenu — voir le README). Les résultats ci-dessous sont ceux de la Figure D (seed
globale, 2000 trajectoires par scénario, donc légèrement différents des premiers essais
notebook à 300-500 trajectoires et seed locale, mais du même ordre de grandeur).

### 3.1 Delta hedging — PnL principal — **exploité (Figure D)**

**Résultat obtenu (Figure D, scénario de référence vol=20%=modèle, freq=5j, 2000
trajectoires)** : PnL moyen = **+1.16**, cohérent avec une couverture non biaisée. La
grille de delta/gamma sous-jacente (25 spots × 40 temps × 3 évaluations bump-reprice)
est construite en ~3.5s en réutilisant `pricer_autocall`.

### 3.2 PnL par fréquence de rebalancement — **exploité (Figure D, panneau b)**

**Résultat obtenu** :

| Fréquence | PnL moyen | Écart-type |
|---|---|---|
| 1 jour | +0.93 | 7.68 |
| 5 jours | +0.84 | 7.50 |
| 10 jours | +1.29 | 8.05 |
| 20 jours | +1.19 | 8.22 |

Écart-type quasiment plat entre 1 et 20 jours — confirmé avec 2000 trajectoires par
fréquence (vs 300 dans le notebook d'origine) : le risque résiduel du hedging vient des
discontinuités de payoff aux barrières (gap risk), pas de la granularité du
rebalancement.

### 3.3 Mismatch volatilité réalisée vs volatilité de couverture — **exploité (Figure D, panneau a)**

**Résultat obtenu, avec prédiction théorique superposée** (voir `src/delta_hedging.py`
pour la convention de signe — un hedger qui vend le produit et couvre au delta modèle
est *short gamma*, la formule correcte est
`dPnL ≈ ½·gamma_$·S²·(σ_modèle² − σ_réalisée²)·dt`, et non l'inverse comme souvent
écrit de façon informelle pour un acheteur d'option) :

| Vol réalisée | PnL moyen (simulé) | PnL théorique |
|---|---|---|
| 15% | −2.52 | −3.94 |
| 20% (= vol modèle) | +1.16 | ≈0 |
| 25% | +5.02 | +5.07 |
| 30% | +8.34 | +11.27 |

La prédiction théorique reproduit le signe sur toute la plage et l'ordre de grandeur
(quasi exact à 25%, sur-estimé d'environ 35% à 30% — attendu, la formule est une
approximation au premier ordre qui ignore la path-dépendance et les sorties anticipées
propres à un autocall). **C'est la validation quantitative demandée pour III.2.**

### 3.4 Taux stochastiques (Vasicek) — toujours inexploité

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

### 3.5 Grille de delta (et désormais gamma) pré-calculée — **portée dans `src/delta_hedging.py`, pas encore affichée en heatmap**

La grille existe et est utilisée en interne par la Figure D (`construire_grille_delta_gamma`,
25 spots × 40 temps, delta ET gamma désormais, ~3.5s), mais n'est pas exposée comme
panneau visuel indépendant (contrairement au notebook qui en fait une figure à part,
cellule 43). **Reste à faire, effort très faible** (les données existent déjà, il ne
manque qu'un `pcolormesh` + export CSV) si une heatmap delta/gamma(temps, spot) s'avère
utile en illustration d'appui pour expliquer visuellement *pourquoi* le hedging est
difficile près des barrières, avant de montrer le PnL qui en résulte.

---

## 4. Ce qui serait peu coûteux à ajouter

Classement par rapport effort/intérêt, en réutilisant uniquement les briques déjà en
place (`simuler_indices`, `pricer_autocall`, `coupon_solver`, `barrier_options`,
`vol_target`) — aucun nouveau moteur de simulation.

| Idée | Effort | Intérêt pour le mémoire | Verdict |
|---|---|---|---|
| **Vega/delta de l'autocall à plusieurs maturités résiduelles** (rejouer le panneau (d) de la Figure A en tronquant `dates_obs`, ex. 10 ans à l'origine vs 5 ans vs 1 an restant) | Faible — boucle autour du code déjà écrit | Élevé — démontre explicitement le point non montré à ce jour : le vega change de signe *aussi* selon la maturité résiduelle (mentionné dans le README mais jamais illustré) | **À faire** |
| **Sensibilité du coupon au pair (cas A/B/C) à σ et r** (reboucler `coupon_solver` + `simuler_indices` sur une grille de volatilités/taux) | Faible-moyen — code identique, juste répété sur une grille de paramètres marché ; coût de calcul cumulé notable (chaque point ≈ 50s à pleine précision, réductible avec moins de trajectoires pour une sensibilité) | Moyen-élevé — robustesse de la thèse de la Figure B face à l'hypothèse de marché | **À faire si le temps le permet** |
| **Sensibilité du coupon à la pente/plancher de la barrière dégressive** (reboucler `barriere_degressive` + `coupon_solver`) | Faible | Moyen — approfondit la comparaison C′ vs A+dégressive déjà présente | Optionnel |
| **PDI fermé à plusieurs maturités** (courbes prix/delta/vega/vanna du panneau (a)-(c) pour T=0.5/1/2/5 ans) | Faible — un paramètre à boucler dans `pdi_grecques` | Moyen — illustre la structure par terme des sensibilités du PDI | Optionnel |
| **Sensibilité de l'indice C au paramètre K** (décrément en points) | Faible | Moyen — approfondit le point de vigilance déjà démontré (K=5 donne un coupon extrême) | Optionnel |
| **Sensibilité de l'indice VT à σ_cible et L_max** (rejouer sortie 2/3 de la Figure C avec d'autres valeurs) | Faible-moyen | Moyen — renforce III.3.2 (le biais dépend des paramètres de construction, pas seulement du mécanisme) | Optionnel |
| ~~Statistique de synthèse manquantes du §2~~ (creux du scénario V, % de temps au plafond L_max sur la trajectoire type, médiane/écart-type de la vol réalisée) | Très faible | Faible-moyen | **Fait** — dans `RESULTATS.md` |
| **Heatmap delta/gamma(temps, spot)** (les grilles existent déjà dans `src/delta_hedging.py`, juste jamais tracées) | Très faible — `pcolormesh` + CSV, aucune nouvelle simulation | Faible-moyen — illustration d'appui pour la Figure D, pas indispensable | **À faire si le temps le permet, c'est presque gratuit** |
| **Delta hedging sur le produit du mémoire (10 ans, coupon au pair)** (porter `src/delta_hedging.py` du produit notebook vers `src/pricer_autocall.py`) | Élevé — même module réutilisable, mais nouvelle grille + nouvelles simulations de couverture à faire tourner et valider | Élevé — chiffres directement comparables aux coupons de la Figure B | Reste "non peu coûteux" malgré la Figure D — voir §3 |
| **Modèle de smile / skew de volatilité** | Élevé — nouveau moteur (vol locale ou stochastique calibrée) | — | **Pas rentable** dans le temps restant |
| **Produit worst-of multi-actifs** | Élevé — nouveau moteur (corrélation, plusieurs sous-jacents) | — | **Pas rentable** |
| **Pricer EDP** | Élevé — nouvelle méthode numérique complète | Faible (le MC suffit à démontrer les points du mémoire) | **Pas rentable** |

---

## 5. Tableau de correspondance final

| Élément disponible | Ce qu'il démontre | Section du mémoire | Statut |
|---|---|---|---|
| Figure A, panneaux (a)-(d) — PDI fermé | Discontinuité de delta/vanna à la barrière ; vega de signe constant | III.1.1 | **Exploité** |
| Figure A, panneau (d) — vega autocall | Vega change de signe (jambes opposées) | III.1.1 | **Exploité** |
| `figureA_validations.csv` (KI+KO, convergence MC) | Rigueur de la formule fermée | III.1.1 (annexe méthodo) | Disponible, non cité dans le README actuel |
| Vega/delta à plusieurs maturités résiduelles | Le vega change de signe *aussi* selon la maturité | III.1.1 | À produire (effort faible, §4) |
| Figure B, panneaux (a)(c)(d) — coupon, PDI, perte | Classement des 6 cas | III.1.3 | **Exploité** (redondant avec `RESULTATS.md`) |
| Figure B, panneau (b) — dates de rappel | Le décrément retarde le rappel | III.1.3 | **Exploité** |
| Colonnes `proba_rappel_t1...t10` | Détail par date, par cas | III.1.3 | Disponible, non tabulé (§2) |
| Sensibilité coupon à σ/r | Robustesse de la thèse décrément | III.1.3 | À produire (effort moyen, §4) |
| Figure D, panneau (a) — PnL vs vol réalisée (mismatch) | `PnL ≈ ½Γ(σ_modèle²−σ_réal²)`, formule validée par la simulation | III.2 | **Exploité (Figure D)** |
| Figure D, panneau (b) — PnL vs fréquence de rebalancement | Fréquence ≈ sans effet sur la dispersion, le gap risk domine | III.2 | **Exploité (Figure D)** |
| `figureD_resume.csv` (gamma moyen, trajectoires) | Chiffres citables (gamma moyen dollar, nb trajectoires) | III.2 | **Exploité (Figure D)** |
| Grille de delta/gamma (heatmap) | Delta/gamma instables près des barrières | III.2 | Grille disponible dans `src/delta_hedging.py`, pas encore tracée (§3.5, §4) |
| Delta hedging sur le produit du mémoire (10 ans, coupon au pair) | Idem, mais chiffres directement comparables à Figure B | III.2 | **À produire, effort élevé** (§3.1) — Figure D porte sur le produit 5 ans du notebook, pas ce produit-ci |
| Figure C, trajectoire type | Exposition oscille entre plafond et désensibilisation | III.3.1 | **Exploité** |
| Figure C, scénario V | Sur-réaction à la chute + sous-participation au rebond | III.3.1 | **Exploité** |
| Creux exact du scénario V | Quantifie la sur-exposition avant le choc | III.3.1 | **Exploité** (dans `RESULTATS.md`) |
| Figure C, distribution vol réalisée | La vol réalisée VT ≠ la cible, biais asymétrique | III.3.2 | **Exploité** |
| Médiane / écart-type / proba ±2pt de la distribution | Précision du biais | III.3.2 | **Exploité** (dans `RESULTATS.md`) |
| Sensibilité VT à σ_cible / L_max | Le biais dépend des paramètres de construction | III.3.2 | À produire (effort faible-moyen, §4) |
