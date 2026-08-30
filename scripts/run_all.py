"""Régénère tout depuis zéro, en une commande : les 4 figures du mémoire, leurs
CSV/MD, et le récapitulatif consolidé RESULTATS.md -- avec la seed globale
unique (src/marche.py::SEED_GLOBAL). À relancer si un paramètre ou la seed
change, pour que tous les chiffres cités dans le mémoire restent cohérents
entre eux.

Compter ~5 minutes (figD_hedging_produit_notebook.py est le plus long, ~3 min,
du fait de la simulation de couverture path-dépendante).

Usage : python scripts/run_all.py
"""

import os
import subprocess
import sys
import time

REPERTOIRE_RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPERTOIRE_SCRIPTS = os.path.join(REPERTOIRE_RACINE, "scripts")

# Ordre du mémoire (spec §5) : Figure B d'abord, puis Figure A, puis Figure C,
# puis Figure D (ajoutée ensuite pour la section III.2). Les 4 scripts sont
# indépendants (aucun ne lit la sortie d'un autre) ; cet ordre n'est donc
# qu'éditorial. generer_resultats.py, lui, doit venir en dernier : il lit les
# CSV que les 4 scripts précédents viennent d'écrire.
ETAPES = [
    "figB_autocall_vs_decrement.py",
    "figA_sensibilites_pdi_autocall.py",
    "figC_volatility_target.py",
    "figD_hedging_produit_notebook.py",
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
