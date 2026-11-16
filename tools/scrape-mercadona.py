"""Recolecta el catálogo de la tienda online de Mercadona.

NO se publica en la web (carpeta tools/). Guarda, para cada producto, su
nombre, la URL de la foto y de qué sección/categoría es, en un JSON.

Uso:  python tools/scrape-mercadona.py

Notas:
  - Usa la API interna de tienda.mercadona.es (no oficial; su robots.txt
    desaconseja /api). Se hace a ritmo lento y solo para uso personal.
  - No pide precios ni nada de cuentas: solo catálogo y fotos.
"""

import json
import sys
import time
import urllib.error
import urllib.request

BASE = "https://tienda.mercadona.es/api"
CABECERAS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "application/json",
}
PAUSA = 0.6          # segundos entre peticiones (ser amable)
REINTENTOS = 3
SALIDA = "tools/mercadona-productos.json"


def pedir(url):
    """GET a url con reintentos y espera creciente."""
    for intento in range(1, REINTENTOS + 1):
        try:
            req = urllib.request.Request(url, headers=CABECERAS)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            if intento == REINTENTOS:
                raise
            print(f"    fallo ({e}); reintento {intento}/{REINTENTOS}…", flush=True)
            time.sleep(1.5 * intento)


def extraer_productos(nodo, seccion, categoria, salida):
    """Recorre un árbol de categorías y va guardando los productos."""
    for sub in nodo.get("categories") or []:
        extraer_productos(sub, seccion, sub.get("name") or categoria, salida)
    for p in nodo.get("products") or []:
        thumb = p.get("thumbnail")
        if not thumb:
            continue
        salida.append({
            "id": str(p.get("id")),
            "nombre": p.get("display_name") or "",
            "foto": thumb,
            "seccion": seccion,
            "categoria": categoria,
            "envase": p.get("packaging") or "",
        })


def main():
    print("1) Listando secciones…", flush=True)
    raiz = pedir(BASE + "/categories/")

    categorias = []          # (seccion, id_categoria)
    for sec in raiz["results"]:
        for cat in sec.get("categories") or []:
            categorias.append((sec["name"], cat["id"], cat["name"]))
    print(f"   {len(categorias)} categorías de primer nivel.")

    productos = []
    for i, (seccion, cid, cnombre) in enumerate(categorias, 1):
        print(f"2) [{i}/{len(categorias)}] {seccion} > {cnombre}", flush=True)
        try:
            detalle = pedir(f"{BASE}/categories/{cid}/")
        except Exception as e:
            print(f"    ERROR, se salta: {e}", flush=True)
            continue
        extraer_productos(detalle, seccion, cnombre, productos)
        time.sleep(PAUSA)

    # Quitar duplicados por id
    unicos = {}
    for p in productos:
        unicos[p["id"]] = p
    lista = list(unicos.values())

    datos = {"total": len(lista), "productos": lista}
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)

    print(f"\nGuardados {len(lista)} productos en {SALIDA}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
