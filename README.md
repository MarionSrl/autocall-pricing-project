# Pricing d'un produit Autocallable — Mémoire BFA3

Pricer Monte Carlo d'un produit autocallable sous Black-Scholes, utilisé pour produire
les 4 figures quantitatives du mémoire *Comment les indices de nouvelle génération
(Volatility Target et indices à décrément) permettent-ils de répondre aux contraintes
de structuration, de valorisation et de couverture des produits structurés actions de
long terme ?*

## Structure du repo

| Dossier | Contenu |
|---|---|
| `notebooks/` | Notebook d'exploration initial (produit 5 ans, taux de Vasicek, delta hedging) — indépendant du reste, exécutable de bout en bout |
| `src/` | Modules de pricing : simulation, indices A/B/C, pricer autocall, PDI, coupon, Volatility Target, delta hedging |
| `scripts/` | Un script par figure du mémoire, plus `run_all.py` pour tout régénérer |
| `figures/` | PNG (300 dpi) et CSV/MD de résultats, un jeu par figure |
| `tests/` | Tests pytest (35) |
| `RESULTATS.md` | Tous les chiffres cités dans le mémoire, regroupés par figure |

## Installation et reproduction

```bash
pip install -r requirements.txt

python scripts/run_all.py   # régénère les 4 figures + RESULTATS.md (~5 min)
pytest tests/                # lance les 35 tests
```

Chaque figure peut aussi être relancée seule, par exemple :
`python scripts/figB_autocall_vs_decrement.py`.

Toutes les simulations partagent la même seed (`src/marche.py::SEED_GLOBAL`), pour
qu'une même quantité recalculée dans deux figures donne toujours le même chiffre.

## Le produit

Autocall 10 ans, observations annuelles, barrière de rappel à 100 % du niveau initial,
coupon **à mémoire** (cumulé depuis l'origine, versé uniquement à la date de rappel —
si le produit n'est jamais rappelé, aucun coupon n'est versé à maturité), protection du
capital (PDI) à 60 %, **observée à maturité uniquement**. C'est le produit des Figures
A, B et C. La **Figure D fait exception** : voir sa description ci-dessous.

## Les 4 figures

**Figure B — Autocall classique vs décrément** (`figB_autocall_vs_decrement.py`).
Compare le coupon au pair, les probabilités de rappel et d'activation du PDI, et la
perte conditionnelle, sur 6 cas : indice classique, décrément en %, décrément en
points, barrière dégressive, et deux cas de contrôle (B′, C′).

**Figure A — Sensibilités du PDI et de l'autocall** (`figA_sensibilites_pdi_autocall.py`).
Formule fermée d'un put down-and-in (prix, delta, vega, vanna), puis vega Monte Carlo
de l'autocall complet, décomposé en jambe « sans PDI » et jambe « PDI ». Montre que le
vega du PDI seul est de signe constant, contrairement à celui de l'autocall complet.

**Figure C — Indice Volatility Target** (`figC_volatility_target.py`). Indice construit
sur un modèle de volatilité à 2 régimes : trajectoire type, distribution de la vol
réalisée face à la cible, et scénario de crash-rebond scripté.

**Figure D — Delta hedging et risques résiduels de couverture**
(`figD_hedging_produit_notebook.py`). Panneau (a) : PnL de couverture en fonction du
mismatch entre volatilité réalisée et volatilité modèle, avec prédiction théorique de
gamma-trading superposée. Panneau (b) : dispersion du PnL selon la fréquence de
rebalancement (quasi plate — le risque vient des discontinuités de payoff aux
barrières, pas de la granularité du rebalancement). **Porte sur le produit du notebook
d'exploration (5 ans, coupon fixe 7 %, vol modèle 20 %, sans dividende), pas sur le
produit de référence des Figures A-C** — voir « Conventions à connaître » ci-dessous.

Tous les chiffres (coupons, sensibilités, sous-participation, gamma moyen...) sont
dans **[`RESULTATS.md`](RESULTATS.md)**.

## Conventions à connaître

- **Coupon à mémoire sans barrière indépendante** : le même niveau (100 %) déclenche à
  la fois le rappel et l'accumulation du coupon. Rien n'est versé à maturité si le
  produit n'a jamais été rappelé — ce qui pénalise mécaniquement les indices à
  décrément dans la Figure B, puisqu'ils retardent le rappel.
- **Deux notions de barrière, à ne pas confondre** : le PDI du produit (Figures B et
  A-panneau b) est une condition terminale, observée à maturité uniquement — pas de
  monitoring continu. Le panneau (a) de la Figure A illustre séparément un *vrai* put
  down-and-in à barrière continûment observée (formule fermée classique), dont la
  validation Monte Carlo utilise une correction de continuité par pont brownien.
- **Pas de coûts de transaction** (réplication du décrément, rebalancement quotidien
  de l'indice Volatility Target ou du hedge de la Figure D) : les mécanismes sont
  présentés dans leur configuration la plus favorable.
- **La Figure D porte sur un produit différent des Figures A-C** : maturité 5 ans (pas
  10), coupon fixe à 7 % (pas résolu au pair), volatilité modèle 20 % (pas 18 %), pas
  de dividende. C'est le produit du notebook d'exploration original, réutilisé tel quel
  plutôt que porté sur le produit à 10 ans. Ce choix ne remet pas en cause la
  conclusion de la Figure D : le mécanisme démontré — risque résiduel de gap aux
  barrières de rappel/capital, sensibilité du PnL de couverture au mismatch entre
  volatilité réalisée et volatilité modèle — est **structurel** à tout autocall à
  barrières discontinues, il ne dépend ni de la maturité ni du niveau du coupon. Les
  *niveaux* de PnL affichés ne sont donc pas directement comparables aux coupons des
  Figures A-C (ils portent sur un produit à 5 ans, coupon 7 % fixe), mais la
  *relation* PnL-vs-mismatch et PnL-vs-fréquence qu'elle illustre se généraliserait
  qualitativement au produit à 10 ans.
- **Convention de signe du gamma en Figure D (émetteur, pas investisseur)** : le PnL
  simulé est celui de l'ÉMETTEUR, qui vend le produit et se couvre en delta au prix
  modèle — pas celui de l'investisseur (voir `src/delta_hedging.py` pour le détail).
  `gamma_moyen_dollar` et `gamma_s2_moyen` (dans `figures/figureD_resume.csv`) sont le
  gamma de f(S,σ), la valeur actualisée du flux versé À L'INVESTISSEUR — exactement la
  même fonction et la même convention que le vega de l'autocall en Figure A, aucun
  changement de perspective entre les deux figures. Ce gamma est négatif ici (f est
  concave près du spot initial : l'investisseur est structurellement « court »
  l'optionalité de barrière — le put down-and-in — cédée à l'émetteur en échange du
  coupon), cohérent avec le vega négatif de l'autocall en Figure A (-0,68 pt de % au
  spot initial du produit de référence, `figureA_autocall_vega.csv`) : même sous-jacent
  économique, même signe. Avec un gamma négatif, la formule `dPnL_émetteur ≈
  ½Γ_f·S²·(σ_modèle² − σ_réalisée²)·dt` prédit — et la simulation confirme — un PnL de
  couverture **croissant** avec la volatilité réalisée : à l'inverse de l'intuition
  usuelle « vendeur d'option = short gamma » (vraie pour une option vanille, toujours
  convexe), l'émetteur de ce produit se retrouve net **long gamma** sur son livre
  couvert une fois delta-hedgé, car la fonction qu'il vend est concave, pas convexe.

Le détail complet de ces hypothèses et de leurs limites est rédigé en texte continu
ci-dessous, pour être repris tel quel en annexe méthodologique du mémoire.

## Note méthodologique

*Section rédigée pour être reprise telle quelle en annexe méthodologique du mémoire.*

Les quatre figures reposent sur un cadre de simulation Black-Scholes standard, à
volatilité constante et sans smile ni skew : chaque sous-jacent est modélisé par un
mouvement brownien géométrique sous la probabilité risque-neutre, avec un taux sans
risque, un rendement de dividende et une volatilité fixés une fois pour toutes
(respectivement 2,5 %, 3 % et 18 % pour les indices actions des Figures A et B). Cette
simplification est délibérée : elle isole l'effet des mécanismes étudiés — décrément,
barrière dégressive, plafond de volatilité — de tout effet confondu par la structure par
terme ou le sourire de volatilité du marché. Elle a cependant un coût : en pratique, un
skew de volatilité affecterait différemment les sensibilités mesurées à proximité des
barrières, qu'il s'agisse du rappel ou de la protection du capital, et son absence tend
probablement à sous-estimer l'ampleur des sensibilités mises en évidence dans les
Figures A et C.

La notion de barrière recouvre par ailleurs deux conventions distinctes dans ce travail,
qu'il convient de ne pas confondre. La protection du capital (PDI) du produit autocall
étudié dans les Figures B et A (panneau b) n'est observée qu'à l'échéance : il s'agit d'une
condition terminale portant sur le seul niveau du sous-jacent à maturité, et non d'un
monitoring, discret ou continu, d'une barrière tout au long de la vie du produit — c'est
la convention la plus fréquente en retail, et elle ne pose donc aucune ambiguïté de
fréquence d'observation, ni ne nécessite de correction de type
Broadie–Glasserman–Kou. Le panneau (a) de la Figure A, en revanche, illustre un objet
différent : un véritable put down-and-in à barrière continûment observée, dans sa
formulation fermée usuelle (Bouzoubaa & Osseiran ; Hull), qui sert de démonstration
pédagogique du profil de sensibilités caractéristique des options à barrière, en
particulier de la discontinuité du delta au franchissement. Pour valider cette formule
fermée par une simulation Monte Carlo indépendante malgré une trajectoire
nécessairement simulée à pas discret, une correction de continuité par pont brownien
est appliquée ; elle ne concerne que cette validation ponctuelle et n'intervient à
aucun moment dans le pricing du produit autocall proprement dit.

Le produit autocall retenu suit une convention de coupon « à mémoire » sans barrière de
coupon indépendante de la barrière de rappel : à la date de rappel, le porteur perçoit
l'ensemble des coupons annuels cumulés depuis l'origine, mais si le produit atteint la
maturité sans avoir jamais été rappelé, aucun coupon n'est versé — seul le capital,
protégé ou non selon le niveau du sous-jacent à l'échéance, est remboursé. Cette
convention n'est pas neutre pour l'interprétation de la Figure B : les sous-jacents à
décrément retardant mécaniquement le rappel, ils augmentent la probabilité d'aller à
maturité sans avoir jamais perçu de coupon, de sorte qu'une partie de la hausse du
coupon facial qu'ils affichent au pair compense ce risque de ne rien percevoir, et pas
seulement le risque de perte en capital que mesure la probabilité d'activation du PDI.

Aucun coût de transaction ni frais de gestion n'est par ailleurs pris en compte, que ce
soit dans la réplication du décrément des indices B et C ou dans le rebalancement
quotidien de l'indice à cible de volatilité de la Figure C entre le sous-jacent et le
cash. Les mécanismes étudiés sont donc présentés dans leur configuration la plus
favorable ; l'indice Volatility Target, dont l'exposition varie précisément le plus dans
les phases où le mécanisme est le plus actif, verrait notamment sa performance amputée
d'autant plus fortement par des coûts de rebalancement réalistes.

Enfin, la volatilité sous-jacente à l'indice Volatility Target de la Figure C est
modélisée par une chaîne de Markov à deux régimes — volatilité basse et volatilité de
stress, avec des durées moyennes de séjour distinctes — plutôt que par un modèle à
volatilité stochastique complet de type Heston. Ce choix se justifie par le fait que
seule la persistance temporelle de la volatilité réalisée importe ici — c'est la
condition nécessaire et suffisante pour que le mécanisme de cible de volatilité ait un
intérêt démonstratif — et non la forme fine de sa distribution ; le modèle à régimes
l'obtient avec un nombre de paramètres réduit et directement interprétables, sans les
difficultés numériques propres à Heston, telles que la condition de Feller ou le choix
d'un schéma de discrétisation évitant les variances négatives. Le scénario en V scripté
de cette même figure, construit de façon déterministe pour isoler l'effet d'un choc de
marché rapide suivi d'un rebond symétrique, comporte une simplification supplémentaire
propre à sa construction : la période précédant le choc y est parfaitement plate, donc
de volatilité réalisée strictement nulle, ce qui porte l'exposition de l'indice
Volatility Target à son plafond de façon plus systématique qu'une période réellement
calme ne le ferait. L'effet de sur-exposition au moment du choc qui en résulte est donc
probablement amplifié par cette construction ; l'effet de sous-participation au rebond
qui suit, piloté non par le niveau de volatilité pré-choc mais par le retard structurel
inhérent à toute fenêtre glissante, est en revanche robuste à cette simplification.

Enfin, la Figure D, consacrée à la couverture en delta et à ses risques résiduels,
porte délibérément sur un produit distinct de celui des Figures A à C : le produit du
notebook d'exploration original (maturité 5 ans, coupon fixe de 7 % non résolu au pair,
volatilité modèle 20 %, sans dividende), plutôt que sur le produit de référence à 10 ans
utilisé partout ailleurs. Ce choix méthodologique est justifié par le fait que le
mécanisme mis en évidence — un risque résiduel de gap au franchissement des barrières
de rappel et de capital, et une sensibilité du P&L de couverture à l'écart entre
volatilité réalisée et volatilité de modèle — est structurel à tout autocall à
barrières discrètes et discontinues, indépendamment de sa maturité ou du niveau de son
coupon ; porter l'analyse sur le produit à 10 ans aurait démontré le même mécanisme,
au prix d'un effort de développement supplémentaire sans valeur ajoutée pour la
démonstration. Une conséquence de ce choix est que les niveaux de P&L rapportés dans la
Figure D ne sont pas directement comparables aux niveaux de coupon des Figures A à C ;
seules la relation qualitative entre P&L et mismatch de volatilité, et la relative
insensibilité du risque de couverture à la fréquence de rebalancement, sont les
résultats à retenir et à généraliser.

## Extensions possibles

- Smile de volatilité
- Produits multi-sous-jacents (worst-of autocall)
- Pricer en EDP

## Auteur

Projet réalisé dans le cadre de mon mémoire de fin d'étude - basé sur le projet fait en cours de Produits Structurés — M2 BFA (Dauphine), par Marion Sirol.
