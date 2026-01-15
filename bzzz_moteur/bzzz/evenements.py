import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, fields
from typing import TYPE_CHECKING, Any, ClassVar, Literal

from bzzz.position import Position
from bzzz.utils import decoder_valeur

if TYPE_CHECKING:
    from bzzz.jeu import Jeu

_REGISTRE_EVENEMENTS: "dict[str, type[Evenement]]" = {}


class Applicable(ABC):
    """Interface permettant de déclarer qu'un évènement s'applique au jeu"""

    __slots__ = ()

    @abstractmethod
    def appliquer(self, jeu: "Jeu") -> None:
        """Applique les conséquences d'un évènement au jeu.

        Par exemple dans le cas d'un évènement d'un nouveau tour, le numéro du tour sera changé dans jeu.

        Args:
            jeu (Jeu): L'instance de jeu
        """
        ...

    @abstractmethod
    def desappliquer(self, jeu: "Jeu") -> None:
        """Desapplique les conséquences d'un évènement au jeu.

        Par exemple dans le cas d'un évènement d'un nouveau tour, le numéro du tour sera remis à son état avant
        cet évènement.

        Args:
            jeu (Jeu): L'instance de jeu
        """
        ...


@dataclass(frozen=True)
class Evenement(ABC):
    """Réprésente un évènement qui s'est passé pendant le jeu"""

    __slots__ = ()

    NOM_EVENEMENT: ClassVar[str]

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if hasattr(cls, "NOM_EVENEMENT"):
            _REGISTRE_EVENEMENTS[cls.NOM_EVENEMENT] = cls

    def serialiser(self) -> str:
        """Transforme l'instance de l'évènement en un équivalent JSON compatible

        Returns:
            str: La chaine de caractères JSON représentant cet évènement et ses attributs
        """
        evenement_dict = asdict(self)
        evenement_dict["_event"] = self.NOM_EVENEMENT

        def set_default(obj: Any) -> list[Any]:
            if isinstance(obj, set):
                return list(obj)
            raise TypeError

        return json.dumps(
            evenement_dict, check_circular=False, indent=None, default=set_default
        )

    @classmethod
    def deserialiser(cls, raw: str) -> "Evenement":
        """Transforme une chaine de caractères JSON générée préalablement par `serialiser` en l'évènement.

        Args:
            raw (str): La chaine de caractères JSON représentant cet évènement et ses attributs

        Returns:
            Evenement: Une instance de l'évènement
        """
        data = json.loads(raw)

        nom_evenement = data.pop("_event")
        evenement_cls = _REGISTRE_EVENEMENTS[nom_evenement]

        kwargs = {}
        for champ in fields(evenement_cls):
            raw_value = data[champ.name]
            kwargs[champ.name] = decoder_valeur(raw_value, champ.type)

        return evenement_cls(**kwargs)

    @abstractmethod
    def message(self, jeu: "Jeu") -> tuple[str, str | None]:
        """Retourne une chaine de caractère à destination d'une lecture humaine expliquant
        ce que fait cet évènement ou ses conséquences.

        Args:
            jeu (Jeu): L'instance de jeu

        Returns:
            (tuple[str, str | None]): La chaine de caractère et une couleur associée si disponible
        """
        ...


@dataclass(frozen=True, slots=True)
class NouveauTourEvenement(Applicable, Evenement):
    """Un évènement représentant un nouveau tour de jeu, ainsi que les abeilles dont le status KO à été modifié"""

    NOM_EVENEMENT: ClassVar[str] = "NOUVEAU_TOUR"

    ancien_tour: int
    nouveau_tour: int
    joueur_idx: int
    abeilles_ids: set[str]

    def appliquer(self, jeu: "Jeu") -> None:
        jeu.tour_actuel = self.nouveau_tour

        assert self.joueur_idx == jeu.index_joueur_actuel

        for abeille in jeu.recuperer_abeilles_joueur(jeu.joueur_actuel):
            if abeille.id in self.abeilles_ids:
                abeille.decrementer_ko()

    def desappliquer(self, jeu: "Jeu") -> None:
        assert self.joueur_idx == jeu.index_joueur_actuel

        for abeille in jeu.recuperer_abeilles_joueur(jeu.joueur_actuel):
            if abeille.id in self.abeilles_ids:
                abeille.incrementer_ko()

        jeu.tour_actuel = self.ancien_tour

    def message(self, jeu: "Jeu") -> tuple[str, str | None]:
        return (
            f"[Nouveau tour] {self.nouveau_tour + 1}/{jeu.constantes.time_out} | Joueur {jeu.joueurs[self.joueur_idx].id}",
            "#D6E3FF",
        )


@dataclass(frozen=True, slots=True)
class JoueurDemandePonteEvenement(Evenement):
    """Un évènement représentant la demande d'un joueur d'effectuer la ponte d'une abeille.
    Il s'agit ici de la demande seulement, l'action n'a pas encore été exécutée.
    """

    NOM_EVENEMENT: ClassVar[str] = "JOUEUR_DEMANDE_PONTE"

    joueur_idx: int
    action_ponte: Literal["OUV", "BOU", "ECL", "RIEN"]

    def message(self, jeu: "Jeu") -> tuple[str, str | None]:
        return (
            f"Le joueur a choisi l'action de ponte: {self.action_ponte}",
            None,
        )


@dataclass(frozen=True, slots=True)
class JoueurPonteEvenement(Applicable, Evenement):
    """Un évènement représentant la ponte d'une abeille par un joueur"""

    NOM_EVENEMENT: ClassVar[str] = "PLAYER_PONTE"

    joueur_idx: int
    id_abeille: str
    type_abeille: Literal["OUV", "BOU", "ECL"]
    nectar: int

    def appliquer(self, jeu: "Jeu") -> None:
        from bzzz.abeille import AbeilleType

        assert self.joueur_idx == jeu.index_joueur_actuel
        assert self.type_abeille in ["OUV", "BOU", "ECL"]

        joueur = jeu.joueur_actuel

        abeille = jeu.creer_abeille(
            self.id_abeille, AbeilleType(self.type_abeille), joueur
        )
        jeu.abeilles.setdefault(joueur.id, []).append(abeille)
        joueur.retirer_nectar(self.nectar)

    def desappliquer(self, jeu: "Jeu") -> None:
        assert self.joueur_idx == jeu.index_joueur_actuel

        joueur = jeu.joueur_actuel

        joueur.ajouter_nectar(self.nectar)

        jeu.abeilles[joueur.id] = [
            a for a in jeu.abeilles[joueur.id] if a.id != self.id_abeille
        ]

    def message(self, jeu: "Jeu") -> tuple[str, str | None]:
        return (
            f"Le joueur a pondu {self.type_abeille} pour {self.nectar} de nectar",
            None,
        )


@dataclass(frozen=True, slots=True)
class JoueurPonteActionIllegaleEvenement(Evenement):
    """Un évènement représentant une erreur car la demande de ponte du joueur était illégale"""

    NOM_EVENEMENT: ClassVar[str] = "JOUEUR_PONTE_ACTION_ILLEGALE"

    raison: str

    def message(self, jeu: "Jeu") -> tuple[str, str | None]:
        return (
            f"Action illégale: {self.raison}",
            "#FFD6D6",
        )


@dataclass(frozen=True, slots=True)
class JoueurActionDemandeEvenement(Evenement):
    """Un évènement représentant la demande d'un joueur d'effectuer une action sur une de ses abeille.
    Il s'agit ici de la demande seulement, l'action n'a pas encore été exécutée.
    """

    NOM_EVENEMENT: ClassVar[str] = "JOUEUR_ACTION_DEMANDE"

    joueur_idx: int
    action: str

    def message(self, jeu: "Jeu") -> tuple[str, str | None]:
        return (
            f"Le joueur a demandé l'action: {self.action}",
            None,
        )


@dataclass(frozen=True, slots=True)
class AbeilleDeplacementEvenement(Applicable, Evenement):
    """Un évènement représentant l'action de déplacement d'une abeille"""

    NOM_EVENEMENT: ClassVar[str] = "ABEILLE_DEPLACEMENT"

    joueur_idx: int
    id_abeille: str
    ancienne_position: Position
    nouvelle_position: Position

    def appliquer(self, jeu: "Jeu") -> None:
        assert self.joueur_idx == jeu.index_joueur_actuel

        abeille = next(
            (
                abeille
                for abeille in jeu.recuperer_abeilles_joueur(jeu.joueur_actuel)
                if abeille.id == self.id_abeille
            ),
            None,
        )
        assert abeille is not None
        assert abeille.position == self.ancienne_position

        abeille.position = self.nouvelle_position

    def desappliquer(self, jeu: "Jeu") -> None:
        assert self.joueur_idx == jeu.index_joueur_actuel

        abeille = next(
            (
                abeille
                for abeille in jeu.recuperer_abeilles_joueur(jeu.joueur_actuel)
                if abeille.id == self.id_abeille
            ),
            None,
        )
        assert abeille is not None
        assert abeille.position == self.nouvelle_position

        abeille.position = self.ancienne_position

    def message(self, jeu: "Jeu") -> tuple[str, str | None]:
        return (
            f"L'abeille {self.id_abeille} s'est déplacée sur {self.nouvelle_position}",
            None,
        )


@dataclass(frozen=True, slots=True)
class AbeilleButinageEvenement(Applicable, Evenement):
    """Un évènement représentant l'action de butinage d'une abeille sur une fleur"""

    NOM_EVENEMENT: ClassVar[str] = "ABEILLE_BUTINAGE"

    joueur_idx: int
    id_abeille: str
    position_fleur: Position
    nectar: int

    def appliquer(self, jeu: "Jeu") -> None:
        assert self.joueur_idx == jeu.index_joueur_actuel

        abeille = next(
            (
                abeille
                for abeille in jeu.recuperer_abeilles_joueur(jeu.joueur_actuel)
                if abeille.id == self.id_abeille
            ),
            None,
        )
        fleur = next((f for f in jeu.fleurs if f.position == self.position_fleur), None)

        assert abeille is not None
        assert fleur is not None

        fleur.retirer_nectar(self.nectar)
        abeille.ajouter_nectar(self.nectar)

    def desappliquer(self, jeu: "Jeu") -> None:
        assert self.joueur_idx == jeu.index_joueur_actuel

        abeille = next(
            (
                abeille
                for abeille in jeu.recuperer_abeilles_joueur(jeu.joueur_actuel)
                if abeille.id == self.id_abeille
            ),
            None,
        )
        fleur = next((f for f in jeu.fleurs if f.position == self.position_fleur), None)

        assert abeille is not None
        assert fleur is not None

        abeille.retirer_nectar(self.nectar)
        fleur.ajouter_nectar(self.nectar)

    def message(self, jeu: "Jeu") -> tuple[str, str | None]:
        return (
            f"L'abeille {self.id_abeille} a butinée {self.nectar} nectar sur la fleur {self.position_fleur}",
            None,
        )


@dataclass(frozen=True, slots=True)
class AbeilleTransfertNectarEvenement(Applicable, Evenement):
    """Un évènement représentant le transfert du nectar d'une abeille dans la ruche d'un joueur"""

    NOM_EVENEMENT: ClassVar[str] = "ABEILLE_TRANSFERT_NECTAR"

    joueur_idx: int
    id_abeille: str
    nectar: int

    def appliquer(self, jeu: "Jeu") -> None:
        assert self.joueur_idx == jeu.index_joueur_actuel

        joueur = jeu.joueur_actuel

        abeille = next(
            (
                abeille
                for abeille in jeu.recuperer_abeilles_joueur(joueur)
                if abeille.id == self.id_abeille
            ),
            None,
        )

        assert abeille is not None

        joueur.ajouter_nectar(self.nectar)
        abeille.retirer_nectar(self.nectar)

        assert abeille.nectar == 0

    def desappliquer(self, jeu: "Jeu") -> None:
        assert self.joueur_idx == jeu.index_joueur_actuel

        joueur = jeu.joueur_actuel

        abeille = next(
            (
                abeille
                for abeille in jeu.recuperer_abeilles_joueur(joueur)
                if abeille.id == self.id_abeille
            ),
            None,
        )

        assert abeille is not None

        abeille.ajouter_nectar(self.nectar)
        joueur.retirer_nectar(self.nectar)

    def message(self, jeu: "Jeu") -> tuple[str, str | None]:
        return (
            f"L'abeille {self.id_abeille} a deposée son nectar ({self.nectar}) dans la ruche",
            None,
        )


@dataclass(frozen=True, slots=True)
class AbeilleActionIllegaleEvenement(Evenement):
    """Un évènement représentant une erreur sur l'action d'une abeille par un joueur car cette action est illégale"""

    NOM_EVENEMENT: ClassVar[str] = "ABEILLE_ACTION_ILLEGALE"

    raison: str

    def message(self, jeu: "Jeu") -> tuple[str, str | None]:
        return (
            f"L'action est illégale: {self.raison}",
            "#FFD6D6",
        )


@dataclass(frozen=True, slots=True)
class AbeilleEscarmoucheEvenement(Evenement):
    """Un évènement représentant une escarmouche entre plusieurs abeilles"""

    NOM_EVENEMENT: ClassVar[str] = "ABEILLE_ESCARMOUCHE"

    escarmouches: list[tuple[str, float, float]]

    def message(self, jeu: "Jeu") -> tuple[str, str | None]:
        return (
            f"{len(self.escarmouches)} abeilles sont en escarmouche !",
            None if len(self.escarmouches) == 0 else "#FFF3D6",
        )


@dataclass(frozen=True, slots=True)
class AbeilleKOEvenement(Applicable, Evenement):
    """Un évènement représentant une abeille qui rate son esquive et tombe KO"""

    NOM_EVENEMENT: ClassVar[str] = "ABEILLE_KO"

    joueur_idx: int
    id_abeille: str
    nectar: int
    ko_temps: int

    def appliquer(self, jeu: "Jeu") -> None:
        assert self.joueur_idx == jeu.index_joueur_actuel

        abeille = next(
            (
                abeille
                for abeille in jeu.abeilles_liste
                if abeille.id == self.id_abeille
            ),
            None,
        )

        assert abeille is not None

        abeille.retirer_nectar(self.nectar)
        abeille.ko_abeille(self.ko_temps)

    def desappliquer(self, jeu: "Jeu") -> None:
        assert self.joueur_idx == jeu.index_joueur_actuel

        abeille = next(
            (
                abeille
                for abeille in jeu.abeilles_liste
                if abeille.id == self.id_abeille
            ),
            None,
        )

        assert abeille is not None

        abeille.ko_abeille(0)
        abeille.ajouter_nectar(self.nectar)

    def message(self, jeu: "Jeu") -> tuple[str, str | None]:
        return (
            f"L'abeille {self.id_abeille} est tombée KO pendant {self.ko_temps} tours perdant {self.nectar} nectar",
            "#FFF3D6",
        )
