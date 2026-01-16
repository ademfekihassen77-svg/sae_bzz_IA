from typing import Literal
from ia import JeuDict, MoteurIA


class TestIA(MoteurIA):
    nom = "TEST"  # Nom de l'IA

    def __init__(self, joueur_id: str, ncases: int, max_tours: int, temps_ko: int) -> None:
        """Initialisation de l'IA avec les paramètres de base du jeu"""
        self.joueur_id = joueur_id
        self.ncases = ncases
        self.max_tours = max_tours
        self.temps_ko = temps_ko

        # Variables pour garder l'état du jeu
        self.tour_courant = 0
        self.strategie_actuelle = "exploration"  # exploration ou collecte

    def ponte(self, jeu: JeuDict, cout_ponte: int) -> Literal["OUV", "BOU", "ECL", "RIEN"]:
        """Décide quelle abeille pondre à ce tour"""
        self.tour_courant = jeu["tour_actuel"]
        nectar_disponible = jeu["moi"]["nectar"]
        nb_abeilles = len(jeu["moi"]["abeilles"])

        # Ne pas pondre si pas assez de nectar
        if nectar_disponible < cout_ponte:
            return "RIEN"

        # Stratégie de ponte selon la phase de jeu
        if self.tour_courant < 20:  # Début de partie
            # Priorité aux éclaireuses pour explorer
            if nb_abeilles < 3:
                return "ECL"
            # Puis des ouvrières pour collecter
            elif nb_abeilles < 8:
                return "OUV"
            else:
                return "RIEN"
        elif self.tour_courant < 100:  # Milieu de partie
            # Équilibre entre ouvrières et quelques bourdons
            if nb_abeilles % 5 == 0:
                return "BOU"  # Un bourdon tous les 5
            else:
                return "OUV"
        else:  # Fin de partie
            # Seulement si beaucoup de nectar disponible
            if nectar_disponible > cout_ponte * 3:
                return "OUV"
            else:
                return "RIEN"

    def action_abeilles(self, jeu: JeuDict) -> list[tuple[str, int, int, Literal["DEPLACEMENT", "BUTINAGE"]]]:
        """Décide des actions pour chaque abeille"""
        actions = []
        mes_abeilles = jeu["moi"]["abeilles"]
        fleurs = jeu["fleurs"]
        ma_position = jeu["moi"]["position"]

        for abeille in mes_abeilles:
            # Ignorer les abeilles KO
            if abeille["ko_temps"] > 0:
                continue

            pos_abeille = abeille["position"]

            # Si l'abeille a du nectar et est près de la ruche, elle rentre
            if abeille["nectar"] > 0:
                if self._est_proche_ruche(pos_abeille, ma_position):
                    # Déjà à la ruche, le nectar sera automatiquement déposé
                    continue
                else:
                    # Se diriger vers la ruche
                    direction = self._direction_vers(pos_abeille, ma_position, abeille["abeille_type"])
                    if direction:
                        actions.append((abeille["id"], direction[0], direction[1], "DEPLACEMENT"))
                    continue

            # Si l'abeille est vide, chercher une fleur
            fleur_proche = self._trouver_fleur_proche(pos_abeille, fleurs)

            if fleur_proche:
                # Si on est à côté d'une fleur avec du nectar, butiner
                if self._est_adjacent(pos_abeille, fleur_proche):
                    actions.append((abeille["id"], fleur_proche["x"], fleur_proche["y"], "BUTINAGE"))
                else:
                    # Se déplacer vers la fleur
                    direction = self._direction_vers(pos_abeille, fleur_proche, abeille["abeille_type"])
                    if direction:
                        actions.append((abeille["id"], direction[0], direction[1], "DEPLACEMENT"))
            else:
                # Explorer : se déplacer aléatoirement
                direction = self._explorer(pos_abeille, abeille["abeille_type"])
                if direction:
                    actions.append((abeille["id"], direction[0], direction[1], "DEPLACEMENT"))

        return actions

    def _est_proche_ruche(self, pos: dict, ruche: dict) -> bool:
        """Vérifie si une position est dans la zone de sécurité (safezone) de la ruche"""
        dx = abs(pos["x"] - ruche["x"])
        dy = abs(pos["y"] - ruche["y"])
        return dx <= 3 and dy <= 3

    def _trouver_fleur_proche(self, pos: dict, fleurs: list) -> dict | None:
        """Trouve la fleur la plus proche avec du nectar"""
        fleur_la_plus_proche = None
        distance_min = float('inf')

        for fleur in fleurs:
            # On ne peut pas voir le nectar des fleurs adverses, on les considère toutes
            distance = abs(fleur["x"] - pos["x"]) + abs(fleur["y"] - pos["y"])
            if distance < distance_min:
                distance_min = distance
                fleur_la_plus_proche = fleur

        return fleur_la_plus_proche

    def _est_adjacent(self, pos1: dict, pos2: dict) -> bool:
        """Vérifie si deux positions sont adjacentes (max 1 case de distance)"""
        dx = abs(pos1["x"] - pos2["x"])
        dy = abs(pos1["y"] - pos2["y"])
        return dx <= 1 and dy <= 1

    def _direction_vers(self, pos_depart: dict, pos_cible: dict, type_abeille: str) -> tuple[int, int] | None:
        """Calcule la direction pour aller vers une cible"""
        dx = pos_cible["x"] - pos_depart["x"]
        dy = pos_cible["y"] - pos_depart["y"]

        # Normaliser les déplacements (-1, 0, 1)
        move_x = 0 if dx == 0 else (1 if dx > 0 else -1)
        move_y = 0 if dy == 0 else (1 if dy > 0 else -1)

        # Les éclaireuses peuvent se déplacer en diagonal
        if type_abeille == "ECL":
            new_x = pos_depart["x"] + move_x
            new_y = pos_depart["y"] + move_y
        else:
            # Ouvrières et bourdons : déplacement cardinal seulement
            # Privilégier le mouvement le plus important
            if abs(dx) > abs(dy):
                new_x = pos_depart["x"] + move_x
                new_y = pos_depart["y"]
            else:
                new_x = pos_depart["x"]
                new_y = pos_depart["y"] + move_y

        # Vérifier les limites du plateau
        if 0 <= new_x < self.ncases and 0 <= new_y < self.ncases:
            return (new_x, new_y)

        return None

    def _explorer(self, pos: dict, type_abeille: str) -> tuple[int, int] | None:
        """Déplacement d'exploration simple"""
        import random

        # Directions possibles selon le type d'abeille
        if type_abeille == "ECL":
            # Les éclaireuses peuvent aller en diagonal
            directions = [
                (1, 0), (-1, 0), (0, 1), (0, -1),  # Cardinal
                (1, 1), (1, -1), (-1, 1), (-1, -1)  # Diagonal
            ]
        else:
            # Ouvrières et bourdons : seulement cardinal
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        random.shuffle(directions)

        for dx, dy in directions:
            new_x = pos["x"] + dx
            new_y = pos["y"] + dy

            if 0 <= new_x < self.ncases and 0 <= new_y < self.ncases:
                return (new_x, new_y)

        return None