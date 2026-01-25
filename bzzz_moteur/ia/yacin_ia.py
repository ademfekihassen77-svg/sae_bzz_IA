import math
from typing import Literal
from ia import JeuDict, MoteurIA


class MonAI(MoteurIA):
    nom = "SUPER_ABEILLE"

    def __init__(self, joueur_id: str, ncases: int, max_tours: int, temps_ko: int) -> None:
        self.joueur_id = joueur_id
        self.ncases = ncases
        self.max_tours = max_tours
        self.temps_ko = temps_ko
        self.phase_jeu = "DEBUT"
        # Suivi du nectar estimé de chaque fleur : {(x, y): nectar_restant_estimé}
        self.nectar_fleurs = {}
        # Nectar MAX des fleurs selon les constantes du jeu
        self.NECTAR_MAX_FLEUR = 50  # MAX_NECTAR depuis constantes.py
        self.dernier_tour = 0

    def ponte(self, jeu: JeuDict, cout_ponte: int) -> Literal["OUV", "BOU", "ECL", "RIEN"]:
        tour = jeu["tour_actuel"]
        nectar = jeu["moi"]["nectar"]
        mes_abeilles = jeu["moi"]["abeilles"]

        if nectar < cout_ponte:
            return "RIEN"

        # Détection de phase
        if tour < self.max_tours * 0.2:
            self.phase_jeu = "DEBUT"
        elif tour < self.max_tours * 0.7:
            self.phase_jeu = "MILIEU"
        else:
            self.phase_jeu = "FIN"

        nb_ecl = sum(1 for a in mes_abeilles if a["abeille_type"] == "ECL")
        nb_ouv = sum(1 for a in mes_abeilles if a["abeille_type"] == "OUV")
        nb_bou = sum(1 for a in mes_abeilles if a["abeille_type"] == "BOU")

        # Démarrage agressif : tout investir
        if len(mes_abeilles) < 4:
            if nb_ecl < 1: return "ECL"
            return "OUV"

        # Après démarrage : garder réserve
        reserve = cout_ponte * 2
        if nectar < (cout_ponte + reserve):
            return "RIEN"

        # Stratégie par phase
        if self.phase_jeu == "DEBUT":
            if nb_ecl < 2: return "ECL"
            if nb_ouv < 10: return "OUV"

        elif self.phase_jeu == "MILIEU":
            if nb_ouv < 18: return "OUV"
            nb_ennemis_total = sum(len(j["abeilles"]) for j in jeu["autres_joueurs"])
            if nb_ennemis_total > 8 and nb_bou < 3: return "BOU"

        else:  # FIN
            if nb_bou < 4: return "BOU"

        return "RIEN"

    def action_abeilles(self, jeu: JeuDict) -> list[tuple[str, int, int, Literal["DEPLACEMENT", "BUTINAGE"]]]:
        actions = []
        ma_ruche = jeu["moi"]["position"]
        fleurs = jeu["fleurs"]
        tour_actuel = jeu["tour_actuel"]

        # Initialiser le nectar des nouvelles fleurs
        for fleur in fleurs:
            pos_fleur = (fleur["x"], fleur["y"])
            if pos_fleur not in self.nectar_fleurs:
                # Nouvelle fleur détectée, initialiser au max
                self.nectar_fleurs[pos_fleur] = self.NECTAR_MAX_FLEUR

        # Nettoyer les fleurs qui ont disparu
        positions_fleurs_actuelles = {(f["x"], f["y"]) for f in fleurs}
        self.nectar_fleurs = {pos: nectar for pos, nectar in self.nectar_fleurs.items()
                              if pos in positions_fleurs_actuelles}

        abeilles_ennemies = []
        for joueur in jeu["autres_joueurs"]:
            abeilles_ennemies.extend(joueur["abeilles"])

        # Collecter TOUTES les positions occupées (mes abeilles + ennemis)
        positions_occupees = set()

        # Ajouter mes abeilles
        for abeille in jeu["moi"]["abeilles"]:
            pos = abeille["position"]
            positions_occupees.add((pos["x"], pos["y"]))

        # Ajouter ennemis
        for ennemi in abeilles_ennemies:
            pos = ennemi["position"]
            positions_occupees.add((pos["x"], pos["y"]))

        # Positions qui seront réservées ce tour
        positions_reservees = set()

        # Trier abeilles par PRIORITÉ
        abeilles_triees = sorted(
            jeu["moi"]["abeilles"],
            key=lambda a: self._calculer_priorite(a, ma_ruche),
            reverse=True
        )

        for abeille in abeilles_triees:
            if abeille["ko_temps"] > 0:
                continue

            pos = abeille["position"]
            id_b = abeille["id"]

            # Retirer position actuelle des occupées pour cette abeille
            pos_actuelle = (pos["x"], pos["y"])
            positions_occupees.discard(pos_actuelle)

            # A. RETOUR RUCHE (priorité absolue)
            if self._doit_retourner_ruche(abeille, ma_ruche):
                if pos["x"] == ma_ruche["x"] and pos["y"] == ma_ruche["y"]:
                    # Sur ruche : repartir vers fleur
                    fleur = self.trouver_meilleure_fleur(abeille, fleurs, positions_occupees | positions_reservees)
                    if fleur:
                        nouvelle_pos = self.calculer_deplacement_avec_contournement(
                            abeille, fleur, positions_occupees | positions_reservees
                        )
                        if nouvelle_pos and nouvelle_pos != pos_actuelle:
                            actions.append((id_b, nouvelle_pos[0], nouvelle_pos[1], "DEPLACEMENT"))
                            positions_reservees.add(nouvelle_pos)
                            positions_occupees.add(nouvelle_pos)
                        else:
                            positions_occupees.add(pos_actuelle)
                else:
                    # Retour vers ruche
                    nouvelle_pos = self.calculer_deplacement_avec_contournement(
                        abeille, ma_ruche, positions_occupees | positions_reservees
                    )
                    if nouvelle_pos and nouvelle_pos != pos_actuelle:
                        actions.append((id_b, nouvelle_pos[0], nouvelle_pos[1], "DEPLACEMENT"))
                        positions_reservees.add(nouvelle_pos)
                        positions_occupees.add(nouvelle_pos)
                    else:
                        positions_occupees.add(pos_actuelle)
                continue

            # B. BOURDONS - Attaque
            if abeille["abeille_type"] == "BOU" and abeilles_ennemies:
                cible = self.trouver_ennemi_proche(abeille, abeilles_ennemies)
                if cible:
                    nouvelle_pos = self.calculer_deplacement_avec_contournement(
                        abeille, cible["position"], positions_occupees | positions_reservees
                    )
                    if nouvelle_pos and nouvelle_pos != pos_actuelle:
                        actions.append((id_b, nouvelle_pos[0], nouvelle_pos[1], "DEPLACEMENT"))
                        positions_reservees.add(nouvelle_pos)
                        positions_occupees.add(nouvelle_pos)
                    else:
                        positions_occupees.add(pos_actuelle)
                    continue

            # C. BUTINAGE
            if fleurs:
                fleur = self.trouver_meilleure_fleur(abeille, fleurs, positions_occupees | positions_reservees)
                if fleur:
                    pos_fleur = (fleur["x"], fleur["y"])

                    if pos["x"] == fleur["x"] and pos["y"] == fleur["y"]:
                        # Vérifier qu'il reste du nectar avant de butiner
                        nectar_fleur_actuel = self.nectar_fleurs.get(pos_fleur, 0)
                        if nectar_fleur_actuel > 0:
                            # Butiner sur place
                            actions.append((id_b, pos["x"], pos["y"], "BUTINAGE"))
                            positions_occupees.add(pos_actuelle)

                            # Calculer combien de nectar sera collecté selon les règles
                            nectar_fourni = self._calculer_nectar_fourni(nectar_fleur_actuel)
                            nectar_collecte = min(
                                nectar_fourni,
                                abeille["max_nectar"] - abeille["nectar"]
                            )

                            # Déduire le nectar de la fleur
                            self.nectar_fleurs[pos_fleur] = max(0, nectar_fleur_actuel - nectar_collecte)
                        else:
                            # Fleur vide, ne pas butiner
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
            else:
                positions_occupees.add(pos_actuelle)

        return actions

    def calculer_deplacement_avec_contournement(self, abeille, cible, positions_bloquees):
        """
        Calcule le meilleur déplacement avec contournement automatique.
        Ordre de tentative : direct > dessous > dessus > recul
        """
        pos = abeille["position"]

        if isinstance(cible, dict) and "x" in cible:
            cx, cy = cible["x"], cible["y"]
        else:
            cx, cy = cible[0], cible[1]

        dx = cx - pos["x"]
        dy = cy - pos["y"]

        # Si déjà sur cible
        if dx == 0 and dy == 0:
            return (pos["x"], pos["y"])

        mouvements_possibles = []

        # TYPE ÉCLAIREUSE : peut bouger en diagonale
        if abeille["abeille_type"] == "ECL":
            # 1. Mouvement DIRECT (priorité max)
            if dx != 0 and dy != 0:
                direct = (pos["x"] + (1 if dx > 0 else -1), pos["y"] + (1 if dy > 0 else -1))
                mouvements_possibles.append(("direct_diag", direct))

            # 2. Mouvements orthogonaux directs
            if abs(dx) > abs(dy) and dx != 0:
                mouvements_possibles.append(("direct_x", (pos["x"] + (1 if dx > 0 else -1), pos["y"])))
                if dy != 0:
                    mouvements_possibles.append(("direct_y", (pos["x"], pos["y"] + (1 if dy > 0 else -1))))
            elif dy != 0:
                mouvements_possibles.append(("direct_y", (pos["x"], pos["y"] + (1 if dy > 0 else -1))))
                if dx != 0:
                    mouvements_possibles.append(("direct_x", (pos["x"] + (1 if dx > 0 else -1), pos["y"])))

            # 3. CONTOURNEMENT par le bas/haut/côté
            if dx != 0:
                mouvements_possibles.append(("contour_bas", (pos["x"] + (1 if dx > 0 else -1), pos["y"] + 1)))
                mouvements_possibles.append(("contour_haut", (pos["x"] + (1 if dx > 0 else -1), pos["y"] - 1)))
            if dy != 0:
                mouvements_possibles.append(("contour_droite", (pos["x"] + 1, pos["y"] + (1 if dy > 0 else -1))))
                mouvements_possibles.append(("contour_gauche", (pos["x"] - 1, pos["y"] + (1 if dy > 0 else -1))))

            # 4. RECUL si vraiment bloqué
            if dx != 0:
                mouvements_possibles.append(("recul_x", (pos["x"] - (1 if dx > 0 else -1), pos["y"])))
            if dy != 0:
                mouvements_possibles.append(("recul_y", (pos["x"], pos["y"] - (1 if dy > 0 else -1))))

        # TYPE OUVRIÈRE/BOURDON : orthogonal uniquement
        else:
            # 1. Mouvement DIRECT principal
            if abs(dx) >= abs(dy):
                if dx != 0:
                    mouvements_possibles.append(("direct", (pos["x"] + (1 if dx > 0 else -1), pos["y"])))
                # 2. CONTOURNEMENT dessous/dessus
                mouvements_possibles.append(("contour_bas", (pos["x"], pos["y"] + 1)))
                mouvements_possibles.append(("contour_haut", (pos["x"], pos["y"] - 1)))
                # 3. RECUL
                if dx != 0:
                    mouvements_possibles.append(("recul", (pos["x"] - (1 if dx > 0 else -1), pos["y"])))
            else:
                if dy != 0:
                    mouvements_possibles.append(("direct", (pos["x"], pos["y"] + (1 if dy > 0 else -1))))
                # 2. CONTOURNEMENT gauche/droite
                mouvements_possibles.append(("contour_gauche", (pos["x"] - 1, pos["y"])))
                mouvements_possibles.append(("contour_droite", (pos["x"] + 1, pos["y"])))
                # 3. RECUL
                if dy != 0:
                    mouvements_possibles.append(("recul", (pos["x"], pos["y"] - (1 if dy > 0 else -1))))

        # Tester chaque mouvement dans l'ordre
        for type_mouv, (nx, ny) in mouvements_possibles:
            # Vérifier limites du terrain
            if not (0 <= nx < self.ncases and 0 <= ny < self.ncases):
                continue

            # Vérifier si case libre
            if (nx, ny) not in positions_bloquees:
                return (nx, ny)

        # Dernier recours : ne pas bouger
        return (pos["x"], pos["y"])

    def _calculer_nectar_fourni(self, nectar_fleur_actuel):
        """
        Calcule le nectar fourni par la fleur selon son niveau.
        - Si fleur > 2/3 max → fournit 3 nectar
        - Si fleur entre 1/3 et 2/3 max → fournit 2 nectar
        - Sinon → fournit 1 nectar
        """
        seuil_haut = (2 / 3) * self.NECTAR_MAX_FLEUR
        seuil_bas = (1 / 3) * self.NECTAR_MAX_FLEUR

        if nectar_fleur_actuel > seuil_haut:
            return 3
        elif nectar_fleur_actuel > seuil_bas:
            return 2
        else:
            return 1

    def _calculer_priorite(self, abeille, ma_ruche):
        """Calcule priorité : retour ruche > attaque > butinage"""
        pos = abeille["position"]

        # Priorité MAX : abeille pleine doit retourner
        if abeille["nectar"] >= abeille["max_nectar"]:
            return 1000 - self._distance(pos, ma_ruche)

        # Priorité moyenne : bourdons (attaque)
        if abeille["abeille_type"] == "BOU":
            return 500

        # Priorité basse : butinage
        return 100

    def _doit_retourner_ruche(self, abeille, ma_ruche):
        """Vérifie si abeille doit retourner à la ruche"""
        # Pleine : retour immédiat
        if abeille["nectar"] >= abeille["max_nectar"]:
            return True

        return False

    def trouver_meilleure_fleur(self, abeille, fleurs, positions_bloquees):
        """Trouve la meilleure fleur libre avec du nectar restant"""
        pos = abeille["position"]

        # Filtrer fleurs avec nectar ET non occupées
        fleurs_disponibles = []
        for f in fleurs:
            pos_fleur = (f["x"], f["y"])

            # Vérifier si pas occupée (sauf si c'est notre position actuelle)
            if (pos_fleur in positions_bloquees and
                    not (f["x"] == pos["x"] and f["y"] == pos["y"])):
                continue

            # Vérifier qu'il reste du nectar
            nectar_estime = self.nectar_fleurs.get(pos_fleur, self.NECTAR_MAX_FLEUR)
            if nectar_estime <= 0:
                continue

            fleurs_disponibles.append(f)

        # Si aucune fleur disponible avec nectar
        if not fleurs_disponibles:
            # Stratégie de repli : chercher fleurs avec le plus de nectar estimé
            fleurs_avec_nectar = [(f, self.nectar_fleurs.get((f["x"], f["y"]), self.NECTAR_MAX_FLEUR))
                                  for f in fleurs]

            # Trier par nectar restant (décroissant)
            fleurs_avec_nectar.sort(key=lambda x: x[1], reverse=True)

            # Prendre les 3 meilleures
            meilleures_fleurs = [f for f, nectar in fleurs_avec_nectar[:3] if nectar > 0]

            if meilleures_fleurs:
                return min(meilleures_fleurs, key=lambda f: self._distance(pos, f))

            # Dernier recours : réinitialiser l'estimation (peut-être régénération?)
            if fleurs:
                fleur_proche = min(fleurs, key=lambda f: self._distance(pos, f))
                pos_proche = (fleur_proche["x"], fleur_proche["y"])
                self.nectar_fleurs[pos_proche] = self.NECTAR_MAX_FLEUR // 2  # Réinitialiser avec estimation moyenne
                return fleur_proche

            return None

        # Retourner la fleur disponible avec le meilleur score
        # Score = nectar_potentiel / distance (favorise fleurs pleines et proches)
        def calculer_score(f):
            nectar = self.nectar_fleurs.get((f["x"], f["y"]), self.NECTAR_MAX_FLEUR)
            distance = max(1, self._distance(pos, f))
            # On privilégie les fleurs avec beaucoup de nectar
            return nectar / distance

        return max(fleurs_disponibles, key=calculer_score)

    def trouver_ennemi_proche(self, abeille, ennemis):
        """Trouve l'ennemi le plus proche et vivant"""
        pos = abeille["position"]
        vivants = [e for e in ennemis if e["ko_temps"] == 0]
        if not vivants:
            return None
        return min(vivants, key=lambda e: self._distance(pos, e["position"]))

    def _distance(self, pos1, pos2):
        """Distance de Manhattan"""
        if isinstance(pos1, dict):
            x1, y1 = pos1["x"], pos1["y"]
        else:
            x1, y1 = pos1

        if isinstance(pos2, dict):
            x2, y2 = pos2["x"], pos2["y"]
        else:
            x2, y2 = pos2

        return abs(x2 - x1) + abs(y2 - y1)