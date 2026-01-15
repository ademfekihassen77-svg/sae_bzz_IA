from abc import ABC, abstractmethod
from typing import ClassVar, Literal, TypedDict


class PositionDict(TypedDict):
    x: int
    y: int


class AbeilleDict(TypedDict):
    abeille_type: Literal["OUV", "BOU", "ECL"]
    id: str
    joueur_id: str
    force: int
    max_nectar: int
    position: PositionDict
    ko_temps: int


class AbeilleProprietaireDict(AbeilleDict):
    nectar: int


class JoueurDict(TypedDict):
    id: str
    position: PositionDict
    abeilles: list[AbeilleDict]


class JoueurActuelDict(TypedDict):
    id: str
    position: PositionDict
    nectar: int
    abeilles: list[AbeilleProprietaireDict]


class JeuDict(TypedDict):
    tour_actuel: int
    fleurs: list[PositionDict]
    moi: JoueurActuelDict
    autres_joueurs: list[JoueurDict]


class MoteurIA(ABC):
    nom: ClassVar[str] = ""

    @abstractmethod
    def __init__(
        self, joueur_id: str, ncases: int, max_tours: int, temps_ko: int
    ) -> None: ...

    @abstractmethod
    def ponte(
        self, jeu: JeuDict, cout_ponte: int
    ) -> Literal["OUV", "BOU", "ECL", "RIEN"]: ...

    @abstractmethod
    def action_abeilles(
        self, jeu: JeuDict
    ) -> list[tuple[str, int, int, Literal["DEPLACEMENT", "BUTINAGE"]]]: ...
