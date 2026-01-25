from typing import Literal
from ia import JeuDict, MoteurIA
import random


# RAPPEL : Remplace 'VOSNOMS_IA' par 'NOM1_NOM2' (ex: DUPONT_DURAND)
class VOSNOMS_IA(MoteurIA):
    nom = ("maya_t'est_mort")

    def __init__(self, joueur_id: str, ncases: int, max_tours: int, temps_ko: int) -> None:
        self.joueur_id = joueur_id
        self.ncases = ncases

        # MEMOIRE :
        # On stocke les coordonnées (x, y) des fleurs qui sont vides
        self.fleurs_vides = set()

        # On stocke le nectar de chaque abeille au tour précédent pour comparer
        # Format : { "id_abeille": quantité_nectar }
        self.nectar_precedent = {}

    def ponte(self, jeu: JeuDict, cout_ponte: int) -> Literal["OUV", "BOU", "ECL", "RIEN"]:
        """
        Correction du problème de ponte :
        On pond dès qu'on a assez de nectar. Stratégie simple et efficace.
        """
        mon_nectar = jeu["moi"]["nectar"]
        mes_abeilles = jeu["moi"]["abeilles"]
        nb_abeilles = len(mes_abeilles)


        # Si on a assez d'argent, on achète une Ouvrière (meilleur rapport qualité/prix)
        if mon_nectar >= cout_ponte and nb_abeilles <= 7 :
            return "OUV"

        return "RIEN"

    def action_abeilles(self, jeu: JeuDict) -> list[tuple[str, int, int, Literal["DEPLACEMENT", "BUTINAGE"]]]:
        actions = []
        mes_abeilles = jeu["moi"]["abeilles"]
        liste_fleurs = jeu["fleurs"]
        ma_ruche = jeu["moi"]["position"]

        # --- 1. ETAPE CRITIQUE : DETECTION DES FLEURS VIDES ---
        # On regarde chaque abeille pour voir si elle a échoué à récolter au tour d'avant
        for abeille in mes_abeilles:
            a_id = abeille["id"]
            nectar_actuel = abeille["nectar"]
            pos = abeille["position"]

            # Si on connaissait cette abeille au tour d'avant
            if a_id in self.nectar_precedent:
                nectar_avant = self.nectar_precedent[a_id]

                # Si le nectar n'a pas bougé ALORS qu'elle n'est pas pleine
                if nectar_actuel == nectar_avant and nectar_actuel < abeille["max_nectar"]:
                    # On regarde si elle est collée à une fleur (distance <= 1)
                    # Si elle est collée à une fleur et n'a rien gagné, c'est que la fleur est vide !
                    fleur_proche = self._trouver_fleur_la_plus_proche(pos, liste_fleurs)

                    if fleur_proche:
                        dist = self._distance(pos, fleur_proche)
                        if dist <= 1:
                            # BINGO : C'est une fleur vide, on l'ajoute à la liste noire
                            self.fleurs_vides.add((fleur_proche["x"], fleur_proche["y"]))

            # On met à jour la mémoire pour le PROCHAIN tour
            self.nectar_precedent[a_id] = nectar_actuel

        # --- 2. DECISION DES ACTIONS ---

        # Anti-collision : on note où vont les copines pour ne pas aller au même endroit
        cases_prises_ce_tour = set()

        for abeille in mes_abeilles:
            if abeille["ko_temps"] > 0:
                continue

            a_id = abeille["id"]
            pos = abeille["position"]
            a_max = abeille["max_nectar"]
            a_type = abeille["abeille_type"]

            # CAS A : JE SUIS PLEINE -> RETOUR RUCHE
            # On ne rentre que si on est VRAIMENT pleine (ou très proche du max)
            if abeille["nectar"] >= a_max:
                if self._est_sur_case(pos, ma_ruche):
                    continue  # Elle dépose automatiquement

                # On rentre
                next_x, next_y = self._aller_vers(pos, ma_ruche, a_type, cases_prises_ce_tour)
                actions.append((a_id, next_x, next_y, "DEPLACEMENT"))
                cases_prises_ce_tour.add((next_x, next_y))
                continue

            # CAS B : JE CHERCHE DU NECTAR
            # On cherche une fleur qui n'est PAS dans self.fleurs_vides
            cible = self._trouver_meilleure_fleur(pos, liste_fleurs, cases_prises_ce_tour)

            if cible:
                # Si on est à côté (distance <= 1), on BUTINE
                if self._distance(pos, cible) <= 1:
                    actions.append((a_id, cible["x"], cible["y"], "BUTINAGE"))
                    # On reste sur place, donc on note notre position comme prise
                    cases_prises_ce_tour.add((pos["x"], pos["y"]))
                else:
                    # Sinon on avance
                    next_x, next_y = self._aller_vers(pos, cible, a_type, cases_prises_ce_tour)
                    actions.append((a_id, next_x, next_y, "DEPLACEMENT"))
                    cases_prises_ce_tour.add((next_x, next_y))

            else:
                # CAS C : RIEN A FAIRE (plus de fleurs valides ?) -> Exploration
                # Mouvement aléatoire pour ne pas rester bloqué
                next_x, next_y = self._mouvement_aleatoire(pos, a_type)
                actions.append((a_id, next_x, next_y, "DEPLACEMENT"))
                cases_prises_ce_tour.add((next_x, next_y))

        return actions

    # --- FONCTIONS OUTILS ---

    def _trouver_meilleure_fleur(self, ma_pos, liste_fleurs, cases_interdites):
        """Trouve la fleur la plus proche qui n'est pas vide et pas ciblée"""
        meilleure = None
        min_dist = 9999

        for f in liste_fleurs:
            # 1. EST-ELLE VIDE ?
            if (f["x"], f["y"]) in self.fleurs_vides:
                continue

            # 2. EST-ELLE TROP LOIN ? (Optimisation simple)
            d = self._distance(ma_pos, f)
            if d < min_dist:
                min_dist = d
                meilleure = f

        return meilleure

    def _trouver_fleur_la_plus_proche(self, ma_pos, liste_fleurs):
        """Juste pour savoir à quelle fleur l'abeille est collée pour la détection"""
        meilleure = None
        min_dist = 9999
        for f in liste_fleurs:
            d = self._distance(ma_pos, f)
            if d < min_dist:
                min_dist = d
                meilleure = f
        return meilleure

    def _distance(self, p1, p2):
        # Distance de Tchebychev (diagonales = 1) est plus adaptée au jeu d'abeille
        # Mais Manhattan (abs+abs) marche bien pour le déplacement cardinal
        return max(abs(p1["x"] - p2["x"]), abs(p1["y"] - p2["y"]))

    def _est_sur_case(self, p1, p2):
        return p1["x"] == p2["x"] and p1["y"] == p2["y"]

    def _aller_vers(self, depart, arrivee, type_abeille, obstacles):
        """Calcule le prochain pas en évitant les obstacles simples"""
        target_x, target_y = depart["x"], depart["y"]

        dx = arrivee["x"] - depart["x"]
        dy = arrivee["y"] - depart["y"]

        # On détermine le mouvement idéal
        move_x = 0
        move_y = 0
        if dx != 0: move_x = 1 if dx > 0 else -1
        if dy != 0: move_y = 1 if dy > 0 else -1

        # Test 1 : Axe prioritaire (celui où on est le plus loin)
        candidat_x, candidat_y = depart["x"], depart["y"]
        if abs(dx) >= abs(dy):
            candidat_x += move_x
        else:
            candidat_y += move_y

        # Si la case est libre, on y va
        if 0 <= candidat_x < self.ncases and 0 <= candidat_y < self.ncases:
            if (candidat_x, candidat_y) not in obstacles:
                return candidat_x, candidat_y

        # Sinon, Test 2 : L'autre axe
        candidat_x, candidat_y = depart["x"], depart["y"]
        if abs(dx) >= abs(dy):
            candidat_y += move_y  # On tente l'autre axe
        else:
            candidat_x += move_x

        if 0 <= candidat_x < self.ncases and 0 <= candidat_y < self.ncases:
            if (candidat_x, candidat_y) not in obstacles:
                return candidat_x, candidat_y

        # Si tout est bloqué, on reste sur place (ou mouvement aléatoire dans une version plus complexe)
        return depart["x"], depart["y"]

    def _mouvement_aleatoire(self, pos, type_abeille):
        dx = random.choice([-1, 0, 1])
        dy = random.choice([-1, 0, 1])
        nx = max(0, min(pos["x"] + dx, self.ncases - 1))
        ny = max(0, min(pos["y"] + dy, self.ncases - 1))
        return nx, ny