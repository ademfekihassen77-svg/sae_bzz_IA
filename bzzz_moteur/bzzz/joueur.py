from dataclasses import dataclass
from typing import Literal, overload

from bzzz.position import Position
from bzzz.securite import MoteurIASecurise
from ia import (
    AbeilleDict,
    AbeilleProprietaireDict,
    JoueurActuelDict,
    JoueurDict,
    MoteurIA,
)


@dataclass(slots=True)
class Joueur:
    id: str
    position: Position
    nectar: int

    moteur_ia: MoteurIA | MoteurIASecurise | None

    def ajouter_nectar(self, nectar: int) -> None:
        """Ajoute un montant au nectar du joueur

        Args:
            nectar (int): Le montant de nectar à ajouter
        """
        self.nectar += nectar

    def retirer_nectar(self, nectar: int) -> None:
        """Retire un montant au nectar du joueur. Le montant final ne sera jamais négatif.

        Args:
            nectar (int): Le montant de nectar à retirer
        """
        self.nectar = max(self.nectar - nectar, 0)

    def est_position_dans_safezone(self, position: Position) -> bool:
        """Est-ce que la position donnée est dans la zone de protection du joueur ?

        Args:
            position (Position): La position à vérifier

        Returns:
            bool: Retourne `True` si la position est dans la zone de protection, sinon `False`
        """
        for y in range(-3, 4):
            for x in range(-3, 4):
                if position == Position(self.position.x + x, self.position.y + y):
                    return True
        return False

    @overload
    def to_dict(
        self, abeilles: list[AbeilleProprietaireDict], est_proprietaire: Literal[True]
    ) -> JoueurActuelDict: ...

    @overload
    def to_dict(
        self, abeilles: list[AbeilleDict], est_proprietaire: Literal[False]
    ) -> JoueurDict: ...

    def to_dict(
        self,
        abeilles: list[AbeilleProprietaireDict] | list[AbeilleDict],
        est_proprietaire: bool,
    ) -> JoueurDict | JoueurActuelDict:
        """Retourne un dictionnaire représentant les attributs du joueur

        Args:
            abeilles (list[AbeilleProprietaireDict] | list[AbeilleDict]): Une liste d'abeilles appartenant au joueur
            est_proprietaire (bool): Si le joueur est celui du tour actuel

        Returns:
            (JoueurDict | JoueurActuelDict): Le dictionnaire contenant les attributs du joueur.
            Certains attributs ne sont disponibles que si `est_proprieraire` est à `True`.
        """
        if est_proprietaire:
            return {
                "id": self.id,
                "position": self.position.to_dict(),
                "nectar": self.nectar,
                "abeilles": abeilles,  # type: ignore
            }
        else:
            return {
                "id": self.id,
                "position": self.position.to_dict(),
                "abeilles": abeilles,  # type: ignore
            }
