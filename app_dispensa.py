# Carica le quattro parti dell'app (parte1.py ... parte4.py) come se fossero un unico file.
import os

_cartella = os.path.dirname(os.path.abspath(__file__))
for _nome in ("parte1.py", "parte2.py", "parte3.py", "parte4.py"):
    _percorso = os.path.join(_cartella, _nome)
    with open(_percorso, encoding="utf-8") as _f:
        exec(compile(_f.read(), _percorso, "exec"), globals())
