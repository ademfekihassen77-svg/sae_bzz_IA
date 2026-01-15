import tkinter as tk
from collections.abc import Callable
from enum import Enum, auto
from tkinter.font import Font
from typing import Literal

from bzzz.abeille import Abeille, AbeilleType
from bzzz.constantes import COULEURS_JOUEURS, RATIO_CANEVAS_ECRAN, TAILLE_CUBE
from bzzz.evenements import Applicable
from bzzz.jeu import AbeilleActionType, AbeilleEscarmouche, Jeu
from bzzz.joueur import Joueur
from bzzz.position import Position
from bzzz.ui.tkiteasy import Canevas, ObjetGraphique
from bzzz.ui.utils import calculer_meilleur_taille_police


class JoueurPanneau(tk.Frame):
    """Petit panneau individuel représentant un joueur."""

    def __init__(
        self,
        parent: tk.Misc,
        jeu: Jeu,
        joueur: Joueur,
        couleur_fond: str = "#D0E8FF",
    ):
        super().__init__(parent, bd=1, relief="solid", padx=5, pady=5, bg=couleur_fond)

        self.joueur = joueur
        self.jeu = jeu

        tk.Label(
            self,
            text=f"Joueur: {self.joueur.id}",
            bg=couleur_fond,
            font=("Arial", 11, "bold"),
        ).pack(anchor="w")
        self.nectar_label = tk.Label(self, text="Nectar: N/A", bg=couleur_fond)
        self.stats_label = tk.Label(self, text="", bg=couleur_fond)

        self.nectar_label.pack(anchor="w")
        self.stats_label.pack(anchor="w")

        self.actualiser_stats()

    def actualiser_stats(self) -> None:
        """Actualiser les statistiques du joueur"""
        joueur_abeilles = self.jeu.recuperer_abeilles_joueur(self.joueur)
        nb_abeilles_ouv = len(
            [a for a in joueur_abeilles if a.abeille_type == AbeilleType.OUVRIERE]
        )
        nb_abeilles_bou = len(
            [a for a in joueur_abeilles if a.abeille_type == AbeilleType.BOURDON]
        )
        nb_abeilles_ecl = len(
            [a for a in joueur_abeilles if a.abeille_type == AbeilleType.ECLAIREUSE]
        )

        self.nectar_label.config(text=f"Nectar: {self.joueur.nectar}")
        self.stats_label.config(
            text=f"OUV: {nb_abeilles_ouv} | BOU: {nb_abeilles_bou} | ECL: {nb_abeilles_ecl}"
        )


class JournalEvenements(tk.Frame):
    """L'interface de journal d'évènement"""

    def __init__(
        self, parent: tk.Misc, fenetre: "FenetreJeu", width: int = 40, height: int = 20
    ) -> None:
        super().__init__(parent)

        self.fenetre = fenetre
        self.event_tags: dict[str, int] = {}
        self.texte = tk.Text(
            self,
            width=width,
            height=height,
            wrap="word",
            state="disabled",
            cursor="arrow",
        )
        self.texte.pack(side="left", fill="both", expand=True)

        self.texte.bind("<Double-Button-1>", self.double_click_evenement)

        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.texte.yview)
        self.scrollbar.pack(side="right", fill="y")

        self.texte.config(yscrollcommand=self.scrollbar.set)

        self.tete_lecture_tag = "TETE_LECTURE"
        self.texte.tag_config(
            self.tete_lecture_tag,
            background="#FFF3A0",
        )

    def double_click_evenement(self, evenement: "tk.Event[tk.Text]") -> None:
        """Lorsqu'un évènement est double-cliqué en mode replay et en pause,
        on se déplace dans le temps jusqu'a ce dernier

        Args:
            evenement (tk.Event[tk.Text]): L'évènement tkinter du double-click
        """
        indice = self.texte.index(f"@{evenement.x},{evenement.y}")
        tags = self.texte.tag_names(indice)

        for tag in tags:
            if tag.startswith("evenement_"):
                indice_evenement = self.event_tags[tag]
                self.fenetre.deplacer_replay_vers(indice_evenement)
                return

    def _est_tout_en_bas(self) -> bool:
        """Est-ce que l'utilisateur est tout en bas du journal d'évènement

        Returns:
            bool: `True` si l'utilisateur est tout en bas, `False` sinon
        """
        dernier_element_visible = self.texte.index(f"@0,{self.texte.winfo_height()}")
        derniere_ligne = int(dernier_element_visible.split(".")[0])

        total_lignes = int(self.texte.index("end-1c").split(".")[0])

        return derniere_ligne >= total_lignes

    def ajouter_evenement(
        self,
        message: str,
        couleur_fond: str | None,
        indice_evenement: int,
        scroller: bool = True,
    ) -> None:
        """Ajoute un évènement au journal

        Args:
            message (str): Le message de l'évènement à afficher
            couleur_fond (str | None): Une couleur de fond optionelle
            indice_evenement (int): L'indice de l'évènement dans la liste du jeu, obligatoire pour le mode replay
            scroller (bool, optional): Si l'on scroll automatiquement sur cet évènement, oui par défaut
        """
        etait_tout_en_bas = self._est_tout_en_bas()
        self.texte.config(state="normal")

        indice_debut = self.texte.index("end-1c")
        self.texte.insert("end", message + "\n")
        indice_fin = self.texte.index("end-1c")

        tag = (
            f"evenement_{indice_evenement if indice_evenement != -1 else indice_debut}"
        )
        self.texte.tag_add(tag, indice_debut, indice_fin)
        self.texte.tag_lower(tag, self.tete_lecture_tag)

        if couleur_fond:
            self.texte.tag_configure(tag, background=couleur_fond)

        self.event_tags[tag] = indice_evenement

        self.texte.config(state="disabled")

        if scroller and etait_tout_en_bas:
            self.texte.see("end")

    def deplacer_tete_lecture(self, indice_evenement: int) -> None:
        """Déplace l'indicateur de tête de lecture sur un indice donné. A utiliser
        en mode replay car tout les évènements sont ajoutés dès le début

        Args:
            indice_evenement (int): L'indice de l'évènement sur lequel placer la tête de lecture
        """
        self.texte.tag_remove(self.tete_lecture_tag, "1.0", "end")

        tag = f"evenement_{indice_evenement}"
        ranges = self.texte.tag_ranges(tag)

        if not ranges:
            return

        debut = ranges[0]
        fin = ranges[1]

        self.texte.tag_add(self.tete_lecture_tag, debut, fin)
        self.texte.see(debut)


class LabelCanevas:
    """Classe représentant un label d'abeille avec un cadre en dessous"""

    def __init__(
        self,
        canevas: "CanevasJeu",
        texte: str,
        x: int,
        y: int,
        police: Font,
        padding: int = 1,
        couleur_cadre: str = "#505050",
        couleur_texte: str = "white",
        ancre: Literal["nw", "n", "ne", "w", "center", "e", "sw", "s", "se"] = "center",
    ) -> None:
        self.canevas = canevas
        self.police = police
        self.padding = padding

        self.texte_id = canevas.create_text(
            0,
            0,
            text=texte,
            font=police,
            fill=couleur_texte,
            anchor=ancre,
            tags=("bee_label",),
        )
        self.rect_id = canevas.create_rectangle(
            0,
            0,
            0,
            0,
            fill=couleur_cadre,
            outline="",
            tags=("bee_label_bg",),
        )

        canevas.tag_raise(self.texte_id, "premier_plan")
        canevas.tag_raise(self.rect_id, "premier_plan")
        canevas.tag_lower(self.rect_id, self.texte_id)

        self.deplacer_vers(x, y)

    def supprimer(self) -> None:
        """Supprime le texte et le cadre"""
        self.canevas.delete(self.texte_id)
        self.canevas.delete(self.rect_id)

    def deplacer_vers(self, x: int, y: int) -> None:
        """Déplace le label autour des coordonnées données, on assume que les
        coordonnées données sont le milieu d'une case. Le positionnement est
        intelligent pour éviter de rentrer en collision avec les autres labels
        ainsi que de sortir du canevas

        Args:
            x (int): Coordonnée X du milieu d'une case
            y (int): Coordonnée Y du milieu d'une case
        """
        bbox = self.canevas.bbox(self.texte_id)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        x_label, y_label = self.trouver_position_label(x, y, w, h)
        x_label, y_label = self._maintenir_dans_canevas(x_label, y_label, w, h)

        self.canevas.coords(self.texte_id, x_label, y_label)

        self.ajuster_cadre()

    def ajuster_cadre(self) -> None:
        """Ajuste la position et la taille du cadre pour couvrir le texte"""
        bbox = self.canevas.bbox(self.texte_id)
        self.canevas.coords(
            self.rect_id,
            bbox[0] - self.padding,
            bbox[1] - self.padding,
            bbox[2] + self.padding,
            bbox[3] + self.padding,
        )

    def affecter_texte(self, texte: str) -> None:
        """Change le texte contenu dans le label

        Args:
            texte (str): Le nouveau texte
        """
        self.canevas.itemconfigure(self.texte_id, text=texte)
        self.ajuster_cadre()

    def trouver_position_label(
        self, cx: int, cy: int, largeur: int, hauteur: int
    ) -> tuple[int, int]:
        """Trouve la position idéale en tenant en compte les collisions avec les autres
        labels

        Args:
            cx (int): La position X de référence
            cy (int): La position Y de référence
            largeur (int): La largeur du texte
            hauteur (int): La hauteur du texte

        Returns:
            tuple[int, int]: Retourne les coordonnées (X,Y) idéales
        """
        taille_demi_cube = self.canevas.taille_cube // 2
        marge = 2

        positions = [
            (cx, cy - taille_demi_cube - marge, "s"),
            (cx, cy + taille_demi_cube + marge, "n"),
            (cx - taille_demi_cube - marge, cy, "e"),
            (cx + taille_demi_cube + marge, cy, "w"),
        ]

        for x, y, ancre in positions:
            bx1, by1, bx2, by2 = self._bbox_from_ancre(x, y, largeur, hauteur, ancre)

            if not self._dans_canevas(bx1, by1, bx2, by2):
                continue

            if not self._collision_label(bx1, by1, bx2, by2):
                self.canevas.itemconfigure(self.texte_id, anchor=ancre)
                return x, y

        self.canevas.itemconfigure(self.texte_id, anchor="center")
        return cx, cy

    def _bbox_from_ancre(
        self,
        x: int,
        y: int,
        largeur: int,
        hauteur: int,
        ancre: str,
    ) -> tuple[int, int, int, int]:
        """Calcule les coordonnées finales du texte à partir d'une ancre

        Args:
            x (int): La coordonnée X relative à l'ancre
            y (int): La coordonnée Y relative à l'ancre
            largeur (int): La largeur du texte
            hauteur (int): La hauteur du texte
            ancre (str): L'ancre à prendre en compte

        Raises:
            ValueError: Si l'ancre n'est pas reconnue / gérée

        Returns:
            tuple[int, int, int, int]: Les coordonnées X,Y des deux coins: (x1, y1, x2, y2)
        """
        if ancre == "center":
            return (
                x - largeur // 2,
                y - hauteur // 2,
                x + largeur // 2,
                y + hauteur // 2,
            )

        if ancre == "n":
            return (x - largeur // 2, y, x + largeur // 2, y + hauteur)

        if ancre == "s":
            return (x - largeur // 2, y - hauteur, x + largeur // 2, y)

        if ancre == "e":
            return (x - largeur, y - hauteur // 2, x, y + hauteur // 2)

        if ancre == "w":
            return (x, y - hauteur // 2, x + largeur, y + hauteur // 2)

        raise ValueError(ancre)

    def _maintenir_dans_canevas(
        self, x: int, y: int, largeur: int, hauteur: int
    ) -> tuple[int, int]:
        """S'assure qu'un label ne puisse pas sortir du canevas, retourne des
        coordonnées corrigées si c'est le cas

        Args:
            x (int): La coordonnée X du coin haut-gauche du label
            y (int): La coordonnée Y du coin haut-gauche du label
            largeur (int): La largeur du texte
            hauteur (int): La hauteur du texte

        Returns:
            (tuple[int, int]): La correction du (X,Y) donné en entrée si le texte sort du canevas,
            sinon les mêmes coordonnées sont retournées
        """
        x = max(largeur // 2, min(x, self.canevas.winfo_width() - largeur // 2))
        y = max(hauteur // 2, min(y, self.canevas.winfo_height() - hauteur // 2))
        return x, y

    def _dans_canevas(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """S'assure qu'un rectangle décrit par ses deux coins soit complètement
        dans un canevas

        Args:
            x1 (int): La coordonnée X du coin haut-gauche
            y1 (int): La coordonnée Y du coin haut-gauche
            x2 (int): La coordonnée X du coin bas-droite
            y2 (int): La coordonnée Y du coin bas-droite

        Returns:
            bool: `True` si le rectangle est complètement dans le canevas, `False` sinon
        """
        return (
            x1 >= 0
            and y1 >= 0
            and x2 <= self.canevas.winfo_width()
            and y2 <= self.canevas.winfo_height()
        )

    def _collision_label(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """S'assure qu'un rectangle décrit par ses deux coins ne soit pas en
        collision avec un autre label

        Args:
            x1 (int): La coordonnée X du coin haut-gauche
            y1 (int): La coordonnée Y du coin haut-gauche
            x2 (int): La coordonnée X du coin bas-droite
            y2 (int): La coordonnée Y du coin bas-droite

        Returns:
            bool: `True` si le rectangle est en collision, `False` sinon
        """
        for lx1, ly1, lx2, ly2 in self.canevas.labels_bbox:
            if not (x2 < lx1 or x1 > lx2 or y2 < ly1 or y1 > ly2):
                return True
        return False


class CanevasJeu(Canevas):
    """Le canevas affichant le plateau de jeu, les ruches, les fleurs et les abeilles"""

    def __init__(self, parent: "FenetreJeu", jeu: Jeu, taille_cube: int):
        super().__init__(
            parent,
            jeu.constantes.ncases * taille_cube,
            jeu.constantes.ncases * taille_cube,
        )

        self.parent = parent
        self.jeu = jeu
        self.taille_cube = taille_cube
        self.fleurs_stats: list[ObjetGraphique] = []
        #                  id_abeille    image_abeille  label_abeille
        self.abeilles: dict[str, tuple[ObjetGraphique, LabelCanevas]] = {}

        self.labels_bbox: list[tuple[int, int, int, int]] = []
        self.police_labels = Font(
            family="Helvetica", size=self.taille_police_label(), weight="normal"
        )

        self.configure(bg="green")

        for dy in range(-3, 4):
            for dx in range(-3, 4):
                for indice, joueur_dpos in enumerate(
                    [
                        (0, 0, "#CDE8FF"),
                        (jeu.constantes.ncases - 1, 0, "#FFE4E4"),
                        (
                            jeu.constantes.ncases - 1,
                            jeu.constantes.ncases - 1,
                            "#E6FFE6",
                        ),
                        (0, jeu.constantes.ncases - 1, "#FFF3D6"),
                    ]
                ):
                    if indice == len(self.jeu.joueurs):
                        break

                    position = Position(joueur_dpos[0] + dx, joueur_dpos[1] + dy)

                    if (
                        0 <= position.x < jeu.constantes.ncases
                        and 0 <= position.y < jeu.constantes.ncases
                    ):
                        self.dessinerRectangle(
                            position.x * self.taille_cube,
                            position.y * self.taille_cube,
                            self.taille_cube,
                            self.taille_cube,
                            joueur_dpos[2],
                        )

        for y in range(jeu.constantes.ncases):
            self.dessinerLigne(
                0,
                y * self.taille_cube,
                jeu.constantes.ncases * self.taille_cube,
                y * self.taille_cube,
                "dark green",
            )
        for x in range(jeu.constantes.ncases):
            self.dessinerLigne(
                x * self.taille_cube,
                0,
                x * self.taille_cube,
                jeu.constantes.ncases * self.taille_cube,
                "dark green",
            )

        for indice, joueur in enumerate(self.jeu.joueurs):
            self.afficherImage(
                joueur.position.x * self.taille_cube,
                joueur.position.y * self.taille_cube,
                f"assets/joueur{indice + 1}_ruche.png",
                "nw",
                self.taille_cube,
                self.taille_cube,
                "premier_plan",
            )

        for fleur in jeu.fleurs:
            self.afficherImage(
                fleur.position.x * self.taille_cube,
                fleur.position.y * self.taille_cube,
                "assets/fleur.png",
                "nw",
                self.taille_cube,
                self.taille_cube,
                "premier_plan",
            )
            self.fleurs_stats.append(
                self.afficherTexte(
                    f"{fleur.nectar}/{fleur.max_nectar}",
                    fleur.position.x * self.taille_cube,
                    fleur.position.y * self.taille_cube,
                    ancre="sw",
                    taille=self.taille_police_label(),
                )
            )

    def actualiser_fleurs(self) -> None:
        """Actualise les statistiques des fleurs"""
        for indice, fleur in enumerate(self.jeu.fleurs):
            self.changerTexte(
                self.fleurs_stats[indice], f"{fleur.nectar}/{fleur.max_nectar}"
            )

    def taille_police_label(self) -> int:
        """Calcule la taille de police optimale pour les labels

        Returns:
            int: La taille de police
        """
        return max(10, int(self.taille_cube * 0.3))

    def abeille_label(self, abeille: Abeille) -> str:
        """Construit le label pour une abeille

        Args:
            abeille (Abeille): L'abeille pour laquelle obtenir le label

        Returns:
            str: Le label contenant les informations de l'abeille
        """
        label = ""
        if self.parent.afficher_nom_abeilles.get():
            label += f"{abeille.id} | "

        label += f"{abeille.nectar}" + (
            "" if not abeille.est_ko else f" | KO={abeille.ko_temps}"
        )

        return label

    def actualiser_abeille(self, abeille: Abeille) -> None:
        """Si l'abeille n'existe pas encore sur le canevas on affiche son image
        et son label. Sinon on actualise sa position et son label

        Args:
            abeille (Abeille): L'abeille à actualiser sur le canevas
        """
        x_case = abeille.position.x * self.taille_cube
        y_case = abeille.position.y * self.taille_cube
        x_centre = x_case + self.taille_cube // 2
        y_centre = y_case + self.taille_cube // 2

        if abeille.id not in self.abeilles:
            abeille_image = self.afficherImage(
                abeille.position.x * self.taille_cube,
                abeille.position.y * self.taille_cube,
                f"assets/joueur{self.jeu.recuperer_index_joueur(abeille.joueur) + 1}_abeille_{abeille.abeille_type}.png",
                "nw",
                self.taille_cube,
                self.taille_cube,
                "premier_plan",
            )
            abeille_texte = LabelCanevas(
                self,
                self.abeille_label(abeille),
                x_centre,
                y_centre,
                police=self.police_labels,
            )

            self.abeilles[abeille.id] = (abeille_image, abeille_texte)
        else:
            abeille_image, abeille_texte = self.abeilles[abeille.id]

            self.moveto(
                abeille_image.id,
                abeille.position.x * self.taille_cube,
                abeille.position.y * self.taille_cube,
            )

            abeille_texte.affecter_texte(self.abeille_label(abeille))
            abeille_texte.deplacer_vers(
                x_centre,
                y_centre,
            )

        self.labels_bbox.append(self.bbox(abeille_texte.rect_id))

    def actualiser_abeilles(self) -> None:
        """Actualise toutes les abeilles du jeu, et détruit les abeilles qui n'existent
        plus dans le jeu (ce cas peut arriver quand on remonte dans le temps en mode replay)
        """
        self.labels_bbox.clear()

        jeu_abeilles = self.jeu.abeilles_liste

        if len(self.abeilles) > len(jeu_abeilles):
            abeilles_ids = {a.id for a in jeu_abeilles}
            abeilles_a_supprimer: list[str] = []

            for abeille_id, (abeille_image, abeille_texte) in self.abeilles.items():
                if abeille_id in abeilles_ids:
                    continue
                self.supprimer(abeille_image)
                abeille_texte.supprimer()
                abeilles_a_supprimer.append(abeille_id)

            for abeille_id in abeilles_a_supprimer:
                del self.abeilles[abeille_id]

        for abeille in jeu_abeilles:
            self.actualiser_abeille(abeille)

    def afficher_abeille_action(
        self,
        ancienne_position: Position,
        nouvelle_position: Position,
        action_type: AbeilleActionType,
    ) -> None:
        """Affiche l'action d'une abeille, que ce soit un déplacement ou un butinage

        Args:
            ancienne_position (Position): L'ancienne position dans le cas d'un déplacement, sinon la position actuelle de l'abeille pour un butinage
            nouvelle_position (Position): La nouvelle position en cas de déplacement, sinon la position de la fleur pour un butinage
            action_type (AbeilleActionType): Le type d'action, un déplacement ou un butinage
        """
        case_mouvement = self.dessinerRectangle(
            ancienne_position.x * self.taille_cube + 1,
            ancienne_position.y * self.taille_cube + 1,
            self.taille_cube - 1,
            self.taille_cube - 1,
            COULEURS_JOUEURS[self.jeu.index_joueur_actuel],
            "abeille_action",
        )
        self.tag_lower(case_mouvement.id, "premier_plan")
        case_mouvement = self.dessinerRectangle(
            nouvelle_position.x * self.taille_cube + 1,
            nouvelle_position.y * self.taille_cube + 1,
            self.taille_cube - 1,
            self.taille_cube - 1,
            "#FD7E14"
            if action_type == AbeilleActionType.BUTINAGE
            else COULEURS_JOUEURS[self.jeu.index_joueur_actuel],
            "abeille_action",
        )
        self.tag_lower(case_mouvement.id, "premier_plan")

    def supprimer_abeille_action(self) -> None:
        """Supprime du canevas toutes les actions affichées avec la fonction `afficher_abeille_action`"""
        self.delete("abeille_action")

    def afficher_escarmouches(
        self, escarmouches: list[AbeilleEscarmouche], callback: Callable[..., None]
    ) -> None:
        """Affiche les escarmouches en cours pendant un certain temps, puis appelle la fonction callack

        Args:
            escarmouches (list[AbeilleEscarmouche]): La liste des abeilles prises en escarmouche
            callback (Callable[..., None]): Une fonction à appeler une fois l'affichage de l'escarmouche terminé
        """
        for escarmouche in escarmouches:
            case_escarmouche = self.dessinerRectangle(
                escarmouche.abeille.position.x * self.taille_cube + 1,
                escarmouche.abeille.position.y * self.taille_cube + 1,
                self.taille_cube - 1,
                self.taille_cube - 1,
                "red",
                "bee_battle",
            )
            self.tag_lower(case_escarmouche.id, "premier_plan")

            _, abeille_texte = self.abeilles[escarmouche.abeille.id]

            abeille_texte.affecter_texte(
                f"FE={escarmouche.force_effective:.2f} | E={escarmouche.probabilite_esquive:.2f}"
            )

        def fin_animation() -> None:
            self.delete("bee_battle")
            callback()

        self.after(
            self.parent.delai_ms_avec_facteur(2000) if len(escarmouches) > 0 else 0,
            fin_animation,
        )

    def afficher_classement(self) -> None:
        """Affiche le classement final de la partie, avec la raison de fin de partie"""
        raison_fin_jeu = self.jeu.est_jeu_termine
        joueurs_classement = self.jeu.joueurs_classement

        self.dessinerRectangle(
            0,
            0,
            self.taille_cube * self.jeu.constantes.ncases + 1,
            self.taille_cube * self.jeu.constantes.ncases + 1,
            "white",
        )

        texte_fin_de_jeu = "Fin de partie"
        taille_police = calculer_meilleur_taille_police(
            self, texte_fin_de_jeu, 0.5, "Helvetica"
        )
        police = Font(family="Helvetica", size=taille_police)
        police_hauteur = police.metrics("linespace")

        self.afficherTexte(
            texte_fin_de_jeu,
            (self.taille_cube * self.jeu.constantes.ncases) // 2,
            police_hauteur // 2,
            "black",
            "center",
            taille=taille_police,
        )

        if raison_fin_jeu == "NECTAR_OUTAGE":
            raison = "Aucun nectar restant"
        elif raison_fin_jeu == "BLITZKRIEG":
            raison = "Victoire blitzkrieg"
        elif raison_fin_jeu == "TIME_OUT":
            raison = "Temps écoulé"
        else:
            raison = "Inconnue ?!?"

        taille_police_moitie = taille_police // 2
        police_moitie = Font(family="Helvetica", size=taille_police_moitie)
        police_moitie_hauteur = police_moitie.metrics("linespace")

        texte_raison = self.afficherTexte(
            f"Raison: {raison}",
            (self.taille_cube * self.jeu.constantes.ncases) // 2,
            20 + police_hauteur + 20,
            "black",
            "center",
            taille=taille_police_moitie,
        )

        place = 0
        dernier_nectar: int | None = None
        police_infos: tuple[int, int, int] | None = None

        for joueur in joueurs_classement:
            texte_joueur = f"{joueur.id}: {joueur.nectar} nectar"
            taille_police = calculer_meilleur_taille_police(
                self, texte_joueur, 0.7, "Helvetica"
            )
            font = Font(family="Helvetica", size=taille_police)
            texte_joueur_hauteur = font.metrics("linespace")
            texte_joueur_largeur = font.measure(texte_joueur)

            if police_infos is None or police_infos[0] > taille_police:
                police_infos = (
                    taille_police,
                    texte_joueur_hauteur,
                    texte_joueur_largeur,
                )

        assert police_infos is not None

        objet_y = texte_raison.y + police_moitie_hauteur + (police_infos[1] // 2)

        for joueur in joueurs_classement:
            if dernier_nectar is None:
                place += 1
            elif joueur.nectar < dernier_nectar:
                place += 1

            dernier_nectar = joueur.nectar

            texte_joueur = f"{joueur.id}: {joueur.nectar} nectar"

            t = self.afficherTexte(
                texte_joueur,
                (self.taille_cube * self.jeu.constantes.ncases) // 2,
                objet_y,
                "black",
                "center",
                taille=police_infos[0],
            )
            self.afficherImage(
                t.x - (police_infos[2] // 2) - police_infos[1],
                objet_y - (police_infos[1] // 2),
                f"assets/classement_{place}.png",
                "nw",
                police_infos[1],
                police_infos[1],
            )

            objet_y += police_infos[1] + 20

        self.attendreClic()


class FenetreJeu(tk.Tk):
    def __init__(self, jeu: Jeu, taille_cube: int | None, mode_replay: bool = False):
        super().__init__()
        self.title("BZZZ")
        self.resizable(False, False)
        self.jeu = jeu
        self.facteur_vitesse_log = tk.DoubleVar(value=0.0)
        self.en_pause = False
        self.mode_replay = mode_replay
        self.afficher_nom_abeilles = tk.BooleanVar(value=False)
        self.etat_replay = EtatReplay()

        self.facteur_vitesse_log.trace_add(
            "write", lambda _, __, ___: self.mise_a_jour_vitesse()
        )

        self.update_idletasks()

        # Auto-détection de l'écran pour un affichage optimisé
        if taille_cube is None:
            ecran_largeur = self.winfo_screenwidth()
            ecran_hauteur = self.winfo_screenheight()

            max_plateau = min(ecran_largeur, ecran_hauteur) * RATIO_CANEVAS_ECRAN
            taille_cube = int(max_plateau / self.jeu.constantes.ncases)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(1, weight=1)

        top = tk.Frame(self)
        bottom = tk.Frame(self)
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        bottom.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        top.grid_columnconfigure((0, 1), weight=1)
        bottom.grid_columnconfigure((0, 1), weight=1)

        self.joueurs_panneaux: list[JoueurPanneau] = []

        if len(self.jeu.joueurs) >= 1:
            self.joueur1 = JoueurPanneau(top, jeu, jeu.joueurs[0], "#CDE8FF")
            self.joueur1.grid(row=0, column=0, sticky="ew", padx=5)
            self.joueurs_panneaux.append(self.joueur1)

        if len(self.jeu.joueurs) >= 2:
            self.joueur2 = JoueurPanneau(top, jeu, jeu.joueurs[1], "#FFE4E4")
            self.joueur2.grid(row=0, column=1, sticky="ew", padx=5)
            self.joueurs_panneaux.append(self.joueur2)

        if len(self.jeu.joueurs) >= 3:
            self.joueur3 = JoueurPanneau(bottom, jeu, jeu.joueurs[2], "#E6FFE6")
            self.joueur3.grid(row=0, column=1, sticky="ew", padx=5)
            self.joueurs_panneaux.append(self.joueur3)

        if len(self.jeu.joueurs) == 4:
            self.joueur4 = JoueurPanneau(bottom, jeu, jeu.joueurs[3], "#FFF3D6")
            self.joueur4.grid(row=0, column=0, sticky="ew", padx=5)
            self.joueurs_panneaux.append(self.joueur4)

        self.canevas = CanevasJeu(self, jeu, taille_cube)
        self.canevas.grid(row=1, column=0, sticky="n", padx=10, pady=10)

        panneau_droite = tk.Frame(self)
        panneau_droite.grid(
            row=0, column=1, rowspan=3, sticky="ns", padx=(5, 10), pady=5
        )
        panneau_droite.grid_rowconfigure(1, weight=1)

        panneau_de_controle = tk.Frame(
            panneau_droite, bd=1, relief="solid", padx=10, pady=8
        )
        panneau_de_controle.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        panneau_de_controle.grid_rowconfigure(1, weight=1)
        panneau_de_controle.grid_columnconfigure(1, weight=1)

        slider_vitesse = tk.Scale(
            panneau_de_controle,
            from_=-2.0,
            to=2.0,
            resolution=0.1,
            orient="horizontal",
            variable=self.facteur_vitesse_log,
            length=160,
            showvalue=False,
        )
        slider_vitesse.grid(row=0, column=1)

        self.bouton_pause = tk.Button(
            panneau_de_controle,
            text="⏸",
            width=4,
            command=lambda: self.basculer_pause(),
        )
        self.bouton_pause.grid(row=0, column=2, pady=(5, 0))

        self.label_vitesse = tk.Label(panneau_de_controle, text="x1.0")
        self.label_vitesse.grid(row=0, column=0, pady=(3, 0))
        self.label_vitesse.bind("<Button-1>", lambda _: self.reinitialiser_vitesse())

        checkbox_noms = tk.Checkbutton(
            panneau_de_controle,
            text="Afficher le nom des abeilles",
            variable=self.afficher_nom_abeilles,
            onvalue=True,
            offvalue=False,
            command=lambda: self.canevas.actualiser_abeilles(),
        )
        checkbox_noms.grid(row=1, column=1)

        self.journal_evenements = JournalEvenements(panneau_droite, self, width=70)
        self.journal_evenements.grid(row=1, column=0, sticky="nsew")

    def actualiser_joueurs(self) -> None:
        """Actualise les statistiques de tout les joueurs"""
        for joueur_panel in self.joueurs_panneaux:
            joueur_panel.actualiser_stats()

    def reinitialiser_vitesse(self) -> None:
        """Réinitialise la vitesse de simulation/lecteur à sa vitesse de base"""
        self.facteur_vitesse_log.set(0.0)

    def recuperer_facteur_vitesse(self) -> float:
        """Récupère le facteur logarithmique de vitesse

        Returns:
            float: Un facteur à multiplier à un délai
        """
        return 2 ** self.facteur_vitesse_log.get()

    def delai_ms_avec_facteur(self, ms: int) -> int:
        """Retourne le nombre de millisecondes donnée en entrée modifié en fonction
        de la vitesse choisie

        Args:
            ms (int): Le nombre de millisecondes de base

        Returns:
            int: Le nouveau temps auquel le facteur de vitesse à été appliqué
        """
        return int(ms / self.recuperer_facteur_vitesse())

    def mise_a_jour_vitesse(self) -> None:
        """Mets à jour le label de vitesse avec la vitesse actuelle"""
        self.label_vitesse.config(text=f"x{self.recuperer_facteur_vitesse():.2g}")

    def basculer_pause(self) -> None:
        """Bascule en mode pause si le jeu est en cours, ou inversement"""
        self.en_pause = not self.en_pause
        self.bouton_pause.config(text="▶" if self.en_pause else "⏸")

        if self.en_pause and self.mode_replay:
            self.journal_evenements.texte.config(cursor="hand2")
        else:
            self.journal_evenements.texte.config(cursor="arrow")

    def deplacer_replay_vers(self, cible: int) -> None:
        """En mode replay cela permet de se déplacer dans le temps pour aller à un
        évènement en particulier, fonctionne dans les deux sens

        Args:
            cible (int): L'indice de l'évènement sur lequel revenir
        """
        if not self.en_pause or not self.mode_replay:
            return

        etat_replay = self.etat_replay

        dernier_applique = etat_replay.position_actuelle - 1

        if cible == dernier_applique:
            return

        if cible > dernier_applique:
            debut = dernier_applique + 1
            fin = cible
        else:
            debut = dernier_applique
            fin = cible + 1

        self.jeu.rejouer_evenements_position(
            debut,
            fin,
        )

        etat_replay.position_actuelle = cible + 1

        self.actualiser_joueurs()
        self.canevas.actualiser_abeilles()
        self.canevas.actualiser_fleurs()
        self.journal_evenements.deplacer_tete_lecture(cible)


class EtatJeu(Enum):
    INIT_TOUR = auto()
    PONTE = auto()
    ACTIONS_ABEILLES = auto()
    ESCARMOUCHES = auto()
    FIN_TOUR = auto()
    FIN_JEU = auto()


class ControleurJeu:
    def __init__(self, fenetre: FenetreJeu, jeu: Jeu):
        self.fenetre = fenetre
        self.jeu = jeu
        self.etat = EtatJeu.INIT_TOUR
        self.actions_abeilles: list[tuple[Abeille, Position, AbeilleActionType]] = []
        self.indice_action = 0

    def demarrer_partie(self) -> None:
        self.fenetre.after(0, self.tick)

    def tick(self) -> None:
        if self.etat == EtatJeu.INIT_TOUR:
            self.init_tour()

        elif self.etat == EtatJeu.PONTE:
            self.ponte()

        elif self.etat == EtatJeu.ACTIONS_ABEILLES:
            self.action_abeille()

        elif self.etat == EtatJeu.ESCARMOUCHES:
            self.escarmouches()

        elif self.etat == EtatJeu.FIN_TOUR:
            self.fin_tour()

        elif self.etat == EtatJeu.FIN_JEU:
            self.fin_jeu()

    def after_delay[*P](
        self, ms: int, callback: Callable[[*P], None], *args: *P
    ) -> None:
        if self.fenetre.en_pause:
            self.fenetre.after(100, lambda: self.after_delay(ms, callback))
        else:
            self.fenetre.after(self.fenetre.delai_ms_avec_facteur(ms), callback)

    def init_tour(self) -> None:
        if self.jeu.est_jeu_termine is not None:
            self.etat = EtatJeu.FIN_JEU
            self.after_delay(0, self.tick)
            return

        self.jeu.gerer_initialisation_tour()
        self.fenetre.actualiser_joueurs()
        self.fenetre.canevas.actualiser_abeilles()

        self.etat = EtatJeu.PONTE
        self.after_delay(50, self.tick)

    def ponte(self) -> None:
        action = self.jeu.recuperer_joueur_ponte_action()
        self.jeu.gerer_ponte(action)

        self.fenetre.actualiser_joueurs()
        self.fenetre.canevas.actualiser_abeilles()

        self.actions_abeilles = self.jeu.recuperer_joueur_abeilles_actions()
        self.indice_action = 0

        self.etat = EtatJeu.ACTIONS_ABEILLES
        self.after_delay(300, self.tick)

    def action_abeille(self) -> None:
        if self.indice_action >= len(self.actions_abeilles):
            self.fenetre.canevas.supprimer_abeille_action()
            self.etat = EtatJeu.ESCARMOUCHES
            self.after_delay(50, self.tick)
            return

        abeille, position, type_action = self.actions_abeilles[self.indice_action]
        ancienne_position = abeille.position

        self.jeu.gerer_action_abeille(abeille, position, type_action)
        self.jeu.gerer_abeille_depot_nectar(abeille)

        self.fenetre.canevas.afficher_abeille_action(
            ancienne_position, position, type_action
        )

        self.after_delay(300, self.fin_action_abeille)

    def fin_action_abeille(self) -> None:
        self.fenetre.canevas.actualiser_fleurs()
        self.fenetre.canevas.actualiser_abeilles()
        self.indice_action += 1
        self.after_delay(200, self.tick)

    def escarmouches(self) -> None:
        escarmouches = self.jeu.preparer_escarmouches()
        self.fenetre.canevas.afficher_escarmouches(
            escarmouches, callback=lambda: self.appliquer_escarmouches(escarmouches)
        )

    def appliquer_escarmouches(self, escarmouches: list[AbeilleEscarmouche]) -> None:
        self.jeu.appliquer_escarmouches(escarmouches)
        self.fenetre.actualiser_joueurs()
        self.fenetre.canevas.actualiser_abeilles()

        self.etat = EtatJeu.FIN_TOUR
        self.after_delay(300, self.tick)

    def fin_tour(self) -> None:
        self.etat = EtatJeu.INIT_TOUR
        self.after_delay(50, self.tick)

    def fin_jeu(self) -> None:
        self.fenetre.canevas.afficher_classement()
        self.fenetre.destroy()


def afficher_fenetre_jeu_ia(jeu: Jeu) -> None:
    fenetre = FenetreJeu(jeu, TAILLE_CUBE)

    jeu.definir_callback_evenement(
        lambda ev: fenetre.journal_evenements.ajouter_evenement(*ev.message(jeu), -1)
    )

    fenetre.actualiser_joueurs()

    controller = ControleurJeu(fenetre, jeu)
    controller.demarrer_partie()

    fenetre.mainloop()


class EtatReplay:
    def __init__(self) -> None:
        self.position_actuelle = 0


def afficher_fenetre_jeu_replay(jeu: Jeu) -> None:
    base_attente_ms = 100
    fenetre = FenetreJeu(jeu, TAILLE_CUBE, mode_replay=True)

    fenetre.actualiser_joueurs()

    for idx, ev in enumerate(jeu.evenements):
        fenetre.journal_evenements.ajouter_evenement(*ev.message(jeu), idx, False)

    def boucle_evenement() -> None:
        etat_replay = fenetre.etat_replay
        total = len(jeu.evenements)

        if etat_replay.position_actuelle >= total:
            fenetre.canevas.afficher_classement()
            fenetre.destroy()
            return

        if fenetre.en_pause:
            fenetre.after(
                50,
                boucle_evenement,
            )
            return

        idx = etat_replay.position_actuelle
        evenement = jeu.evenements[idx]

        if isinstance(evenement, Applicable):
            evenement.appliquer(jeu)

            fenetre.actualiser_joueurs()
            fenetre.canevas.actualiser_abeilles()
            fenetre.canevas.actualiser_fleurs()

        fenetre.journal_evenements.deplacer_tete_lecture(idx)

        etat_replay.position_actuelle += 1

        fenetre.after(
            fenetre.delai_ms_avec_facteur(base_attente_ms)
            if isinstance(evenement, Applicable)
            else fenetre.delai_ms_avec_facteur(10),
            boucle_evenement,
        )

    boucle_evenement()

    fenetre.mainloop()
