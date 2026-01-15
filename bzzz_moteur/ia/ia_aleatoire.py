import random
from typing import Literal

from ia import JeuDict, MoteurIA


class IAAleatoire(MoteurIA):
    nom = "Aleatoire"

    def __init__(
        self, joueur_id: str, ncases: int, max_tours: int, temps_ko: int
    ) -> None:
        self.joueur_id = joueur_id
        self.ncases = ncases
        self.max_tours = max_tours
        self.temps_ko = temps_ko

    def ponte(
        self, jeu: JeuDict, cout_ponte: int
    ) -> Literal["OUV", "BOU", "ECL", "RIEN"]:
        actions: list[Literal["OUV", "BOU", "ECL", "RIEN"]] = [
            "OUV",
            "BOU",
            "ECL",
            "RIEN",
        ]

        return actions[random.randint(0, len(actions) - 1)]

    def action_abeilles(
        self, jeu: JeuDict
    ) -> list[tuple[str, int, int, Literal["DEPLACEMENT", "BUTINAGE"]]]:
        moi = jeu["moi"]
        abeilles_actions: list[
            tuple[str, int, int, Literal["DEPLACEMENT", "BUTINAGE"]]
        ] = []

        for abeille in moi["abeilles"]:
            positions = [
                (0, 0),
                (-1, -1),
                (0, -1),
                (1, -1),
                (1, 0),
                (1, 1),
                (0, 1),
                (-1, 1),
                (-1, 0),
            ]

            position_aleatoire = positions[random.randint(0, len(positions) - 1)]

            abeilles_actions.append(
                (
                    abeille["id"],
                    abeille["position"]["x"] + position_aleatoire[0],
                    abeille["position"]["y"] + position_aleatoire[1],
                    "DEPLACEMENT" if random.randint(0, 1) == 0 else "BUTINAGE",
                )
            )

        return abeilles_actions
