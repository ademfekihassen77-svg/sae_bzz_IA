from typing import Literal
from ia import JeuDict, MoteurIA


class MonAI(MoteurIA):
    # REMPLIR ICI : Uniquement MAJUSCULES, tirets si noms composés, séparés par _
    nom = "NOM1_NOM2"

    def __init__(self, joueur_id: str, ncases: int, max_tours: int, temps_ko: int) -> None:
        """Initialisation des données de base de l'IA."""
        self.joueur_id = joueur_id
        self.ncases = ncases
        self.max_tours = max_tours
        self.temps_ko = temps_ko

    def distance(self, pos1: dict, pos2: dict) -> int:
        """Calcule la distance de Manhattan entre deux points."""
        return abs(pos1['x'] - pos2['x']) + abs(pos1['y'] - pos2['y'])

    def ponte(self, jeu: JeuDict, cout_ponte: int) -> Literal["OUV", "BOU", "ECL", "RIEN"]:
        """Logique de reproduction : on privilégie les ouvrières pour récolter."""
        # Si on a assez de nectar, on pond une ouvrière pour maximiser la récolte
        if jeu["moi"]["nectar"] >= cout_ponte:
            return "OUV"
        return "RIEN"

    def action_abeilles(self, jeu: JeuDict) -> list[tuple[str, int, int, Literal["DEPLACEMENT", "BUTINAGE"]]]:
        """Logique de mouvement et de récolte."""
        actions = []
        ma_ruche = jeu["moi"]["position"]
        mes_abeilles = jeu["moi"]["abeilles"]
        fleurs = jeu["fleurs"]

        for abeille in mes_abeilles:
            abeille_id = abeille["id"]
            pos_actuelle = abeille["position"]

            # STRATÉGIE : Si l'abeille est pleine, elle rentre à la ruche
            if abeille["nectar"] >= abeille["max_nectar"]:
                if pos_actuelle == ma_ruche:
                    # L'abeille dépose automatiquement le nectar si elle est sur la ruche
                    pass
                else:
                    # On se déplace vers la ruche
                    actions.append((abeille_id, ma_ruche["x"], ma_ruche["y"], "DEPLACEMENT"))

            # STRATÉGIE : Sinon, elle cherche une fleur
            else:
                # Trouver la fleur la plus proche
                if fleurs:
                    fleur_proche = min(fleurs, key=lambda f: self.distance(pos_actuelle, f))

                    # Si on est déjà sur la fleur, on butine
                    if pos_actuelle["x"] == fleur_proche["x"] and pos_actuelle["y"] == fleur_proche["y"]:
                        actions.append((abeille_id, fleur_proche["x"], fleur_proche["y"], "BUTINAGE"))
                    else:
                        # Sinon, on se déplace vers la fleur
                        actions.append((abeille_id, fleur_proche["x"], fleur_proche["y"], "DEPLACEMENT"))

        return actions