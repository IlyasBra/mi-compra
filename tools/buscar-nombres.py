import json
import re
import unicodedata

d = json.load(open("tools/mercadona-productos.json", encoding="utf-8"))["productos"]


def n(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def pal(s):
    return set(re.findall(r"[a-z0-9]+", n(s)))


def buscar(*terminos, todos=True):
    hits = [p["nombre"] for p in d if all(t in pal(p["nombre"]) for t in terminos)]
    print(f"--- {' + '.join(terminos)}: {len(hits)}")
    for h in (hits if todos else hits[:8]):
        print("    ", h)


for t in [("camembert",), ("detergente", "polvo"), ("ginebra",), ("ron",), ("vodka",)]:
    buscar(*t)
