from dataclasses import dataclass
from enum import StrEnum

from ia import PositionDict


class DirectionType(StrEnum):
    NORD = "N"
    OUEST = "O"
    EST = "E"
    SUD = "S"
    NORD_OUEST = "NO"
    NORD_EST = "NE"
    SUD_OUEST = "SO"
    SUD_EST = "SE"


@dataclass(frozen=True, slots=True)
class Position:
    """Classe représentant une position avec une coordonnée X (abscisse) et Y (ordonnée)"""

    x: int
    y: int

    def positions_voisines(self) -> dict[DirectionType, "Position"]:
        """Retourne un dictionnaire contenant les positions voisines avec leur direction

        Returns:
            (dict[DirectionType, Position]): Un dictionnaire où chaque clé est la direction et la valeur sa position associée
        """
        return {
            DirectionType.NORD_OUEST: Position(self.x - 1, self.y - 1),
            DirectionType.NORD: Position(self.x, self.y - 1),
            DirectionType.NORD_EST: Position(self.x + 1, self.y - 1),
            DirectionType.EST: Position(self.x + 1, self.y),
            DirectionType.SUD_EST: Position(self.x + 1, self.y + 1),
            DirectionType.SUD: Position(self.x, self.y + 1),
            DirectionType.SUD_OUEST: Position(self.x - 1, self.y + 1),
            DirectionType.OUEST: Position(self.x - 1, self.y),
        }

    def to_dict(self) -> PositionDict:
        """Retourne un dictionnaire représentant cette position

        Returns:
            PositionDict: Un dictionnaire contenant les attributs de cette position
        """
        return {"x": self.x, "y": self.y}
