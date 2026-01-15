import tkinter as tk
import tkinter.font as tkFont  # noqa: N812


def calculer_meilleur_taille_police(
    canevas: tk.Canvas,
    texte: str,
    ratio_souhaite: float = 0.5,
    famille_police: str = "Helvetica",
) -> int:
    """Permet pour un texte donné de calculer la taille de police
    de caractères idéale pour ne pas dépasser en largeur le ratio de la largeur du canevas

    Args:
        canevas (tk.Canvas): Le canevas
        texte (str): Le texte à faire rentrer en largeur
        ratio_souhaite (float, optional): Le ratio maximal que doit prendre le texte en largeur par rapport au canevas. Valeur par défaut à 0.5.
        famille_police (str, optional): La police de caractères souhaitée. Valeur par défaut à "Helvetica".

    Returns:
        int: _description_
    """
    canevas_largeur = canevas.winfo_width()
    if canevas_largeur == 1:
        canevas.update_idletasks()
        canevas_largeur = canevas.winfo_width()

    largeur_cible = canevas_largeur * ratio_souhaite

    taille = 5
    police = tkFont.Font(family=famille_police, size=taille)

    while police.measure(texte) < largeur_cible:
        taille += 1
        police.configure(size=taille)

    return taille - 1
