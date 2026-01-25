from typing import Literal
from ia import JeuDict, MoteurIA
import random


class VOSNOMS_IA(MoteurIA):
    nom = "detroneuse_de_maya"

    def __init__(self, joueur_id: str, ncases: int, max_tours: int, temps_ko: int) -> None:
        self.joueur_id = joueur_id
        self.ncases = ncases

        # MEMOIRE INTERNE DU NECTAR
        # Le jeu ne nous donne pas le nectar restant, on doit l'estimer nous-mêmes.
        # Dictionnaire {(x, y): quantite_estimee}
        self.nectar_fleurs = {}

        # Constante du jeu (MAX_NECTAR est souvent 50) [cite: 247]
        self.MAX_NECTAR_FLEUR = 50

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
        fleurs_visibles = jeu["fleurs"]

        # 1. Initialisation de la mémoire des fleurs (si pas encore fait)
        # On suppose au début que toutes les fleurs sont pleines
        for f in fleurs_visibles:
            pos_f = (f["x"], f["y"])
            if pos_f not in self.nectar_fleurs:
                self.nectar_fleurs[pos_f] = self.MAX_NECTAR_FLEUR

        # Ensembles pour éviter les collisions (Anti-bouchons)
        positions_occupees = set()
        positions_reservees = set()

        # On marque les positions actuelles des abeilles comme occupées par défaut
        for a in mes_abeilles:
            positions_occupees.add((a["position"]["x"], a["position"]["y"]))

        for abeille in mes_abeilles:
            if abeille["ko_temps"] > 0:
                continue

            id_b = abeille["id"]
            pos = abeille["position"]
            pos_actuelle = (pos["x"], pos["y"])

            # --- CAS 1 : RETOUR RUCHE ---
            # Si l'abeille est pleine, elle rentre
            if abeille["nectar"] >= abeille["max_nectar"]:
                ruche = jeu["moi"]["position"]
                # Si on est sur la ruche, ça dépose tout seul, sinon on bouge
                if not (pos["x"] == ruche["x"] and pos["y"] == ruche["y"]):
                    nouvelle_pos = self.calculer_deplacement_avec_contournement(
                        abeille, ruche, positions_occupees | positions_reservees
                    )
                    if nouvelle_pos:
                        actions.append((id_b, nouvelle_pos[0], nouvelle_pos[1], "DEPLACEMENT"))
                        positions_reservees.add(nouvelle_pos)
                        positions_occupees.add(nouvelle_pos)
                continue

            # --- CAS 2 : CHERCHE NECTAR (INTEGRATION DE TON CODE) ---

            # On cherche la meilleure fleur (la plus proche qui a du nectar en mémoire)
            fleur = self._trouver_meilleure_fleur(pos, fleurs_visibles)

            # === DEBUT DE TON INTEGRATION ===
            if fleur:
                pos_fleur = (fleur["x"], fleur["y"])

                # J'ai adapté la condition pour inclure les cases ADJACENTES (règle du jeu)
                # car on peut butiner à distance 1.
                dist = max(abs(pos["x"] - fleur["x"]), abs(pos["y"] - fleur["y"]))

                if dist <= 1:  # Si on est sur la fleur OU à côté
                    # Vérifier qu'il reste du nectar avant de butiner
                    nectar_fleur_actuel = self.nectar_fleurs.get(pos_fleur, 0)

                    if nectar_fleur_actuel > 0:
                        # Butiner sur place
                        # Si on est à côté, on cible la fleur, sinon on butine notre case (si fleur dessus)
                        # Pour respecter le format butinage: (ID, x_fleur, y_fleur, "BUTINAGE")
                        actions.append((id_b, fleur["x"], fleur["y"], "BUTINAGE"))
                        positions_occupees.add(pos_actuelle)

                        # Calculer combien de nectar sera collecté selon les règles
                        nectar_fourni = self._calculer_nectar_fourni(nectar_fleur_actuel)
                        nectar_collecte = min(
                            nectar_fourni,
                            abeille["max_nectar"] - abeille["nectar"]
                        )

                        # Déduire le nectar de la fleur dans notre mémoire
                        self.nectar_fleurs[pos_fleur] = max(0, nectar_fleur_actuel - nectar_collecte)
                    else:
                        # Fleur vide, ne pas butiner -> On essaiera de bouger au prochain tour
                        # Ou on cherche une exploration aléatoire ici
                        positions_occupees.add(pos_actuelle)
                else:
                    # Aller vers fleur
                    nouvelle_pos = self.calculer_deplacement_avec_contournement(
                        abeille, fleur, positions_occupees | positions_reservees
                    )
                    if nouvelle_pos and nouvelle_pos != pos_actuelle:
                        actions.append((id_b, nouvelle_pos[0], nouvelle_pos[1], "DEPLACEMENT"))
                        positions_reservees.add(nouvelle_pos)
                        positions_occupees.add(nouvelle_pos)
                    else:
                        positions_occupees.add(pos_actuelle)
            # === FIN DE TON INTEGRATION ===

            else:
                # Si aucune fleur valide trouvée (tout est vide ou loin), mouvement aléatoire
                dest_rand = {"x": random.randint(0, self.ncases - 1), "y": random.randint(0, self.ncases - 1)}
                nouvelle_pos = self.calculer_deplacement_avec_contournement(
                    abeille, dest_rand, positions_occupees | positions_reservees
                )
                if nouvelle_pos:
                    actions.append((id_b, nouvelle_pos[0], nouvelle_pos[1], "DEPLACEMENT"))
                    positions_reservees.add(nouvelle_pos)

        return actions

    # --- FONCTIONS UTILITAIRES NECESSAIRES A TON CODE ---

    def _calculer_nectar_fourni(self, nectar_actuel: int) -> int:
        """
        Simule la logique de la classe Fleur du jeu
        """
        # Si > 66% (33 sur 50), donne 3
        if nectar_actuel >= (self.MAX_NECTAR_FLEUR * 0.66):
            return min(nectar_actuel, 3)
        # Si > 33% (16 sur 50), donne 2
        elif nectar_actuel >= (self.MAX_NECTAR_FLEUR * 0.33):
            return min(nectar_actuel, 2)
        # Sinon donne 1
        else:
            return min(nectar_actuel, 1)

    def calculer_deplacement_avec_contournement(self, abeille, cible, obstacles) -> tuple[int, int]:
        """
        Trouve la prochaine case libre vers la cible.
        """
        depart = abeille["position"]
        dx = cible["x"] - depart["x"]
        dy = cible["y"] - depart["y"]

        directions = []
        # Ordre de préférence : se rapprocher le plus vite possible
        step_x = 1 if dx > 0 else -1
        step_y = 1 if dy > 0 else -1

        if dx != 0: directions.append((step_x, 0))
        if dy != 0: directions.append((0, step_y))

        # On ajoute les autres directions pour contourner si bloqué
        if dx == 0: directions.extend([(1, 0), (-1, 0)])
        if dy == 0: directions.extend([(0, 1), (0, -1)])

        # On teste les mouvements
        for mx, my in directions:
            nx, ny = depart["x"] + mx, depart["y"] + my

            # Vérif limites map
            if not (0 <= nx < self.ncases and 0 <= ny < self.ncases):
                continue

            # Vérif obstacles (ruches adverses ou abeilles prévues ici)
            if (nx, ny) in obstacles:
                continue

            return (nx, ny)

        return None

    def _trouver_meilleure_fleur(self, ma_pos, fleurs):
        """
        Trouve la fleur la plus proche qui a encore du nectar selon notre mémoire > 0
        """
        choix = None
        min_dist = 9999

        for f in fleurs:
            pos_f = (f["x"], f["y"])

            # On ignore les fleurs qu'on pense vides
            if self.nectar_fleurs.get(pos_f, 0) <= 0:
                continue

            d = max(abs(ma_pos["x"] - f["x"]), abs(ma_pos["y"] - f["y"]))
            if d < min_dist:
                min_dist = d
                choix = f

        return choix