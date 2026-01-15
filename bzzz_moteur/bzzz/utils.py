import importlib
import inspect
from pathlib import Path
from typing import Any, get_args, get_origin

from ia import MoteurIA


def recuperer_moteurs_ia(path: Path) -> list[tuple[str, type[MoteurIA]]]:
    """Cherche dans un dossier donné et retourne les fichiers python ayant une classe héritant de `MoteurIA`

    Args:
        path (Path): Le dossier dans lequel scanner les fichiers d'IA

    Returns:
        (list[tuple[str, type[MoteurIA]]]): Une liste contenant pour chaque élément le nom de l'IA et la classe
    """
    moteurs_ia: list[tuple[str, type[MoteurIA]]] = []

    for fichier in [
        fichier for fichier in path.glob("*.py") if fichier.stem != "__init__"
    ]:
        module = importlib.import_module(f"ia.{fichier.stem}")

        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MoteurIA) and obj is not MoteurIA:
                moteurs_ia.append((fichier.name, obj))
                break

    return moteurs_ia


def decoder_valeur(valeur: Any, annotation: Any) -> Any:
    """Fonction permettant de transformer certains types (provenant d'un JSON) en d'autres.

    Args:
        valeur (Any): L'instance de la valeur
        annotation (Any): L'annotation de type de cette valeur

    Returns:
        Any: Le type transformé ou tel quel si aucune transformation n'est nécessaire
    """
    from bzzz.position import Position

    origin = get_origin(annotation)
    args = get_args(annotation)

    # set[str]
    if origin is set:
        return set(valeur)

    # list[tuple[...]]
    if origin is list and args and get_origin(args[0]) is tuple:
        return [tuple(item) for item in valeur]

    # Position (dataclass)
    if annotation is Position:
        return Position(**valeur)

    # tuple simple
    if origin is tuple:
        return tuple(valeur)

    # types simples
    return valeur
