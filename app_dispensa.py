# Carica l'app (parte1.py, parte2.py, aggiunte.py, categorie.py, interattivi.py, stile.py, spesa.py, elimina.py, account.py, lingue*.py, parte3.py, parte4.py, avvisi.py) come se fosse un unico file.
import glob
import os

_cartella = os.path.dirname(os.path.abspath(__file__))


def _carica(percorso):
    with open(percorso, encoding="utf-8") as _f:
        exec(compile(_f.read(), percorso, "exec"), globals())


for _nome in ("parte1.py", "parte2.py", "aggiunte.py", "categorie.py", "interattivi.py", "stile.py", "spesa.py", "elimina.py", "account.py"):
    _carica(os.path.join(_cartella, _nome))
for _percorso in sorted(glob.glob(os.path.join(_cartella, "lingue*.py"))):
    _carica(_percorso)
for _nome in ("parte3.py", "parte4.py", "avvisi.py"):
    _carica(os.path.join(_cartella, _nome))
