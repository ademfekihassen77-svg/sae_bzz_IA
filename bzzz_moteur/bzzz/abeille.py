from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar, Literal, Self, overload

from .joueur import Joueur
from .position import DirectionType, Position
from ia import AbeilleDict, AbeilleProprietaireDict

class AbeilleType(StrEnum):
    OUVRIERE = "OUV"
    BOURDON = "BOU"
    ECLAIREUSE = "ECL"


@dataclass(slots=True)
class Abeille(ABC):
    abeille_type: ClassVar[AbeilleType]

    id: str
    joueur: Joueur
    force: int
    max_nectar: int
    nectar: int
    position: Position
    ko_temps: int
    a_fait_action: bool = False

    @property
    def est_ko(self) -> bool:
        """Retourne un booléen si l'abeille est KO ou non"""
        return self.ko_temps > 0

    @classmethod
    @abstractmethod
    def creer_abeille(cls, id: str, joueur: Joueur, position: Position) -> Self: ...

    def deplacer(self, position: Position) -> None:
        """Déplace l'abeille à la position donnée

        Args:
            position (Position): La nouvelle position de l'abeille
        """
        self.position = position

    def est_direction_autorise(self, direction: DirectionType) -> bool:
        """Retourne un booléen selon si la direction donnée est possible pour cette abeille.
        Les directions autorisées sont dépendantes du type d'abeille

        Args:
            direction (DirectionType): La direction à vérifier

        Returns:
            bool: `True` si la direction est autorisée, `False` sinon
        """
        return direction not in [
            DirectionType.NORD_OUEST,
            DirectionType.NORD_EST,
            DirectionType.SUD_OUEST,
            DirectionType.SUD_EST,
        ]

    def ajouter_nectar(self, nectar: int) -> None:
        """Ajoute un montant au nectar de l'abeille. Le nouveau montant ne dépassera pas le
        max de nectar de l'abeille

        Args:
            nectar (int): Le montant de nectar à ajouter
        """
        self.nectar = min(self.nectar + nectar, self.max_nectar)

    def retirer_nectar(self, nectar: int) -> None:
        """Retire un montant au nectar de l'abeille. Le nouveau montant aura pour valeur minimale 0

        Args:
            nectar (int): Le montant de nectar à retirer
        """
        self.nectar = max(self.nectar - nectar, 0)

    def vider_nectar(self) -> None:
        """Retire complètement le nectar de l'abeille, le mettant à 0"""
        self.nectar = 0

    def ko_abeille(self, temps: int) -> None:
        """Mets l'abeille KO pendant un nombre de tours donné

        Args:
            temps (int): Le nombre de tours où l'abeille est KO. Si le nombre est égale à 0 alors l'abeille n'est plus KO
        """
        self.ko_temps = temps

    def decrementer_ko(self) -> None:
        """Décrémente de 1 le compteur de tours pendant lequel l'abeille est KO et s'arrête à 0"""
        self.ko_temps = max(self.ko_temps - 1, 0)

    def incrementer_ko(self) -> None:
        """Incrémente de 1 le compteur de tours pendant lequel l'abeille est KO"""
        self.ko_temps += 1

    def force_effective(self, k: int) -> float:
        """Retourne la force effective de l'abeille en fonction du nombre d'enemies qu'elle doit attaquer

        Args:
            k (int): Le nombre d'enemies

        Returns:
            float: La force effective
        """
        return self.force / k

    def probabilite_esquive(self, enemies_efstr: list[float]) -> float:
        """Retourne la probabilité d'esquive de l'abeille en fonction de la force effectives des enemies

        Args:
            enemies_efstr (list[float]): La liste des forces effectives des enemies

        Returns:
            float: La probabilité d'esquive, un nombre flottant entre 0 et 1
        """
        return self.force / (self.force + sum(enemies_efstr))

    @overload
    def to_dict(self, est_prorietaire: Literal[True]) -> AbeilleProprietaireDict: ...

    @overload
    def to_dict(self, est_prorietaire: Literal[False]) -> AbeilleDict: ...

    def to_dict(self, est_prorietaire: bool) -> AbeilleDict | AbeilleProprietaireDict:
        """Retourne un dictionnaire réprésentant l'état de l'abeille.

        Args:
            est_prorietaire (bool): Si `True` alors des informations supplémentaires comme le nectar seront renvoyées

        Returns:
            (AbeilleDict | AbeilleProprietaireDict): Un dictionnaire représentant les attributs de l'abeilles.
            Certains attributs ne sont disponibles que si `est_proprietaire` vaut `True`
        """

        if est_prorietaire:
            return {
                "abeille_type": self.abeille_type,  # type: ignore
                "id": self.id,
                "joueur_id": self.joueur.id,
                "force": self.force,
                "max_nectar": self.max_nectar,
                "nectar": self.nectar,
                "position": self.position.to_dict(),
                "ko_temps": self.ko_temps,
            }
        else:
            return {
                "abeille_type": self.abeille_type,  # type: ignore
                "id": self.id,
                "joueur_id": self.joueur.id,
                "force": self.force,
                "max_nectar": self.max_nectar,
                "position": self.position.to_dict(),
                "ko_temps": self.ko_temps,
            }


@dataclass(slots=True)
class AbeilleOuvriere(Abeille):
    abeille_type: ClassVar[Literal[AbeilleType.OUVRIERE]] = AbeilleType.OUVRIERE

    @classmethod
    def creer_abeille(
        cls, id: str, joueur: Joueur, position: Position
    ) -> "AbeilleOuvriere":
        return AbeilleOuvriere(id, joueur, 1, 12, 0, position, 0)


@dataclass(slots=True)
class AbeilleBourdon(Abeille):
    abeille_type: ClassVar[Literal[AbeilleType.BOURDON]] = AbeilleType.BOURDON

    @classmethod
    def creer_abeille(
        cls, id: str, joueur: Joueur, position: Position
    ) -> "AbeilleBourdon":
        return AbeilleBourdon(id, joueur, 5, 1, 0, position, 0)


@dataclass(slots=True)
class AbeilleEclaireuse(Abeille):
    abeille_type: ClassVar[Literal[AbeilleType.ECLAIREUSE]] = AbeilleType.ECLAIREUSE

    @classmethod
    def creer_abeille(
        cls, id: str, joueur: Joueur, position: Position
    ) -> "AbeilleEclaireuse":
        return AbeilleEclaireuse(id, joueur, 1, 3, 0, position, 0)

    def est_direction_autorise(self, direction: DirectionType) -> bool:
        return True


def generer_id_abeille(type_abeille: AbeilleType, abeilles: list[Abeille]) -> str:
    """Fonction utilitaire permettant de générer un identifiant unique pour une abeille

    Args:
        type_abeille (AbeilleType): Le type d'abeille, ouvrière, éclaireuse ou bourdon
        abeilles (list[Abeille]): La liste des abeilles appartenant à un joueur

    Returns:
        str: Un identifiant unique du style "OUV.0".
    """

    abeille_id = f"{type_abeille}."

    abeille_id += str(
        len([abeille for abeille in abeilles if abeille.abeille_type == type_abeille])
    )

    return abeille_id
