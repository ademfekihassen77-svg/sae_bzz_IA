import tkinter as tk
import tkinter.ttk as ttk


def afficher_fenetre_selection_ia(moteurs_ia_noms: list[str]) -> tuple[list[str], bool]:
    """Affiche une fenêtre graphique permettant à l'utilisateur de configurer une IA pour
    chaque joueur ainsi qu'activer ou non le mode sécurité

    Args:
        moteurs_ia_noms (list[str]): Les noms des IA disponibles qui seront proposés

    Returns:
        (tuple[list[str], bool]): Retourne la liste des IA choisies pour chacun des joueurs et
        un booléen indiquant si l'utilisateur souhaite activer le mode sécurité
    """
    selections_ias: list[str] = []

    tk_selection_ia = tk.Tk()
    tk_selection_ia.title("BZZZ")

    moteurs_ia_noms.insert(0, "")

    def valider() -> None:
        selections_ias.extend(
            [combo_j1.get(), combo_j2.get(), combo_j3.get(), combo_j4.get()]
        )
        tk_selection_ia.destroy()

    frame = tk.Frame(tk_selection_ia, padx=20, pady=20)
    frame.pack()

    label_titre = tk.Label(
        frame, text="Sélectionnez les IA pour chacun des joueurs", font=("Arial", 14)
    )
    label_titre.grid(row=0, column=0, columnspan=2, pady=(0, 20))

    label_j1 = tk.Label(frame, text="Joueur 1")
    label_j1.grid(row=1, column=0, sticky="e", pady=5)
    combo_j1 = ttk.Combobox(frame, values=moteurs_ia_noms, state="readonly", width=20)
    combo_j1.grid(row=1, column=1, pady=5)

    label_j2 = tk.Label(frame, text="Joueur 2")
    label_j2.grid(row=2, column=0, sticky="e", pady=5)
    combo_j2 = ttk.Combobox(frame, values=moteurs_ia_noms, state="readonly", width=20)
    combo_j2.grid(row=2, column=1, pady=5)

    label_j3 = tk.Label(frame, text="Joueur 3")
    label_j3.grid(row=3, column=0, sticky="e", pady=5)
    combo_j3 = ttk.Combobox(frame, values=moteurs_ia_noms, state="readonly", width=20)
    combo_j3.grid(row=3, column=1, pady=5)

    label_j4 = tk.Label(frame, text="Joueur 4")
    label_j4.grid(row=4, column=0, sticky="e", pady=5)
    combo_j4 = ttk.Combobox(frame, values=moteurs_ia_noms, state="readonly", width=20)
    combo_j4.grid(row=4, column=1, pady=5)

    checkbox_mode_securite_var = tk.BooleanVar(tk_selection_ia, value=False)
    checkbox_mode_securite = tk.Checkbutton(
        frame,
        text="Lancer les IA en mode sécurité",
        variable=checkbox_mode_securite_var,
        onvalue=True,
        offvalue=False,
    )
    checkbox_mode_securite.grid(row=5, column=0, columnspan=2, pady=3)

    btn_valider = tk.Button(frame, text="VALIDER", command=valider)
    btn_valider.grid(row=6, column=0, columnspan=2, pady=20)

    tk_selection_ia.mainloop()

    return selections_ias, checkbox_mode_securite_var.get()
