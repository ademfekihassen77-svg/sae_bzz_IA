from typing import Literal
from ia import JeuDict, MoteurIA
import random


# ATTENTION : Change le nom de la classe et la variable 'nom' ci-dessous
# Règle : Noms de famille en majuscule séparés par un tiret ou underscore [cite: 7]
class VOSNOMS_IA(MoteurIA):
    nom = "maya_la_opps"

    def __init__(self, joueur_id: str, ncases: int, max_tours: int, temps_ko: int) -> None:
        """
        Initialisation de l'IA.
        On garde les variables persistantes ici[cite: 25].
        """
        self.joueur_id = joueur_id
        self.ncases = ncases
        self.max_tours = max_tours
        self.temps_ko = temps_ko
        # On peut stocker des infos ici si besoin pour les tours suivants

    def ponte(self, jeu: JeuDict, cout_ponte: int) -> Literal["OUV", "BOU", "ECL", "RIEN"]:
        """
        Logique de ponte : on garde ta logique qui semblait cohérente.
        """
        tour = jeu["tour_actuel"]
        nectar = jeu["moi"]["nectar"]
        mes_abeilles = jeu["moi"]["abeilles"]
        nb_abeilles = len(mes_abeilles)


        if nb_abeilles < 7:
            if nectar < cout_ponte:
                return "RIEN"

            # Stratégie simple et efficace
            if tour < 20:
                if nb_abeilles < 2: return "ECL"  # Un peu de vision au début
                return "OUV"
            elif tour < 150:
                # On priorise la force de travail
                return "OUV"

            # Fin de partie : on ne pond que si on est très riche
            if nectar > cout_ponte * 5:
                return "OUV"

        return "RIEN"

    def action_abeilles(self, jeu: JeuDict) -> list[tuple[str, int, int, Literal["DEPLACEMENT", "BUTINAGE"]]]:
        actions = []
        mes_abeilles = jeu["moi"]["abeilles"]
        fleurs = jeu["fleurs"]  # Liste des positions {x, y} [cite: 66]
        ma_ruche = jeu["moi"]["position"]

        # --- SOLUTION ANTI-BOUCHON ---
        # On crée un ensemble pour retenir les fleurs déjà visées par mes abeilles ce tour-ci
        fleurs_ciblees_ce_tour = set()
        # -----------------------------

        for abeille in mes_abeilles:
            # 1. Gestion des abeilles KO ou invalides
            if abeille["ko_temps"] > 0:
                continue

            pos = abeille["position"]
            a_id = abeille["id"]
            a_type = abeille["abeille_type"]

            # 2. RETOUR A LA RUCHE
            # Si l'abeille a du nectar, elle rentre (simple et efficace)
            if abeille["nectar"] > 0:
                if self._est_sur_case(pos, ma_ruche):
                    # Elle est sur la ruche, elle dépose automatiquement (pas d'action requise)
                    continue
                else:
                    # Elle rentre
                    next_x, next_y = self._prochaine_case(pos, ma_ruche, a_type)
                    actions.append((a_id, next_x, next_y, "DEPLACEMENT"))
                    continue

            # 3. CHERCHER UNE FLEUR (Si pas de nectar)
            # On cherche une fleur LIBRE (pas dans fleurs_ciblees_ce_tour)
            fleur_cible = self._trouver_meilleure_fleur(pos, fleurs, fleurs_ciblees_ce_tour)

            if fleur_cible:
                # On marque cette fleur comme "réservée" pour éviter que la prochaine abeille n'y aille
                # On utilise un tuple (x, y) pour l'identifier
                coord_fleur = (fleur_cible["x"], fleur_cible["y"])
                fleurs_ciblees_ce_tour.add(coord_fleur)

                # Si on est dessus ou à côté : BUTINAGE
                if self._est_adjacent(pos, fleur_cible):
                    actions.append((a_id, fleur_cible["x"], fleur_cible["y"], "BUTINAGE"))
                else:
                    # Sinon : DEPLACEMENT vers la fleur
                    next_x, next_y = self._prochaine_case(pos, fleur_cible, a_type)
                    actions.append((a_id, next_x, next_y, "DEPLACEMENT"))

            else:
                # 4. EXPLORATION (Si aucune fleur dispo ou toutes prises)
                # Mouvement aléatoire pour ne pas rester bloqué
                next_x, next_y = self._mouvement_aleatoire(pos, a_type)
                actions.append((a_id, next_x, next_y, "DEPLACEMENT"))

        return actions

    # --- FONCTIONS UTILITAIRES ---

    def _trouver_meilleure_fleur(self, ma_pos: dict, liste_fleurs: list, fleurs_interdites: set) -> dict | None:
        """
        Trouve la fleur la plus proche qui N'EST PAS dans fleurs_interdites.
        """
        meilleure_fleur = None
        dist_min = float('inf')

        for fleur in liste_fleurs:
            # Si cette fleur est déjà ciblée par une de mes collègues, on l'ignore !
            if (fleur["x"], fleur["y"]) in fleurs_interdites:
                continue

            dist = self._distance(ma_pos, fleur)
            if dist < dist_min:
                dist_min = dist
                meilleure_fleur = fleur

        return meilleure_fleur

    def _distance(self, p1: dict, p2: dict) -> int:
        """Distance de Manhattan (|dx| + |dy|)"""
        return abs(p1["x"] - p2["x"]) + abs(p1["y"] - p2["y"])

    def _est_sur_case(self, p1: dict, p2: dict) -> bool:
        return p1["x"] == p2["x"] and p1["y"] == p2["y"]

    def _est_adjacent(self, p1: dict, p2: dict) -> bool:
        """Vérifie si p2 est à portée de butinage (distance max 1 case, diagonales incluses)"""
        dx = abs(p1["x"] - p2["x"])
        dy = abs(p1["y"] - p2["y"])
        # Pour le butinage, la règle permet de butiner tout ce qui est autour (distance Tchebychev = 1)
        return dx <= 1 and dy <= 1

    def _prochaine_case(self, depart: dict, arrivee: dict, type_abeille: str) -> tuple[int, int]:
        """Calcule la prochaine case pour aller vers l'objectif"""
        dx = arrivee["x"] - depart["x"]
        dy = arrivee["y"] - depart["y"]

        move_x = 0
        move_y = 0

        if dx != 0: move_x = 1 if dx > 0 else -1
        if dy != 0: move_y = 1 if dy > 0 else -1

        new_x, new_y = depart["x"], depart["y"]

        # Logique de déplacement selon le type
        if type_abeille == "ECL":
            # L'éclaireuse peut aller en diagonale
            new_x += move_x
            new_y += move_y
        else:
            # Les autres : un seul axe à la fois. On choisit l'axe le plus loin.
            if abs(dx) >= abs(dy):
                new_x += move_x
            else:
                new_y += move_y

        # Vérification limites (au cas où)
        new_x = max(0, min(new_x, self.ncases - 1))
        new_y = max(0, min(new_y, self.ncases - 1))

        return new_x, new_y

    def _mouvement_aleatoire(self, pos: dict, type_abeille: str) -> tuple[int, int]:
        choices = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        if type_abeille == "ECL":
            choices += [(1, 1), (1, -1), (-1, 1), (-1, -1)]

        dx, dy = random.choice(choices)
        nx = max(0, min(pos["x"] + dx, self.ncases - 1))
        ny = max(0, min(pos["y"] + dy, self.ncases - 1))
        return nx, ny