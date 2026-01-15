import datetime
import sys
from pathlib import Path

from bzzz.carte import generer_fleurs_aleatoire
from bzzz.constantes import recuperer_constantes_defaut
from bzzz.jeu import Jeu
from bzzz.securite import MoteurIASecurise
from bzzz.ui.fenetre_jeu import afficher_fenetre_jeu_ia
from bzzz.ui.fenetre_selection_ia import afficher_fenetre_selection_ia
from bzzz.utils import recuperer_moteurs_ia
from ia import MoteurIA

SECURITE_TEMPS_REPONSE_SECONDES = 3


def jouer() -> None:
    moteurs_ia = recuperer_moteurs_ia(Path("ia"))
    moteurs_ia_noms = [e[1].nom for e in moteurs_ia]

    noms_ia_selectionnes, mode_securite = afficher_fenetre_selection_ia(moteurs_ia_noms)

    noms_ia_selectionnes = [nom for nom in noms_ia_selectionnes if len(nom) > 0]

    if len(noms_ia_selectionnes) < 2:
        print("Erreur, moins de 2 joueurs ont été configurés avec une IA")
        sys.exit(-1)

    moteurs_ai_selectionnes = [
        next(e[1] for e in moteurs_ia if e[1].nom == nom)
        for nom in noms_ia_selectionnes
    ]

    constantes = recuperer_constantes_defaut()
    fleurs = generer_fleurs_aleatoire(constantes)
    joueurs: list[tuple[str, MoteurIA | MoteurIASecurise | None]] = []

    for idx, moteur_ia in zip(range(1, 5), moteurs_ai_selectionnes, strict=False):
        id_joueur = moteur_ia.nom + f"#{idx}"

        if mode_securite:
            joueur_ia: MoteurIA | MoteurIASecurise = MoteurIASecurise(
                moteur_ia,
                id_joueur,
                constantes.ncases,
                constantes.time_out,
                constantes.time_ko,
                SECURITE_TEMPS_REPONSE_SECONDES,
            )
        else:
            joueur_ia = moteur_ia(
                id_joueur, constantes.ncases, constantes.time_out, constantes.time_ko
            )

        joueurs.append((id_joueur, joueur_ia))

    jeu = Jeu(constantes, joueurs, fleurs)

    afficher_fenetre_jeu_ia(jeu)

    for joueur in joueurs:
        if isinstance(joueur[1], MoteurIASecurise):
            joueur[1].stop()

    if jeu.est_jeu_termine is not None:
        with Path(
            f"replays/ia_{datetime.datetime.now().strftime('%d-%m-%Y-%H-%M-%S')}.bzzz"
        ).open("wt") as f:
            jeu.ecrire_replay_dans_fichier(f)


if __name__ == "__main__":
    jouer()
