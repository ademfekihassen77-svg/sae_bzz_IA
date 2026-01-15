import random
from typing import TYPE_CHECKING

from bzzz.fleur import Fleur
from bzzz.position import Position

if TYPE_CHECKING:
    from bzzz.constantes import ConstantesJeu


def generer_fleurs_aleatoire(constantes: "ConstantesJeu") -> list[Fleur]:
    """Génère de manière aléatoire toutes les fleurs disponibles sur le plateau de jeu.
    Les fleurs sont réparties de manière symétrique pour chacun des quatres joueurs.

    Args:
        constantes (ConstantesJeu): Les constantes de jeu à utiliser

    Raises:
        Exception: Si la constante ncases n'est pas pair

    Returns:
        list[Fleur]: La liste des fleurs
    """

    fleurs: list[Fleur] = []

    if constantes.ncases % 2 == 1:
        raise Exception("NCASES doit être pair !")

    case_milieu = constantes.ncases // 2

    for _ in range(constantes.nfleurs):
        while True:
            x = random.randint(0, case_milieu - 1)
            y = random.randint(0, case_milieu - 1)
            position = Position(x, y)

            # Empêcher les fleurs d'être dans les safe zones
            if 0 <= x <= 3 and 0 <= y <= 3:
                continue

            # Empêcher d'avoir plus d'une fleur à la même position
            if any(True for fleur in fleurs if fleur.position == position):
                continue

            break

        nectar = random.randint(1, constantes.max_nectar)

        fleur_1 = Fleur(position, nectar, nectar)
        fleur_2 = Fleur(Position(constantes.ncases - 1 - x, y), nectar, nectar)
        fleur_3 = Fleur(Position(x, constantes.ncases - 1 - y), nectar, nectar)
        fleur_4 = Fleur(
            Position(constantes.ncases - 1 - x, constantes.ncases - 1 - y),
            nectar,
            nectar,
        )

        fleurs += [fleur_1, fleur_2, fleur_3, fleur_4]

    return fleurs
