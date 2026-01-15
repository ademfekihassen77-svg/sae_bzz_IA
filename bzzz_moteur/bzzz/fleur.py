from dataclasses import dataclass

from bzzz.position import Position
from ia import PositionDict


@dataclass(slots=True)
class Fleur:
    position: Position
    nectar: int
    max_nectar: int

    def lacher_nectar(self) -> int:
        """Retourne un montant de nectar simulant le butinage de cette fleur.
        Ce montant est déduis du montant de la fleur.

        Si le nectar restant est au dessus de deux tiers:
            Donne jusqu'à 3 de nectar
        Sinon si le nectar restant est au dessus d'un tier:
            Donne jusqu'à 2 de nectar
        Sinon:
            Donne jusqu'à 1 de nectar

        Le nectar restant dans la fleur ne tombera jamais en négatif.

        Returns:
            int: Le nectar récupéré après butinage
        """
        nectar_to_drop = 0
        if self.nectar / self.max_nectar >= 0.66:
            nectar_to_drop = min(self.nectar, 3)
        elif self.nectar / self.max_nectar >= 0.33:
            nectar_to_drop = min(self.nectar, 2)
        else:
            nectar_to_drop = min(self.nectar, 1)

        self.nectar -= nectar_to_drop

        return nectar_to_drop

    def ajouter_nectar(self, nectar: int) -> None:
        """Ajoute un montant au nectar de la fleur, ne peut pas dépasser le maximum de nectar

        Args:
            nectar (int): Le montant de nectar à ajouter
        """
        self.nectar = min(self.nectar + nectar, self.max_nectar)

    def retirer_nectar(self, nectar: int) -> None:
        """Retire un montant au nectar de la fleur, ne peut pas descendre en dessous de 0

        Args:
            nectar (int): Le montant de nectar à retirer
        """
        self.nectar = max(self.nectar - nectar, 0)

    def est_position_proche(self, position: Position) -> bool:
        """Est-ce que la position donnée est dans les 8 cases voisines de la fleur

        Args:
            position (Position): La position à vérifier

        Returns:
            bool: Retourne `True` si la position est voisine, sinon `False`
        """
        if position == self.position:
            return True

        for position_voisine in self.position.positions_voisines().values():
            if position == position_voisine:
                return True

        return False

    def to_dict(self) -> PositionDict:
        """Retourne un dictionnaire représentant la position de la fleur

        Returns:
            PositionDict: Un dictionnaire contenant la position X et Y de la fleur
        """
        return self.position.to_dict()
