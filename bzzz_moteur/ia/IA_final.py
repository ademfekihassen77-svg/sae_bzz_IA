from typing import Literal
from ia import JeuDict, MoteurIA
import random


class VOSNOMS_IA(MoteurIA):
    nom = "FEKIHASSEN_GIRARD"

    def __init__(self, joueur_id: str, ncases: int, max_tours: int, temps_ko: int) -> None:
        self.joueur_id = joueur_id
        self.ncases = ncases
        self.max_tours = max_tours

        # Dictionnaire pour se souvenir de la quantité de nectar dans chaque fleur
        # Clé : (x, y), Valeur : quantité restante
        self.memoire_nectar = {}

        # Constante : Une fleur commence généralement à 50
        self.MAX_NECTAR = 50

    def ponte(self, jeu: JeuDict, cout_ponte: int) -> Literal["OUV", "BOU", "ECL", "RIEN"]:
        # Récupération des infos
        mon_nectar = jeu["moi"]["nectar"]
        tour = jeu["tour_actuel"]
        mes_abeilles = jeu["moi"]["abeilles"]

        # On compte nos troupes manuellement avec une boucle (plus simple à lire)
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

        # Si on n'a pas assez de nectar, on ne fait rien
        if mon_nectar < cout_ponte:
            return "RIEN"

        # STRATEGIE : Evolution selon le moment de la partie

        # 1. Tout début de partie : il nous faut des ouvrières vite !
        if len(mes_abeilles) < 5:
            # Juste une éclaireuse pour voir les fleurs
            if nb_eclaireuses == 0:
                return "ECL"
            return "OUV"

        # On garde une petite sécurité de nectar (2 pontes d'avance)
        if mon_nectar < cout_ponte * 3:
            return "RIEN"

        # 2. Première moitié du jeu : On masse les ouvrières
        if tour < self.max_tours / 2:
            if nb_ouvrieres < 15:
                return "OUV"
            # Si on a assez d'ouvrières, on fait une 2eme éclaireuse
            if nb_eclaireuses < 2:
                return "ECL"

        # 3. Fin de partie : On prépare la défense/attaque
        else:
            # S'il y a beaucoup d'ouvrières, on fait des bourdons
            if nb_bourdons < 4:
                return "BOU"

        return "RIEN"

    def action_abeilles(self, jeu: JeuDict) -> list[tuple[str, int, int, Literal["DEPLACEMENT", "BUTINAGE"]]]:
        actions = []
        abeilles = jeu["moi"]["abeilles"]
        fleurs_visibles = jeu["fleurs"]
        ma_ruche = jeu["moi"]["position"]

        # --- ETAPE 1 : Mise à jour de la mémoire ---

        # On note les fleurs qu'on voit
        for f in fleurs_visibles:
            coord = (f["x"], f["y"])
            # Si on ne connaissait pas cette fleur, on l'ajoute
            if coord not in self.memoire_nectar:
                self.memoire_nectar[coord] = self.MAX_NECTAR

        # On nettoie la mémoire (on enlève les fleurs qui ont disparu de la carte)
        # On crée une liste temporaire des positions visibles
        pos_visibles = []
        for f in fleurs_visibles:
            pos_visibles.append((f["x"], f["y"]))

        # On refait le dictionnaire en gardant que ce qui existe encore
        nouvelle_memoire = {}
        for pos, qte in self.memoire_nectar.items():
            if pos in pos_visibles:
                nouvelle_memoire[pos] = qte
        self.memoire_nectar = nouvelle_memoire

        # --- ETAPE 2 : Liste des obstacles ---
        # On liste toutes les cases où il y a déjà quelqu'un pour ne pas foncer dedans
        cases_interdites = []

        # Les ennemis
        for j in jeu["autres_joueurs"]:
            for a in j["abeilles"]:
                cases_interdites.append((a["position"]["x"], a["position"]["y"]))

        # Mes propres abeilles (position actuelle)
        for a in abeilles:
            cases_interdites.append((a["position"]["x"], a["position"]["y"]))

        # --- ETAPE 3 : Décision pour chaque abeille ---

        for abeille in abeilles:
            # Si l'abeille est KO, on passe
            if abeille["ko_temps"] > 0:
                continue

            id_abeille = abeille["id"]
            pos_x = abeille["position"]["x"]
            pos_y = abeille["position"]["y"]
            pos_actuelle = (pos_x, pos_y)

            # On retire notre propre position des interdits car on va bouger
            if pos_actuelle in cases_interdites:
                cases_interdites.remove(pos_actuelle)

            action_choisie = None  # Variable pour stocker ce qu'on va faire

            # CAS A : L'abeille est pleine -> RENTRER A LA MAISON
            if abeille["nectar"] == abeille["max_nectar"]:
                if pos_x == ma_ruche["x"] and pos_y == ma_ruche["y"]:
                    # On est arrivé, le jeu vide automatiquement le nectar
                    pass
                else:
                    # On se déplace vers la ruche
                    prochaine_case = self.trouver_direction(pos_x, pos_y, ma_ruche["x"], ma_ruche["y"],
                                                            cases_interdites, abeille["abeille_type"])
                    if prochaine_case:
                        action_choisie = (id_abeille, prochaine_case[0], prochaine_case[1], "DEPLACEMENT")
                        cases_interdites.append(prochaine_case)  # On réserve la case

            # CAS B : L'abeille cherche du nectar
            else:
                # 1. Trouver la meilleure fleur
                objectif_fleur = self.choisir_fleur_rentable(pos_x, pos_y, fleurs_visibles, cases_interdites)

                if objectif_fleur:
                    dist_x = abs(pos_x - objectif_fleur["x"])
                    dist_y = abs(pos_y - objectif_fleur["y"])
                    distance = max(dist_x, dist_y)

                    # Si on est dessus ou juste à côté (distance <= 1)
                    if distance <= 1:
                        coord_fleur = (objectif_fleur["x"], objectif_fleur["y"])
                        qte_estimee = self.memoire_nectar.get(coord_fleur, 0)

                        if qte_estimee > 0:
                            # ON BUTINE
                            action_choisie = (id_abeille, objectif_fleur["x"], objectif_fleur["y"], "BUTINAGE")
                            cases_interdites.append(pos_actuelle)  # On ne bouge pas

                            # Mise à jour de notre simulation
                            gain = self.calculer_gain_virtuel(qte_estimee)
                            place_dispo = abeille["max_nectar"] - abeille["nectar"]
                            if gain > place_dispo:
                                gain = place_dispo

                            self.memoire_nectar[coord_fleur] = qte_estimee - gain
                        else:
                            # Fleur vide virtuellement : on attend sur place
                            cases_interdites.append(pos_actuelle)
                    else:
                        # On est trop loin, on avance
                        prochaine_case = self.trouver_direction(pos_x, pos_y, objectif_fleur["x"], objectif_fleur["y"],
                                                                cases_interdites, abeille["abeille_type"])
                        if prochaine_case:
                            action_choisie = (id_abeille, prochaine_case[0], prochaine_case[1], "DEPLACEMENT")
                            cases_interdites.append(prochaine_case)
                        else:
                            cases_interdites.append(pos_actuelle)
                else:
                    # Pas de fleur intéressante trouvée
                    cases_interdites.append(pos_actuelle)

            # Si on a décidé d'une action, on l'ajoute à la liste finale
            if action_choisie:
                actions.append(action_choisie)
            else:
                # Si rien de prévu, on remet la position actuelle dans les interdits pour bloquer les autres
                if pos_actuelle not in cases_interdites:
                    cases_interdites.append(pos_actuelle)

        return actions

    # --- MES FONCTIONS UTILITAIRES ---

    def calculer_gain_virtuel(self, qte_actuelle):
        """ Copie de la règle du jeu pour savoir combien on gagne """
        if qte_actuelle >= 33:  # 66% de 50
            return 3
        elif qte_actuelle >= 16:  # 33% de 50
            return 2
        else:
            return 1

    def choisir_fleur_rentable(self, x, y, liste_fleurs, obstacles):
        """
        Algorithme classique de recherche de maximum.
        On cherche le meilleur rapport (Nectar / Distance).
        """
        meilleure_fleur = None
        meilleur_score = -1

        for f in liste_fleurs:
            # On vérifie si la fleur est accessible (pas d'abeille dessus sauf nous)
            # Note : on simplifie, on vérifie juste si la fleur est dans la liste des obstacles
            # Dans l'idéal il faudrait vérifier plus finement mais c'est suffisant pour un niveau 1
            if (f["x"], f["y"]) in obstacles:
                # Petite exception : si c'est moi qui suis dessus (x,y), c'est bon
                if not (f["x"] == x and f["y"] == y):
                    continue

            # On récupère combien il reste de nectar dans notre mémoire
            qte = self.memoire_nectar.get((f["x"], f["y"]), 0)

            if qte <= 0:
                continue

            # Calcul de la distance
            dist = max(1, max(abs(f["x"] - x), abs(f["y"] - y)))

            # Le score est : Quantité divisée par Distance
            score = qte / dist

            if score > meilleur_score:
                meilleur_score = score
                meilleure_fleur = f

        return meilleure_fleur

    def trouver_direction(self, mon_x, mon_y, cible_x, cible_y, obstacles, type_abeille):
        """
        Fonction de déplacement qui essaie d'avancer, et contourne si bloqué.
        """
        # Direction idéale
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

        # 1. Essai : Déplacement direct (Pour Eclaireuse : Diagonale possible)
        if type_abeille == "ECL" and dx != 0 and dy != 0:
            test_x = mon_x + dx
            test_y = mon_y + dy
            if self.est_valide(test_x, test_y, obstacles):
                return (test_x, test_y)

        # 2. Essai : Avancer sur l'axe X
        if dx != 0:
            test_x = mon_x + dx
            test_y = mon_y
            if self.est_valide(test_x, test_y, obstacles):
                return (test_x, test_y)

        # 3. Essai : Avancer sur l'axe Y
        if dy != 0:
            test_x = mon_x
            test_y = mon_y + dy
            if self.est_valide(test_x, test_y, obstacles):
                return (test_x, test_y)

        # 4. Si tout est bloqué : Contournement simple
        # Si je voulais aller en X mais bloqué, j'essaie d'aller en Y (Haut/Bas) pour contourner
        if dx != 0:
            # Essai bas
            if self.est_valide(mon_x, mon_y + 1, obstacles): return (mon_x, mon_y + 1)
            # Essai haut
            if self.est_valide(mon_x, mon_y - 1, obstacles): return (mon_x, mon_y - 1)

        if dy != 0:
            # Essai droite
            if self.est_valide(mon_x + 1, mon_y, obstacles): return (mon_x + 1, mon_y)
            # Essai gauche
            if self.est_valide(mon_x - 1, mon_y, obstacles): return (mon_x - 1, mon_y)

        return None

    def est_valide(self, x, y, obstacles):
        # Vérifier si on sort du plateau
        if x < 0 or x >= self.ncases: return False
        if y < 0 or y >= self.ncases: return False

        # Vérifier si la case est prise
        if (x, y) in obstacles: return False

        return True