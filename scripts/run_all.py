"""Régénère tout depuis zéro, en une commande : les 4 figures du mémoire, leurs
CSV/MD, et le récapitulatif consolidé RESULTATS.md -- avec la seed globale
unique (src/marche.py::SEED_GLOBAL). À relancer si un paramètre ou la seed
change, pour que tous les chiffres cités dans le mémoire restent cohérents
entre eux.

Compter ~5 minutes (figC_hedging_produit_notebook.py est le plus long, ~3 min,
du fait de la simulation de couverture path-dépendante).

Usage : python scripts/run_all.py
"""

import os
import subprocess
import sys
import time

REPERTOIRE_RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPERTOIRE_SCRIPTS = os.path.join(REPERTOIRE_RACINE, "scripts")

# Ordre alphabétique des figures (A, B, C, D), qui suit l'ordre de lecture du
# mémoire : Figure A (III.1.1), Figure B (III.1.3), Figure C -- delta hedging
# (III.2), Figure D -- Volatility Target (III.3). Les 4 scripts sont
# indépendants (aucun ne lit la sortie d'un autre) ; cet ordre est donc éditorial,
# pas une contrainte technique. generer_resultats.py, lui, doit venir en
# dernier : il lit les CSV que les 4 scripts précédents viennent d'écrire.
ETAPES = [
    "figA_sensibilites_pdi_autocall.py",
    "figB_autocall_vs_decrement.py",
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
