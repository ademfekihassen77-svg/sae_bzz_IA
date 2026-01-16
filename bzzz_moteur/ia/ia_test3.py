from typing import Literal
from ia import JeuDict, MoteurIA
import random


class VOSNOMS_IA(MoteurIA):
    nom = "ADEM"

    def __init__(self, joueur_id: str, ncases: int, max_tours: int, temps_ko: int) -> None:
        self.joueur_id = joueur_id
        self.ncases = ncases
        self.max_tours = max_tours
        self.temps_ko = temps_ko

    def ponte(self, jeu: JeuDict, cout_ponte: int) -> Literal["OUV", "BOU", "ECL", "RIEN"]:
        """Ponte économe et limitée pour éviter les bouchons"""
        tour = jeu["tour_actuel"]
        nectar = jeu["moi"]["nectar"]
        nb_abeilles = len(jeu["moi"]["abeilles"])

        # Arrêt à 2/3 du jeu (environ tour 100) et limite à 10 abeilles
        if tour > (self.max_tours * 0.65) or nb_abeilles >= 10 or nectar < cout_ponte:
            return "RIEN"

        if nb_abeilles < 1: return "ECL"
        return "OUV"

    def action_abeilles(self, jeu: JeuDict) -> list[tuple[str, int, int, Literal["DEPLACEMENT", "BUTINAGE"]]]:
        actions = []
        mes_abeilles = jeu["moi"]["abeilles"]
        fleurs = jeu["fleurs"]
        ma_ruche = jeu["moi"]["position"]
        fleurs_ciblees_ce_tour = set()

        for abeille in mes_abeilles:
            if abeille["ko_temps"] > 0: continue

            pos = abeille["position"]
            a_id, a_type = abeille["id"], abeille["abeille_type"]

            # --- DÉFINITION DE LA CAPACITÉ MAX ---
            cap_max = 12 if a_type == "OUV" else 3

            # Recherche d'une fleur avant de décider quoi faire
            fleur_cible = self._trouver_meilleure_fleur(pos, fleurs, fleurs_ciblees_ce_tour)

            # --- LOGIQUE DE DÉCISION ---

            # 1. RETOUR RUCHE : Uniquement si elle est PLEINE (nectar >= cap_max)
            # OU si elle a du nectar et qu'il n'y a plus de fleurs sur la carte
            if abeille["nectar"] >= cap_max or (abeille["nectar"] > 0 and not fleur_cible):
                if self._est_sur_case(pos, ma_ruche):
                    continue  # Dépose automatique
                else:
                    nx, ny = self._prochaine_case(pos, ma_ruche, a_type)
                    actions.append((a_id, nx, ny, "DEPLACEMENT"))
                    continue

            # 2. BUTINAGE / CHERCHER FLEUR (Si pas pleine)
            if fleur_cible:
                coord_fleur = (fleur_cible["x"], fleur_cible["y"])
                fleurs_ciblees_ce_tour.add(coord_fleur)

                if self._est_adjacent(pos, fleur_cible):
                    actions.append((a_id, fleur_cible["x"], fleur_cible["y"], "BUTINAGE"))
                else:
                    nx, ny = self._prochaine_case(pos, fleur_cible, a_type)
                    actions.append((a_id, nx, ny, "DEPLACEMENT"))
            else:
                # 3. EXPLORATION (Rien à faire, bouger au hasard)
                nx, ny = self._mouvement_aleatoire(pos, a_type)
                actions.append((a_id, nx, ny, "DEPLACEMENT"))

        return actions

    # --- FONCTIONS UTILITAIRES ---

    def _trouver_meilleure_fleur(self, ma_pos: dict, liste_fleurs: list, fleurs_interdites: set) -> dict | None:
        meilleure_fleur = None
        dist_min = float('inf')
        for fleur in liste_fleurs:
            if fleur["nectar"] <= 0 or (fleur["x"], fleur["y"]) in fleurs_interdites:
                continue
            dist = self._distance(ma_pos, fleur)
            if dist < dist_min:
                dist_min, meilleure_fleur = dist, fleur
        return meilleure_fleur

    def _distance(self, p1: dict, p2: dict) -> int:
        return abs(p1["x"] - p2["x"]) + abs(p1["y"] - p2["y"])

    def _est_sur_case(self, p1: dict, p2: dict) -> bool:
        return p1["x"] == p2["x"] and p1["y"] == p2["y"]

    def _est_adjacent(self, p1: dict, p2: dict) -> bool:
        return abs(p1["x"] - p2["x"]) <= 1 and abs(p1["y"] - p2["y"]) <= 1

    def _prochaine_case(self, depart: dict, arrivee: dict, type_abeille: str) -> tuple[int, int]:
        dx, dy = arrivee["x"] - depart["x"], arrivee["y"] - depart["y"]
        mx = 1 if dx > 0 else (-1 if dx < 0 else 0)
        my = 1 if dy > 0 else (-1 if dy < 0 else 0)
        nx, ny = depart["x"], depart["y"]

        if type_abeille == "ECL" and mx != 0 and my != 0:
            nx, ny = nx + mx, ny + my
        else:
            if abs(dx) >= abs(dy):
                nx += mx
            else:
                ny += my
        return max(0, min(nx, self.ncases - 1)), max(0, min(ny, self.ncases - 1))

    def _mouvement_aleatoire(self, pos: dict, type_abeille: str) -> tuple[int, int]:
        choices = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        if type_abeille == "ECL": choices += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        dx, dy = random.choice(choices)
        return max(0, min(pos["x"] + dx, self.ncases - 1)), max(0, min(pos["y"] + dy, self.ncases - 1))