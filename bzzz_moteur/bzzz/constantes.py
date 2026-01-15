import json
from dataclasses import asdict, dataclass, fields
from typing import Any

from bzzz.utils import decoder_valeur

# Constantes de jeu

# Le nombre de cases du plateau de jeu, doit être pair
NCASES = 16
# Le nombre de fleurs disponibles sur le côté d'un joueur,
# le nombre total de fleurs sur le plateau sera donc NFLEURS * 4
NFLEURS = 4
# Le nectar de départ que possède chaque joueur en début de partie
NECTAR_INITIAL = 5
# Le nombre maximal de nectar que peut contenir une fleur
MAX_NECTAR = 50
# Le nombre de tours maximal de la partie
TIME_OUT = 250
# Le cout en nectar de la ponte d'une abeille
COUT_PONTE = 5
# Le nombre de tours qu'une abeille reste KO après avoir raté son esquive
TIME_KO = 5

# Constantes d'interface

# Remplacez None par un entier pour forcer la taille, sinon c'est calculé
# automatiquement en fonction de la taille de l'écran
TAILLE_CUBE: int | None = None

# Si vous souhaitez changer le ratio de la taille du canevas par rapport à l'écran
RATIO_CANEVAS_ECRAN = 0.6
COULEURS_JOUEURS = ["#A6D2F8", "#FDBCBC", "#BCFFBC", "#FCE1A4"]


@dataclass(frozen=True, slots=True)
class ConstantesJeu:
    ncases: int
    nfleurs: int
    nectar_initial: int
    max_nectar: int
    time_out: int
    cout_ponte: int
    time_ko: int

    def serialiser(self) -> str:
        """Transforme une instance de `ConstantesJeu` en une chaine de caractère JSON

        Returns:
            str: L'équivalent JSON de cette structure de données
        """
        self_dict = asdict(self)
        self_dict["_type"] = "JEU_CONSTANTES"

        return json.dumps(self_dict, check_circular=False, indent=None)

    @classmethod
    def deserialiser(cls, raw: str) -> "ConstantesJeu":
        """Transforme une chaine JSON créée par `serialiser` en une instance de `ConstantesJeu`

        Args:
            raw (str): La chaine de caractère JSON

        Returns:
            ConstantesJeu: Une instance contenant les constantes pré-remplies
        """

        data = json.loads(raw)

        obj_type = data.pop("_type")

        assert obj_type == "JEU_CONSTANTES"

        kwargs: dict[str, Any] = {}
        for field in fields(cls):
            raw_value = data[field.name]
            kwargs[field.name] = decoder_valeur(raw_value, field.type)

        return cls(**kwargs)


def recuperer_constantes_defaut() -> ConstantesJeu:
    """Récupère une instance de `ConstantesJeu` basée sur les constantes définies plus haut

    Returns:
        ConstantesJeu: L'instance pré-remplie
    """

    return ConstantesJeu(
        NCASES, NFLEURS, NECTAR_INITIAL, MAX_NECTAR, TIME_OUT, COUT_PONTE, TIME_KO
    )
