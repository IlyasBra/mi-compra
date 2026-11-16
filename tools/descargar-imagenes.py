"""Descarga las fotos de Mercadona y las guarda en img/ (uso personal).

Lee tools/emparejamiento.json (generado por match-mercadona.py) y baja cada foto
al CDN de Mercadona a la carpeta img/, con el nombre del producto en "slug"
(el mismo formato que usa la app: sin acentos, minúsculas, guiones).

  - Las fotos ya vienen pequeñas y recortadas a 300x300 desde el CDN.
  - Si un archivo ya existe, se salta (se puede volver a lanzar sin miedo).
  - NO se publica la carpeta tools/; img/ sí va con la web.

Uso:  python tools/descargar-imagenes.py
"""

import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

EMPAREJAMIENTO = "tools/emparejamiento.json"
NUESTROS = "tools/nuestros-productos.json"
DESTINO = "img"
MAPA = "tools/imagenes.json"          # nombre -> ruta final (./img/xxx.jpg)
CABECERAS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
}
REINTENTOS = 3
HILOS = 4


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return s.lower().strip()


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", norm(s)).strip("-")


def bajar(foto, ruta):
    """Descarga foto -> ruta. Devuelve True/False."""
    for intento in range(1, REINTENTOS + 1):
        try:
            req = urllib.request.Request(foto, headers=CABECERAS)
            with urllib.request.urlopen(req, timeout=30) as r:
                datos = r.read()
            if len(datos) < 200:
                raise ValueError(f"archivo sospechosamente pequeño ({len(datos)} B)")
            tmp = ruta + ".parcial"
            with open(tmp, "wb") as f:
                f.write(datos)
            os.replace(tmp, ruta)
            return True
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as e:
            if intento == REINTENTOS:
                print(f"    FALLO {os.path.basename(ruta)}: {e}", flush=True)
                return False
            time.sleep(1.0 * intento)


def main():
    emp = json.load(open(EMPAREJAMIENTO, encoding="utf-8"))
    nuestros = json.load(open(NUESTROS, encoding="utf-8"))
    os.makedirs(DESTINO, exist_ok=True)

    tareas = []          # (nombre, foto, ruta)
    mapa = {}
    sin_foto = []
    for entrada in nuestros:
        nombre = entrada[0]
        info = emp.get(nombre) or {}
        foto = info.get("foto")
        if not foto:
            sin_foto.append(nombre)
            continue
        ruta = os.path.join(DESTINO, slug(nombre) + ".jpg")
        mapa[nombre] = "./" + ruta.replace("\\", "/")
        if os.path.exists(ruta):
            continue
        tareas.append((nombre, foto, ruta))

    print(f"Con foto: {len(mapa)}   Sin foto: {len(sin_foto)}")
    print(f"Pendientes de descargar: {len(tareas)} (las ya descargadas se saltan)\n")

    hechas = 0
    fallos = []
    with ThreadPoolExecutor(max_workers=HILOS) as pool:
        futuros = {pool.submit(bajar, foto, ruta): (nombre, ruta) for nombre, foto, ruta in tareas}
        for fut in as_completed(futuros):
            nombre, ruta = futuros[fut]
            hechas += 1
            if not fut.result():
                fallos.append(nombre)
            if hechas % 25 == 0 or hechas == len(tareas):
                print(f"  {hechas}/{len(tareas)}…", flush=True)

    json.dump(mapa, open(MAPA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"\nDescargadas ahora: {len(tareas) - len(fallos)}")
    print(f"Fallos: {len(fallos)}")
    for n in fallos:
        print("   -", n)
    print(f"Sin foto (no hay equivalente en Mercadona): {len(sin_foto)}")
    for n in sin_foto:
        print("   -", n)
    print(f"\nMapa nombre -> ruta guardado en {MAPA}")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
