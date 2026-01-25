import sys
from pathlib import Path

from bzzz.jeu import Jeu
from bzzz.ui.fenetre_jeu import afficher_fenetre_jeu_replay

args = sys.argv

if len(args) != 2:
    print(
        "Pas de fichier de replay renseigné, usage: python rejouer.py nom_du_fichier.bzzz"
    )
    sys.exit(1)

filename = args[1]

with Path(f"replays/{filename}").open("rt") as f:
    jeu = Jeu.creer_jeu_depuis_fichier_replay(f)

afficher_fenetre_jeu_replay(jeu)

