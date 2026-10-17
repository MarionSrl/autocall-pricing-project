"""Régénère tout depuis zéro, en une commande : les 5 figures du mémoire, leurs
CSV/MD, et le récapitulatif consolidé RESULTATS.md -- avec la seed globale
unique (src/marche.py::SEED_GLOBAL). À relancer si un paramètre ou la seed
change, pour que tous les chiffres cités dans le mémoire restent cohérents
entre eux.

Compter ~20 minutes (figBbis_vol_target_decrement.py est de loin le plus
long, ~16 min, du fait de la construction quotidienne de l'indice Vol Target
sur 200 000 trajectoires x 10 ans ; figC_hedging_produit_notebook.py vient
ensuite, ~3 min, du fait de la simulation de couverture path-dépendante).

Usage : python scripts/run_all.py
"""

import os
import subprocess
import sys
import time

REPERTOIRE_RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPERTOIRE_SCRIPTS = os.path.join(REPERTOIRE_RACINE, "scripts")

# Ordre de lecture du mémoire : Figure A (III.1.1), Figure B (III.1.3),
# Figure B bis -- extension de la Figure B (Vol Target + décrément), Figure C
# -- delta hedging (III.2), Figure D -- Volatility Target (III.3). Les 5
# scripts sont indépendants (aucun ne lit la sortie d'un autre) ; cet ordre
# est donc éditorial, pas une contrainte technique. generer_resultats.py,
# lui, doit venir en dernier : il lit les CSV que les 5 scripts précédents
# viennent d'écrire.
ETAPES = [
    "figA_sensibilites_pdi_autocall.py",
    "figB_autocall_vs_decrement.py",
    "figBbis_vol_target_decrement.py",
    "figC_hedging_produit_notebook.py",
    "figD_volatility_target.py",
    "generer_resultats.py",
]


def main():
    t0 = time.time()
    for nom_script in ETAPES:
        chemin = os.path.join(REPERTOIRE_SCRIPTS, nom_script)
        print(f"=== {nom_script} ===")
        t_script = time.time()
        resultat = subprocess.run([sys.executable, chemin], cwd=REPERTOIRE_RACINE)
        if resultat.returncode != 0:
            print(f"\nÉchec de {nom_script} (code {resultat.returncode}) -- arrêt.", file=sys.stderr)
            sys.exit(resultat.returncode)
        print(f"  -> {nom_script} terminé en {time.time() - t_script:.1f}s\n")

    print(f"Tout régénéré en {time.time() - t0:.1f}s.")


if __name__ == "__main__":
    main()
