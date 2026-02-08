from typing import Literal
from ia import JeuDict, MoteurIA
import random


class VOSNOMS_IA(MoteurIA):
    nom = "FEKIHASSEN_GIRARD"

    def __init__(self, joueur_id: str, ncases: int, max_tours: int, temps_ko: int) -> None:
        """
        Initialise l'intelligence artificielle du joueur.

        :param joueur_id: Identifiant du joueur contrôlé par l'IA
        :param ncases: Taille du plateau de jeu (ncases x ncases)
        :param max_tours: Nombre maximum de tours dans la partie
        :param temps_ko: Durée pendant laquelle une abeille est KO
        """
        self.joueur_id = joueur_id
        self.ncases = ncases
        self.max_tours = max_tours

        
        self.memoire_nectar = {}

        self.MAX_NECTAR = 50

    def ponte(self, jeu: JeuDict, cout_ponte: int) -> Literal["OUV", "BOU", "ECL", "RIEN"]:
        """
        Décide quel type d’abeille faire naître à ce tour.

        param jeu: Dictionnaire contenant l’état actuel du jeu
        param cout_ponte: Coût en nectar pour faire naître une abeille
        return: Type d’abeille à créer ("OUV", "ECL", "BOU") ou "RIEN"
        """
        mon_nectar = jeu["moi"]["nectar"]
        tour = jeu["tour_actuel"]
        mes_abeilles = jeu["moi"]["abeilles"]

        nb_ouvrieres = 0
        nb_eclaireuses = 0
        nb_bourdons = 0

        for a in mes_abeilles:
            if a["abeille_type"] == "OUV":
                nb_ouvrieres += 1
            elif a["abeille_type"] == "ECL":
                nb_eclaireuses += 1
            elif a["abeille_type"] == "BOU":
                nb_bourdons += 1

        if mon_nectar < cout_ponte:
            return "RIEN"


        if len(mes_abeilles) < 5:
            if nb_eclaireuses == 0:
                return "ECL"
            return "OUV"

        if mon_nectar < cout_ponte * 3:
            return "RIEN"

        if tour < self.max_tours / 2:
            if nb_ouvrieres < 15:
                return "OUV"

            if nb_eclaireuses < 2:
                return "ECL"

        else:
            if nb_bourdons < 4:
                return "BOU"

        return "RIEN"

    def action_abeilles(self, jeu: JeuDict) -> list[tuple[str, int, int, Literal["DEPLACEMENT", "BUTINAGE"]]]:
        """
        Détermine l’action de chaque abeille pour le tour en cours.

        Pour chaque abeille :
        - si elle est pleine, elle retourne à la ruche
        - sinon, elle cherche une fleur rentable
        - évite les collisions avec les autres abeilles

        :param jeu: Dictionnaire contenant l’état actuel du jeu
        :return: Liste des actions à effectuer (déplacement ou butinage)
        """
         
        actions = []
        abeilles = jeu["moi"]["abeilles"]
        fleurs_visibles = jeu["fleurs"]
        ma_ruche = jeu["moi"]["position"]

        # --- ETAPE 1 : Mise à jour de la mémoire ---

        for f in fleurs_visibles:
            coord = (f["x"], f["y"])
            if coord not in self.memoire_nectar:
                self.memoire_nectar[coord] = self.MAX_NECTAR

        
        pos_visibles = []
        for f in fleurs_visibles:
            pos_visibles.append((f["x"], f["y"]))

        nouvelle_memoire = {}
        for pos, qte in self.memoire_nectar.items():
            if pos in pos_visibles:
                nouvelle_memoire[pos] = qte
        self.memoire_nectar = nouvelle_memoire

        # --- ETAPE 2 : Liste des obstacles ---
        cases_interdites = []

        for j in jeu["autres_joueurs"]:
            for a in j["abeilles"]:
                cases_interdites.append((a["position"]["x"], a["position"]["y"]))

        for a in abeilles:
            cases_interdites.append((a["position"]["x"], a["position"]["y"]))

        # --- ETAPE 3 : Décision pour chaque abeille ---

        for abeille in abeilles:
            if abeille["ko_temps"] > 0:
                continue

            id_abeille = abeille["id"]
            pos_x = abeille["position"]["x"]
            pos_y = abeille["position"]["y"]
            pos_actuelle = (pos_x, pos_y)

            if pos_actuelle in cases_interdites:
                cases_interdites.remove(pos_actuelle)

            action_choisie = None  
            
            if abeille["nectar"] == abeille["max_nectar"]:
                if pos_x == ma_ruche["x"] and pos_y == ma_ruche["y"]:
                    pass
                else:
                    prochaine_case = self.trouver_direction(pos_x, pos_y, ma_ruche["x"], ma_ruche["y"],
                                                            cases_interdites, abeille["abeille_type"])
                    if prochaine_case:
                        action_choisie = (id_abeille, prochaine_case[0], prochaine_case[1], "DEPLACEMENT")
                        cases_interdites.append(prochaine_case)  
            else:
                objectif_fleur = self.choisir_fleur_rentable(pos_x, pos_y, fleurs_visibles, cases_interdites)

                if objectif_fleur:
                    dist_x = abs(pos_x - objectif_fleur["x"])
                    dist_y = abs(pos_y - objectif_fleur["y"])
                    distance = max(dist_x, dist_y)

                    if distance <= 1:
                        coord_fleur = (objectif_fleur["x"], objectif_fleur["y"])
                        qte_estimee = self.memoire_nectar.get(coord_fleur, 0)

                        if qte_estimee > 0:
                            action_choisie = (id_abeille, objectif_fleur["x"], objectif_fleur["y"], "BUTINAGE")
                            cases_interdites.append(pos_actuelle) 

                            
                            gain = self.calculer_gain_virtuel(qte_estimee)
                            place_dispo = abeille["max_nectar"] - abeille["nectar"]
                            if gain > place_dispo:
                                gain = place_dispo

                            self.memoire_nectar[coord_fleur] = qte_estimee - gain
                        else:
                           
                            cases_interdites.append(pos_actuelle)
                    else:
                        
                        prochaine_case = self.trouver_direction(pos_x, pos_y, objectif_fleur["x"], objectif_fleur["y"],
                                                                cases_interdites, abeille["abeille_type"])
                        if prochaine_case:
                            action_choisie = (id_abeille, prochaine_case[0], prochaine_case[1], "DEPLACEMENT")
                            cases_interdites.append(prochaine_case)
                        else:
                            cases_interdites.append(pos_actuelle)
                else:
                    
                    cases_interdites.append(pos_actuelle)

            
            if action_choisie:
                actions.append(action_choisie)
            else:
                
                if pos_actuelle not in cases_interdites:
                    cases_interdites.append(pos_actuelle)

        return actions


    def calculer_gain_virtuel(self, qte_actuelle):
        """ Copie de la règle du jeu pour savoir combien on peut récolter 
            
            param qte_actuelle: Quantité de nectar estimée sur la fleur
            return: Quantité de nectar récupérée (1, 2 ou 3) """
        if qte_actuelle >= 33: 
            return 3
        elif qte_actuelle >= 16: 
            return 2
        else:
            return 1

    def choisir_fleur_rentable(self, x, y, liste_fleurs, obstacles):
        """
        Algorithme classique de recherche de maximum.
        On cherche le meilleur rapport (Nectar / Distance).

        param x: Position x actuelle de l’abeille
        param y: Position y actuelle de l’abeille
        param liste_fleurs: Liste des fleurs visibles
        param obstacles: Liste des cases occupées
        return: La fleur la plus rentable ou None si aucune n’est valable
        """
        meilleure_fleur = None
        meilleur_score = -1

        for f in liste_fleurs:
            
            if (f["x"], f["y"]) in obstacles:
                if not (f["x"] == x and f["y"] == y):
                    continue

            qte = self.memoire_nectar.get((f["x"], f["y"]), 0)

            if qte <= 0:
                continue

            dist = max(1, max(abs(f["x"] - x), abs(f["y"] - y)))

            score = qte / dist

            if score > meilleur_score:
                meilleur_score = score
                meilleure_fleur = f

        return meilleure_fleur

    def trouver_direction(self, mon_x, mon_y, cible_x, cible_y, obstacles, type_abeille):
        """
        Fonction de déplacement qui essaie d'avancer, et contourne si bloqué.
        
        param mon_x: Position x actuelle
        param mon_y: Position y actuelle
        param cible_x: Position x de la cible
        param cible_y: Position y de la cible
        param obstacles: Liste des cases interdites
        param type_abeille: Type de l’abeille ("OUV", "ECL", "BOU")
        return: Tuple (x, y) de la prochaine case ou None
        """
        dx = 0
        dy = 0

        if cible_x > mon_x:
            dx = 1
        elif cible_x < mon_x:
            dx = -1

        if cible_y > mon_y:
            dy = 1
        elif cible_y < mon_y:
            dy = -1

        if type_abeille == "ECL" and dx != 0 and dy != 0:
            test_x = mon_x + dx
            test_y = mon_y + dy
            if self.est_valide(test_x, test_y, obstacles):
                return (test_x, test_y)

        if dx != 0:
            test_x = mon_x + dx
            test_y = mon_y
            if self.est_valide(test_x, test_y, obstacles):
                return (test_x, test_y)

        if dy != 0:
            test_x = mon_x
            test_y = mon_y + dy
            if self.est_valide(test_x, test_y, obstacles):
                return (test_x, test_y)

        if dx != 0:
            if self.est_valide(mon_x, mon_y + 1, obstacles): 
                return (mon_x, mon_y + 1)

            if self.est_valide(mon_x, mon_y - 1, obstacles): 
                return (mon_x, mon_y - 1)

        if dy != 0:
            if self.est_valide(mon_x + 1, mon_y, obstacles): 
                return (mon_x + 1, mon_y)

            if self.est_valide(mon_x - 1, mon_y, obstacles): 
                return (mon_x - 1, mon_y)

        return None

    def est_valide(self, x, y, obstacles):
        """
        fonction qui verifie si une case est valide (dans le plateau et non occupée)

        param x: Coordonnée x de la case
        param y: Coordonnée y de la case
        param obstacles: Liste des cases interdites
        return: True si la case est valide, False sinon
        
        """
        if x < 0 or x >= self.ncases: 
            return False
        if y < 0 or y >= self.ncases: 
            return False

        if (x, y) in obstacles: return False

        return True