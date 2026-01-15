import random
from typing import Literal

from ia import JeuDict, MoteurIA


class IAAleatoire(MoteurIA):
    nom = ("test")

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


        return "OUV"


    def action_abeilles(
        self, jeu: JeuDict
    ) -> list[tuple[str, int, int, Literal["DEPLACEMENT", "BUTINAGE"]]]:
        if self.premier_tour_joueur :
            self.fleur_cible = jeu["fleur"][0]
            self.premier_tour_joueur = False

        abeille = jeu["moi"]["abeilles"][0]
        if abeille["nectar"] > 0:
            cible = jeu["moi"]['position']
        else :
            cible = self.fleur_cible
            if abs(abeille['position']["x"] - cible["x"]) <= 1 and abs(abeille['position']["y"] - cible["y"]) <= 1:
                return [(abeille["id"], cible["x"], cible["y"], "BUTINAGE")]
        dx = 0
        dy = 0

        if abeille["position"]["x"] < cible["x"]:
            dx = 1
        elif abeille["position"]["x"] > cible["x"]:
            dx = -1

        if abeille["position"]["y"] < cible["y"]:
            dy = 1
        elif abeille["position"]["y"] > cible["y"]:
            dy = -1

        return [(abeille["id"], abeille["position"]["x"] + dx, abeille["position"]["y"] + dy, "DEPLACEMENT")]
