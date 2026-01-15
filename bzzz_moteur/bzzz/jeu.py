import json
import random
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import IO, Literal

from bzzz.abeille import (
    Abeille,
    AbeilleBourdon,
    AbeilleEclaireuse,
    AbeilleOuvriere,
    AbeilleType,
    generer_id_abeille,
)
from bzzz.constantes import ConstantesJeu
from bzzz.evenements import (
    AbeilleActionIllegaleEvenement,
    AbeilleButinageEvenement,
    AbeilleDeplacementEvenement,
    AbeilleEscarmoucheEvenement,
    AbeilleKOEvenement,
    AbeilleTransfertNectarEvenement,
    Applicable,
    Evenement,
    JoueurActionDemandeEvenement,
    JoueurDemandePonteEvenement,
    JoueurPonteActionIllegaleEvenement,
    JoueurPonteEvenement,
    NouveauTourEvenement,
)
from bzzz.fleur import Fleur
from bzzz.joueur import Joueur
from bzzz.position import Position
from bzzz.securite import MoteurIASecurise
from ia import JeuDict, MoteurIA


class AbeilleActionType(StrEnum):
    DEPLACEMENT = "DEPLACEMENT"
    BUTINAGE = "BUTINAGE"


@dataclass(frozen=True, slots=True)
class AbeilleEscarmouche:
    abeille: Abeille
    force_effective: float
    probabilite_esquive: float


class Jeu:
    __slots__ = (
        "abeilles",
        "callback_evenement",
        "constantes",
        "evenements",
        "fleurs",
        "joueurs",
        "total_nectar_initial",
        "tour_actuel",
    )

    def __init__(
        self,
        constantes: "ConstantesJeu",
        joueurs: list[tuple[str, MoteurIA | MoteurIASecurise | None]],
        fleurs: list[Fleur],
    ) -> None:
        self.constantes = constantes
        self.joueurs: list[Joueur] = []
        self.fleurs = fleurs
        self.abeilles: dict[str, list[Abeille]] = {}
        self.total_nectar_initial = (
            sum(f.nectar for f in self.fleurs) + constantes.nectar_initial
        )
        self.tour_actuel = -1
        self.callback_evenement: Callable[[Evenement], None] | None = None

        self.evenements: list[Evenement] = []

        positions: list[Position] = [
            Position(0, 0),
            Position(constantes.ncases - 1, 0),
            Position(constantes.ncases - 1, constantes.ncases - 1),
            Position(0, constantes.ncases - 1),
        ]

        for idx, joueur_infos in enumerate(joueurs):
            self.joueurs.append(
                Joueur(
                    joueur_infos[0],
                    positions[idx],
                    constantes.nectar_initial,
                    joueur_infos[1],
                )
            )

        for joueur in self.joueurs:
            self.abeilles[joueur.id] = []

    def definir_callback_evenement(self, callable: Callable[[Evenement], None]) -> None:
        self.callback_evenement = callable

    def recuperer_abeilles_joueur(self, joueur: Joueur) -> list[Abeille]:
        """Récupère la liste des abeilles d'un joueur

        Args:
            joueur (Joueur): Le joueur dont on veut récupérer les abeilles

        Returns:
            list[Abeille]: Les abeilles de ce joueur
        """
        return self.abeilles[joueur.id]

    def recuperer_index_joueur(self, joueur: Joueur) -> int:
        """Récupère l'indice du joueur dans la liste

        Args:
            joueur (Joueur): Le joueur dont on veut récupérer l'indice

        Raises:
            Exception: Si le joueur n'a pas été trouvé

        Returns:
            int: L'indice du joueur
        """
        for idx, j in enumerate(self.joueurs):
            if j.id == joueur.id:
                return idx
        raise Exception("Le joueur n'a pas été trouvé")

    def to_dict(self) -> JeuDict:
        joueur = self.joueur_actuel
        joueur_abeilles = self.recuperer_abeilles_joueur(joueur)

        return {
            "tour_actuel": self.tour_actuel,
            "fleurs": [f.to_dict() for f in self.fleurs],
            "moi": joueur.to_dict([b.to_dict(True) for b in joueur_abeilles], True),
            "autres_joueurs": [
                j.to_dict(
                    [b.to_dict(False) for b in self.recuperer_abeilles_joueur(j)], False
                )
                for j in self.joueurs
                if j.id != joueur.id
            ],
        }

    @property
    def abeilles_liste(self) -> list[Abeille]:
        """Retourne la liste de toutes les abeilles du jeu

        Returns:
            list[Abeille]: Les abeilles du jeu
        """
        return [abeille for abeilles in self.abeilles.values() for abeille in abeilles]

    @property
    def joueur_actuel(self) -> Joueur:
        """Retourne le joueur dont c'est actuellement le tour

        Returns:
            Joueur: Le joueur en cours
        """
        return self.joueurs[self.index_joueur_actuel]

    @property
    def index_joueur_actuel(self) -> int:
        """Retourne l'indice du joueur dont c'est actuellement le tour

        Returns:
            int: L'indice du joueur en cours
        """
        return self.tour_actuel % len(self.joueurs)

    @property
    def joueurs_classement(self) -> list[Joueur]:
        """Retourne le classement des joueurs selon le nombre de nectar

        Returns:
            list[Joueur]: La liste des joueurs triée par nectar
        """
        return sorted(self.joueurs, key=lambda j: j.nectar, reverse=True)

    @property
    def est_jeu_termine(
        self,
    ) -> Literal["NECTAR_OUTAGE", "BLITZKRIEG", "TIME_OUT"] | None:
        """Indique si le jeu est terminé, et dans le cas échéant la raison de fin de partie

        Returns:
            (Literal["NECTAR_OUTAGE", "BLITZKRIEG", "TIME_OUT"] | None): Retourne `None` si le jeu n'est pas terminé, sinon renvoit un code pour chaque type
            de fin possible
        """
        if all(fleur.nectar == 0 for fleur in self.fleurs) and all(
            bee.nectar == 0 for bee in self.abeilles_liste
        ):
            return "NECTAR_OUTAGE"

        if any(
            joueur.nectar >= self.total_nectar_initial // 2 for joueur in self.joueurs
        ):
            return "BLITZKRIEG"

        if self.tour_actuel + 1 == self.constantes.time_out:
            return "TIME_OUT"

        return None

    def gerer_initialisation_tour(self) -> None:
        """Gère un nouveau tour.

        Conséquences:
        - Le tour actuel est augmenté de 1
        - Pour chaque abeille KO du joueur en cours, on décrémente le nombre de tours en KO
        """
        self.tour_actuel += 1

        joueur = self.joueur_actuel
        joueur_abeilles = self.recuperer_abeilles_joueur(joueur)
        joueur_abeilles_ko_ids = {
            abeille.id for abeille in joueur_abeilles if abeille.est_ko
        }

        for abeille in joueur_abeilles:
            abeille.a_fait_action = False

            if abeille.est_ko:
                abeille.decrementer_ko()

        self.ajouter_evenement(
            NouveauTourEvenement(
                self.tour_actuel - 1,
                self.tour_actuel,
                self.index_joueur_actuel,
                joueur_abeilles_ko_ids,
            )
        )

    def recuperer_joueur_ponte_action(self) -> Literal["OUV", "BOU", "ECL", "RIEN"]:
        """On récupère auprès de l'IA du joueur en cours l'action de ponte qu'il souhaite effectuer.
        Si l'action n'est pas valide "RIEN" est retourné.

        Raises:
            Exception: Si aucune IA pour ce joueur à été trouvé

        Returns:
            (Literal["OUV", "BOU", "ECL", "RIEN"]): Retourne l'une des actions possibles de ponte
        """
        joueur = self.joueur_actuel

        if joueur.moteur_ia is None:
            raise Exception(f"Le joueur {joueur.id} n'a pas d'IA !")

        action = joueur.moteur_ia.ponte(self.to_dict(), self.constantes.cout_ponte)

        if action == "CRASH":
            self.ajouter_evenement(
                JoueurPonteActionIllegaleEvenement(
                    "L'IA du joueur à plantée et n'a pas pu fournir de réponse pour l'opération 'ponte'"
                )
            )
            return "RIEN"
        if action == "TIMEOUT":
            self.ajouter_evenement(
                JoueurPonteActionIllegaleEvenement(
                    "L'IA du joueur n'a pas répondue dans le délai imparti pour l'opération 'ponte'"
                )
            )
            return "RIEN"

        self.ajouter_evenement(
            JoueurDemandePonteEvenement(self.index_joueur_actuel, action)
        )

        if not isinstance(action, str):
            self.ajouter_evenement(
                JoueurPonteActionIllegaleEvenement(
                    "L'action n'est pas une chaine de caractères !"
                )
            )
            return "RIEN"
        if action not in ["OUV", "BOU", "ECL", "RIEN"]:
            self.ajouter_evenement(
                JoueurPonteActionIllegaleEvenement(
                    "L'action n'est pas un choix attendu !"
                )
            )
            return "RIEN"

        return action

    def creer_abeille(
        self, id_abeille: str, type_abeille: AbeilleType, joueur: Joueur
    ) -> Abeille:
        """Instancie une nouvelle abeille en fonction de son type.

        Args:
            id_abeille (str): L'identifiant unique de l'abeille
            type_abeille (AbeilleType): Le type d'abeille (ouvrière, bourdon, éclaireuse)
            joueur (Joueur): Le joueur auquel appartient l'abeille

        Returns:
            Abeille: L'instance de l'abeille créée
        """
        match type_abeille:
            case AbeilleType.OUVRIERE:
                abeille: Abeille = AbeilleOuvriere.creer_abeille(
                    id_abeille, joueur, joueur.position
                )
            case AbeilleType.BOURDON:
                abeille = AbeilleBourdon.creer_abeille(
                    id_abeille, joueur, joueur.position
                )
            case AbeilleType.ECLAIREUSE:
                abeille = AbeilleEclaireuse.creer_abeille(
                    id_abeille, joueur, joueur.position
                )

        return abeille

    def gerer_ponte(
        self, action_ponte: Literal["OUV", "BOU", "ECL", "RIEN"]
    ) -> Abeille | None:
        """Valide l'action de ponte donnée et le cas échéant créer une nouvelle abeille

        Args:
            action_ponte (Literal["OUV", "BOU", "ECL", "RIEN"]): L'action de ponte

        Returns:
            (Abeille | None): Retourne l'abeille pondue si l'action à bien été effectuée, sinon `None`
        """
        joueur = self.joueur_actuel

        if action_ponte == "RIEN":
            return None

        if joueur.nectar < self.constantes.cout_ponte:
            self.ajouter_evenement(
                JoueurPonteActionIllegaleEvenement("Le joueur n'a pas assez de nectar")
            )
            return None

        if any(
            True
            for abeille in self.recuperer_abeilles_joueur(joueur)
            if abeille.position == joueur.position
        ):
            self.ajouter_evenement(
                JoueurPonteActionIllegaleEvenement(
                    "Une abeille est déjà présente sur la ruche"
                )
            )
            return None

        id_abeille = (
            generer_id_abeille(action_ponte, self.recuperer_abeilles_joueur(joueur))  # type: ignore
            + f".{len(self.abeilles_liste)}"
        )

        abeille = self.creer_abeille(id_abeille, action_ponte, joueur)  # type: ignore

        self.abeilles.setdefault(joueur.id, []).append(abeille)

        joueur.retirer_nectar(self.constantes.cout_ponte)

        self.ajouter_evenement(
            JoueurPonteEvenement(
                self.index_joueur_actuel,
                id_abeille,
                action_ponte,
                self.constantes.cout_ponte,
            )
        )

        return abeille

    def recuperer_joueur_abeilles_actions(
        self,
    ) -> list[tuple[Abeille, Position, AbeilleActionType]]:
        """Récupère auprès de l'IA du joueur en cours les actions qu'il souhaite effectuer pour chacune
        de ses abeilles. Chaque action est vérifiée sur sa forme. Si une action n'est pas lisible, elle est ignorée.

        Raises:
            Exception: Si le joueur en cours ne possède pas d'IA

        Returns:
            (list[tuple[Abeille, Position, AbeilleActionType]]): La liste des actions par abeille
        """
        joueur = self.joueur_actuel
        joueur_abeilles = self.recuperer_abeilles_joueur(joueur)

        if joueur.moteur_ia is None:
            raise Exception(f"Le joueur {joueur.id} n'a pas d'IA !")

        joueur_abeilles_actions = joueur.moteur_ia.action_abeilles(self.to_dict())
        abeilles_actions: list[tuple[Abeille, Position, AbeilleActionType]] = []

        if joueur_abeilles_actions == "CRASH":
            self.ajouter_evenement(
                AbeilleActionIllegaleEvenement(
                    "L'IA du joueur à plantée et n'a pas pu fournir de réponse pour l'opération 'action_abeilles'"
                )
            )
            return abeilles_actions
        if joueur_abeilles_actions == "TIMEOUT":
            self.ajouter_evenement(
                AbeilleActionIllegaleEvenement(
                    "L'IA du joueur n'a pas répondue dans le délai imparti pour l'opération 'action_abeilles'"
                )
            )
            return abeilles_actions

        if not isinstance(joueur_abeilles_actions, list):
            self.ajouter_evenement(
                AbeilleActionIllegaleEvenement("L'objet reçu n'est pas une liste !")
            )
            return abeilles_actions

        for action_abeille in joueur_abeilles_actions:
            self.ajouter_evenement(
                JoueurActionDemandeEvenement(
                    self.index_joueur_actuel, str(action_abeille)
                )
            )

            if not isinstance(action_abeille, tuple) or len(action_abeille) != 4:
                self.ajouter_evenement(
                    AbeilleActionIllegaleEvenement("L'objet reçu n'est pas une liste !")
                )
                continue

            id_abeille, abeille_x, abeille_y, type_action = action_abeille

            if not isinstance(id_abeille, str):
                self.ajouter_evenement(
                    AbeilleActionIllegaleEvenement(
                        "L'ID de l'abeille n'est pas une chaine de caractères !"
                    )
                )
                continue
            if not isinstance(abeille_x, int):
                self.ajouter_evenement(
                    AbeilleActionIllegaleEvenement(
                        "La position X de l'abeille n'est pas un entier !"
                    )
                )
                continue
            if not isinstance(abeille_y, int):
                self.ajouter_evenement(
                    AbeilleActionIllegaleEvenement(
                        "La position Y de l'abeille n'est pas un entier !"
                    )
                )
                continue
            if not isinstance(type_action, str):
                self.ajouter_evenement(
                    AbeilleActionIllegaleEvenement(
                        "Le type d'action n'est pas une chaine de caractères !"
                    )
                )
                continue
            if type_action not in ["DEPLACEMENT", "BUTINAGE"]:
                self.ajouter_evenement(
                    AbeilleActionIllegaleEvenement(
                        "Le type d'action n'est pas un choix attendu !"
                    )
                )
                continue

            abeille = next(
                (abeille for abeille in joueur_abeilles if abeille.id == id_abeille),
                None,
            )

            if abeille is None:
                self.ajouter_evenement(
                    AbeilleActionIllegaleEvenement(
                        f"Aucune abeille trouvée pour l'ID {id_abeille}"
                    )
                )
                continue
            if abeille.joueur.id != self.joueur_actuel.id:
                self.ajouter_evenement(
                    AbeilleActionIllegaleEvenement(
                        f"L'abeille {id_abeille} n'appartient pas au joueur actuel !"
                    )
                )
                continue

            abeilles_actions.append(
                (
                    abeille,
                    Position(abeille_x, abeille_y),
                    AbeilleActionType(type_action),
                )
            )

        return abeilles_actions

    def recuperer_abeille_actions_autorisees(
        self, abeille: Abeille | None
    ) -> tuple[list[Position], list[Fleur]]:
        """Pour une abeille donnée, retourne les actions autorisées, que ce soit en déplacement
        ou en butinage.

        Args:
            abeille (Abeille | None): L'abeille dont on veux les actions possibles

        Returns:
            (tuple[list[Position], list[Fleur]]): Deux listes, la première contenant les positions sur lequelles
            l'abeille peut se déplacer, et la deuxième contenant la liste des fleurs qu'elle peut butiner
        """

        positions_autorisees: list[Position] = []
        fleurs_autorisees: list[Fleur] = []
        joueur = self.joueur_actuel

        if abeille is None or abeille.est_ko or abeille.a_fait_action:
            return positions_autorisees, fleurs_autorisees

        positions_autorisees.append(abeille.position)
        fleur = next((f for f in self.fleurs if f.position == abeille.position), None)

        if fleur is not None:
            fleurs_autorisees.append(fleur)

        for direction, position in abeille.position.positions_voisines().items():
            fleur = next((f for f in self.fleurs if f.position == position), None)

            if fleur is not None:
                fleurs_autorisees.append(fleur)

            if not abeille.est_direction_autorise(direction):
                continue
            if (
                position.x < 0
                or position.x >= self.constantes.ncases
                or position.y < 0
                or position.y >= self.constantes.ncases
            ):
                continue
            if any(
                True
                for j in self.joueurs
                if j.id != joueur.id and j.est_position_dans_safezone(position)
            ):
                continue

            if any(
                True for abeille in self.abeilles_liste if abeille.position == position
            ):
                continue

            positions_autorisees.append(position)

        return positions_autorisees, fleurs_autorisees

    def gerer_action_abeille(
        self, abeille: Abeille, position: Position, type_action: AbeilleActionType
    ) -> None:
        """Valide une action demandée pour une abeille, si l'action est valide alors l'abeille est déplacée ou butine
        la fleur

        Args:
            abeille (Abeille): L'abeille sur laquelle on souhaite effectuer une action
            position (Position): La position soit du déplacement, soit de la fleur sur laquelle butiner
            type_action (AbeilleActionType): Le type d'action, un déplacement ou un butinage
        """
        if abeille.est_ko:
            self.ajouter_evenement(
                AbeilleActionIllegaleEvenement(
                    f"L'abeille {abeille.id} est KO, elle ne peut pas effectuer d'action"
                )
            )
            return
        if abeille.a_fait_action:
            self.ajouter_evenement(
                AbeilleActionIllegaleEvenement(
                    f"L'abeille {abeille.id} à déjà effectuée une action dans ce tour"
                )
            )
            return

        positions_autorisees, fleurs_autorisees = (
            self.recuperer_abeille_actions_autorisees(abeille)
        )
        abeille.a_fait_action = (
            True  # Important d'être après recuperer_abeille_actions_autorisees()
        )

        if type_action == AbeilleActionType.DEPLACEMENT:
            if position in positions_autorisees:
                old_position = abeille.position
                abeille.position = position

                self.ajouter_evenement(
                    AbeilleDeplacementEvenement(
                        self.index_joueur_actuel, abeille.id, old_position, position
                    )
                )
            else:
                self.ajouter_evenement(
                    AbeilleActionIllegaleEvenement(
                        f"L'abeille {abeille.id} ne peut pas se déplacer sur {position}"
                    )
                )
        elif type_action == AbeilleActionType.BUTINAGE:
            fleur = next((f for f in fleurs_autorisees if f.position == position), None)

            if fleur is not None:
                nectar = fleur.lacher_nectar()
                abeille.ajouter_nectar(nectar)

                self.ajouter_evenement(
                    AbeilleButinageEvenement(
                        self.index_joueur_actuel, abeille.id, fleur.position, nectar
                    )
                )
            else:
                self.ajouter_evenement(
                    AbeilleActionIllegaleEvenement(
                        f"L'abeille {abeille.id} ne peut butiner à {position} car aucune fleur"
                    )
                )
        else:
            self.ajouter_evenement(
                AbeilleActionIllegaleEvenement("Le type d'action n'est pas reconnu !")
            )

    def gerer_abeille_depot_nectar(self, abeille: Abeille) -> bool:
        """Si l'abeille est dans la safezone de son joueur, elle dépose tout son nectar
        dans la ruche (joueur)

        Args:
            abeille (Abeille): L'abeille à vérifier

        Returns:
            bool: Retourne `True` si l'abeille à déposée au moins 1 de nectar, `False` sinon
        """
        joueur = abeille.joueur

        if abeille.est_ko:
            return False

        if joueur.est_position_dans_safezone(abeille.position) and abeille.nectar > 0:
            nectar = abeille.nectar
            joueur.ajouter_nectar(nectar)
            abeille.vider_nectar()

            self.ajouter_evenement(
                AbeilleTransfertNectarEvenement(
                    self.index_joueur_actuel, abeille.id, nectar
                )
            )

            return True

        return False

    def preparer_escarmouches(self) -> list[AbeilleEscarmouche]:
        """Regarde les abeilles du joueur en cours qui ont des abeilles enemis voisines,
        pour chacune d'entre elle on calcul la force effective et la probabilité d'esquive

        Returns:
            list[AbeilleEscarmouche]: Une liste où pour chaque abeille dans l'escarmouche,
            on a la force effective et la probabilité d'esquive
        """
        joueur = self.joueur_actuel
        joueur_abeilles = self.recuperer_abeilles_joueur(joueur)
        abeilles_force_effective: dict[str, float] = {}
        abeilles_en_combat: list[tuple[Abeille, list[Abeille]]] = []
        abeilles_a_analyser = [
            abeille for abeille in joueur_abeilles if not abeille.est_ko
        ]
        abeilles_explorees = {abeille.id for abeille in abeilles_a_analyser}
        escarmouches: list[AbeilleEscarmouche] = []

        while len(abeilles_a_analyser) > 0:
            abeille = abeilles_a_analyser.pop()
            positions_voisines = abeille.position.positions_voisines().values()

            if abeille.joueur.id == joueur.id:
                abeilles_voisines_enemies = [
                    b
                    for b in self.abeilles_liste
                    if b.position in positions_voisines
                    and b.joueur.id != joueur.id
                    and not b.est_ko
                ]
            else:
                abeilles_voisines_enemies = [
                    b
                    for b in joueur_abeilles
                    if b.position in positions_voisines and not b.est_ko
                ]

            if len(abeilles_voisines_enemies) == 0:
                continue

            abeille_force_effective = abeille.force_effective(
                len(abeilles_voisines_enemies)
            )

            abeilles_force_effective[abeille.id] = abeille_force_effective
            abeilles_en_combat.append((abeille, abeilles_voisines_enemies))

            for abeille_enemie in abeilles_voisines_enemies:
                if abeille_enemie.id in abeilles_explorees:
                    continue
                abeilles_a_analyser.append(abeille_enemie)
                abeilles_explorees.add(abeille_enemie.id)

        for abeille, abeilles_voisines_enemies in abeilles_en_combat:
            abeille_force_effective = abeilles_force_effective[abeille.id]
            abeille_prob_esquive = abeille.probabilite_esquive(
                [abeilles_force_effective[b.id] for b in abeilles_voisines_enemies]
            )

            escarmouches.append(
                AbeilleEscarmouche(
                    abeille,
                    abeille_force_effective,
                    abeille_prob_esquive,
                )
            )

        self.ajouter_evenement(
            AbeilleEscarmoucheEvenement(
                [
                    (b.abeille.id, b.force_effective, b.probabilite_esquive)
                    for b in escarmouches
                ]
            )
        )

        return escarmouches

    def appliquer_escarmouches(self, escarmouches: list[AbeilleEscarmouche]) -> None:
        """A partir d'une résultat d'escamourche, on test la probabilité d'esquive.
        Si l'esquive échoue on met l'abeille KO pour le nombre de tours définit.

        Args:
            escarmouches (list[AbeilleEscarmouche]): Les abeilles prises dans l'escarmouche
        """
        for escarmouche in escarmouches:
            if not random.random() <= escarmouche.probabilite_esquive:
                nectar = escarmouche.abeille.nectar
                escarmouche.abeille.vider_nectar()
                escarmouche.abeille.ko_abeille(self.constantes.time_ko)

                self.ajouter_evenement(
                    AbeilleKOEvenement(
                        self.index_joueur_actuel,
                        escarmouche.abeille.id,
                        nectar,
                        self.constantes.time_ko,
                    )
                )

    def ajouter_evenement(self, evenement: Evenement) -> None:
        """Ajout un nouvel évènement à la journalisation des évènements du jeu

        Args:
            evenement (Evenement): L'évènement à rajouter
        """
        self.evenements.append(evenement)

        if self.callback_evenement is not None:
            self.callback_evenement(evenement)

    def rejouer_evenements_position(self, indice_depart: int, indice_fin: int) -> None:
        """Rejoue la séquence d'évènements depuis indice_depart jusqu'à
        indice_fin, les deux bornes incluses. Si la direction est négative (remonter
        dans le temps), alors les évènements sont désappliqués.

        Args:
            indice_depart (int): L'indice de départ inclus de la séquence
            indice_fin (int): L'indice de fin inclus de la séquence
        """
        if indice_depart == indice_fin:
            return

        direction = 1 if indice_fin > indice_depart else -1

        while indice_depart != indice_fin + direction:
            evenement = self.evenements[indice_depart]

            if isinstance(evenement, Applicable) and direction == 1:
                evenement.appliquer(self)
            elif isinstance(evenement, Applicable) and direction == -1:
                evenement.desappliquer(self)

            indice_depart += direction

    def ecrire_replay_dans_fichier(self, obj_fichier: IO[str]) -> None:
        """Ecrit le contenu du fichier de replay dans un objet file-like

        Args:
            obj_fichier (IO[str]): L'objet file-like
        """
        obj_fichier.write(self.constantes.serialiser() + "\n")

        joueurs_dict = json.dumps(
            {"_type": "JEU_JOUEURS", "joueurs": [j.id for j in self.joueurs]},
            check_circular=False,
            indent=None,
        )

        obj_fichier.write(joueurs_dict + "\n")

        fleurs_dict = json.dumps(
            {
                "_type": "JEU_FLEURS",
                "fleurs": [
                    (f.position.x, f.position.y, f.max_nectar) for f in self.fleurs
                ],
            },
            check_circular=False,
            indent=None,
        )

        obj_fichier.write(fleurs_dict + "\n")

        for evenement in self.evenements:
            obj_fichier.write(evenement.serialiser() + "\n")

    @classmethod
    def creer_jeu_depuis_fichier_replay(cls, obj_fichier: IO[str]) -> "Jeu":
        """A partir d'un objet file-like qui contient un replay, créé la partie

        Args:
            obj_fichier (IO[str]): Un objet file-like

        Raises:
            Exception: Si quelque chose s'est mal passé avec la lecture du fichier

        Returns:
            Jeu: L'instance de jeu initialisée au début mais contenant tous les évènements qui se sont déroulés
        """
        ligne_index = 0
        jeu_constantes: ConstantesJeu | None = None
        noms_joueurs: list[str] | None = None
        fleurs_infos: list[list[int]] | None = None
        evenements: list[Evenement] = []

        while ligne := obj_fichier.readline():
            ligne = ligne.rstrip()

            if ligne_index == 0:
                jeu_constantes = ConstantesJeu.deserialiser(ligne)
            elif ligne_index == 1:
                noms_joueurs = json.loads(ligne)["joueurs"]
            elif ligne_index == 2:
                fleurs_infos = json.loads(ligne)["fleurs"]
            else:
                evenements.append(Evenement.deserialiser(ligne))

            ligne_index += 1

        if (
            jeu_constantes is None
            or noms_joueurs is None
            or fleurs_infos is None
            or len(evenements) == 0
        ):
            raise Exception(
                "Quelque chose s'est mal passé avec la lecture du fichier !"
            )

        jeu = Jeu(
            jeu_constantes,
            [(nom, None) for nom in noms_joueurs],
            [Fleur(Position(f[0], f[1]), f[2], f[2]) for f in fleurs_infos],
        )

        jeu.evenements = evenements

        return jeu
