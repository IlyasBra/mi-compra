"""Mete la ruta de la foto como cuarto valor de cada producto de mi-catalogo.js.

Lee tools/imagenes.json (nombre -> ./img/xxx.jpg, hecho por descargar-imagenes.py)
y reescribe cada linea del catalogo anadiendo el cuarto campo. Los productos sin
foto se quedan con "" y un comentario para saber que es a proposito.

NO se publica en la web.

Uso:  python tools/aplicar-imagenes.py
"""

import json
import re
import sys

CATALOGO = "mi-catalogo.js"
MAPA = "tools/imagenes.json"

# Linea de producto:  ["Nombre", "Categoría", "unidad"],
LINEA = re.compile(
    r'^(?P<sangria>\s*)\["(?P<nombre>(?:[^"\\]|\\.)*)",\s*'
    r'"(?P<categoria>(?:[^"\\]|\\.)*)",\s*'
    r'"(?P<unidad>(?:[^"\\]|\\.)*)"\](?P<coma>,?)(?P<resto>.*)$'
)

CABECERA_VIEJA = """   IMÁGENES (preparado, todavía sin activar)
   Cuando activemos las fotos, cada producto podrá llevar un cuarto
   valor con la imagen:

       [ nombre, categoría, unidad, imagen ]

   donde "imagen" será una foto hecha con el móvil. De momento se
   deja el hueco reservado para no tener que rehacer nada después."""

CABECERA_NUEVA = """   IMÁGENES
   Cada producto lleva un cuarto valor con la ruta de su foto:

       [ nombre, categoría, unidad, imagen ]

   Las fotos están en img/ y se bajaron del catálogo de Mercadona como
   mejor aproximación al producto. Cuando no hay nada parecido, el
   cuarto valor va vacío ("") y se queda sin foto."""


def main():
    mapa = json.load(open(MAPA, encoding="utf-8"))
    lineas = open(CATALOGO, encoding="utf-8").read().split("\n")

    puestas = 0
    sin_foto = []
    no_encontradas = []
    salida = []

    for linea in lineas:
        m = LINEA.match(linea)
        if not m:
            salida.append(linea)
            continue
        nombre = m["nombre"]
        img = mapa.get(nombre)
        if img:
            nueva = (f'{m["sangria"]}["{nombre}", "{m["categoria"]}", '
                     f'"{m["unidad"]}", "{img}"]{m["coma"]}{m["resto"]}')
            puestas += 1
        else:
            nueva = (f'{m["sangria"]}["{nombre}", "{m["categoria"]}", '
                     f'"{m["unidad"]}", ""]{m["coma"]}{m["resto"]}')
            sin_foto.append(nombre)
        salida.append(nueva)

    texto = "\n".join(salida)

    # Actualizar el comentario de cabecera
    if CABECERA_VIEJA in texto:
        texto = texto.replace(CABECERA_VIEJA, CABECERA_NUEVA)
    else:
        print("AVISO: no encontré la cabecera antigua para actualizarla")

    open(CATALOGO, "w", encoding="utf-8").write(texto)

    # Comprobaciones
    conocidos = set(mapa)
    for nombre in sin_foto:
        if nombre not in ("Peine / cepillo", "Gomas de pelo", "Paraguas"):
            no_encontradas.append(nombre)

    print(f"Productos con foto añadida: {puestas}")
    print(f"Productos sin foto: {len(sin_foto)} -> {', '.join(sin_foto)}")
    if no_encontradas:
        print(f"¡OJO! sin foto y no esperados: {no_encontradas}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
