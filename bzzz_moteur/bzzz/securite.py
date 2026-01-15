import sys
import time
from multiprocessing import get_context
from typing import Any, Literal

from ia import JeuDict, MoteurIA

if sys.platform != "win32":
    from multiprocessing.connection import Connection

    ctx = get_context("fork")  # Linux/macOS

    type MaConnection[V, K] = Connection[V, K]
else:
    from multiprocessing.connection import PipeConnection

    ctx = get_context()
    type MaConnection[V, K] = PipeConnection[V, K]


def processus_ia(
    conn: MaConnection[Any, Any],
    classe_ia: type[MoteurIA],
    joueur_id: str,
    ncases: int,
    max_tours: int,
    temps_ko: int,
) -> None:
    """Fonction qui doit tourner dans un processus à part, elle a pour responsabilité
    d'instancier une classe IA et d'appeler des méthodes à la demande du processus parent

    Args:
        conn (MaConnection[Any, Any]): La connexion avec le processus parent
        classe_ia (type[MoteurIA]): La classe de l'IA à instancier et sur lequel faire les appels de méthode
        joueur_id (str): L'identifiant unique du joueur
        ncases (int): Le nombre de cases que contient le plateau de jeu carré
        max_tours (int): Le nombre maximal de tours du jeu
    """
    ia = classe_ia(joueur_id, ncases, max_tours, temps_ko)

    while True:
        try:
            nom_methode, data = conn.recv()
            if nom_methode == "__STOP__":
                break

            method = getattr(ia, nom_methode)
            result = method(*data)
            conn.send(("OK", result))

        except Exception as e:
            conn.send(("ERROR", str(e)))


class MoteurIASecurise:
    __slots__ = ("parent_conn", "processus", "temps_max")

    def __init__(
        self,
        classe_ia: type[MoteurIA],
        joueur_id: str,
        ncases: int,
        max_tours: int,
        temps_ko: int,
        temps_max: float,
    ):
        self.temps_max = temps_max

        self.parent_conn, enfant_conn = ctx.Pipe()
        self.processus = ctx.Process(
            target=processus_ia,
            args=(enfant_conn, classe_ia, joueur_id, ncases, max_tours, temps_ko),
            daemon=True,
        )
        self.processus.start()

    def _appel_methode(
        self, nom_methode: str, data: tuple[Any, ...]
    ) -> Literal["TIMEOUT", "CRASH"] | Any:
        """Appelle une méthode via le processus enfant et retourne sa valeur de retour.
        Si la fonction à planté le retour est "CRASH". Si la fonction à pris plus de `temps_max` secondes pour
        répondre, "TIMEOUT" est retournée et le processus enfant est détruit. Les prochains appels à cette méthode
        retourneront toujours "TIMEOUT" dans ce cas la.

        Returns:
            (Literal["TIMEOUT", "CRASH"] | Any): Retourne la valeur de retour de la méthode appelée, ou "CRASH" si la méthode a plantée ou "TIMEOUT"
            si elle n'a pas répondue dans le temps imparti
        """
        if not self.processus.is_alive():
            return "TIMEOUT"

        self.parent_conn.send((nom_methode, data))

        debut = time.time()
        while True:
            if self.parent_conn.poll(0.01):
                status, payload = self.parent_conn.recv()
                if status == "OK":
                    return payload
                else:
                    return "CRASH"

            if time.time() - debut > self.temps_max:
                self.processus.terminate()
                self.processus.join()
                return "TIMEOUT"

    def stop(self) -> None:
        """Arrête proprement le processus enfant qui contient l'IA"""
        if self.processus.is_alive():
            self.parent_conn.send(("__STOP__", None))
            self.processus.join()

    def ponte(
        self, jeu: JeuDict, cout_ponte: int
    ) -> Literal["OUV", "BOU", "ECL", "RIEN", "TIMEOUT", "CRASH"]:
        return self._appel_methode("ponte", (jeu, cout_ponte))

    def action_abeilles(
        self, jeu: JeuDict
    ) -> (
        list[tuple[str, int, int, Literal["DEPLACEMENT", "BUTINAGE"]]]
        | Literal["TIMEOUT", "CRASH"]
    ):
        return self._appel_methode("action_abeilles", (jeu,))
