# Progreso del catálogo personal

Nota interna (esta carpeta `tools/` no se publica en la web).

## Decisiones tomadas

- **Imágenes de producto**: **activadas**. Cada producto lleva en `mi-catalogo.js`
  la ruta de su foto (`./img/xxx.jpg`), bajada del catálogo de Mercadona como
  mejor aproximación real. 444 de 447 con foto; sin foto solo *Paraguas*,
  *Gomas de pelo* y *Peine / cepillo* (no hay nada parecido).
- **Catálogo**: **solo con tus productos** (`mi-catalogo.js`). Los 356 genéricos
  quedaron archivados en `tools/catalogo-generico.js`, sin cargar.

## Partes revisadas

| Parte | Sección | Resultado |
| ----- | ------- | --------- |
| 1 | Frutas y verduras | **Saltada** (no compra ahí) |
| 2 | Carnes | **Saltada** |
| 3 | Pescado y marisco | Solo **Dorada** |
| 4 | Charcutería y quesos | Solo **los 23 quesos** (nada de charcutería) |
| 5 | Lácteos, huevos y panadería | **Todo** (60 productos) |
| 6A | Aceite, especias, salsas, arroz, legumbres, pasta | **Todo** (65 productos) |
| 6B | Conservas y caldos | **Todo** (38 productos) |
| 6C | Dulces, café, cereales, aperitivos y frutos secos | **Todo** (53 productos) |
| 7 | Congelados | **Todo** (44 productos) |
| 8 | Bebidas | **Todo** (38 productos) |
| 9 | Limpieza y hogar | **Todo** (48 productos) |
| 10 | Cuidado personal (Deliplus) | **Todo** (43 productos) |
| 11 | Mascotas y bebé | **Saltada** (no compra ahí) |
| 12 | Bazar y hogar | **Todo** (34 productos) |

Total en el catálogo: **447 productos**.

## Estado

**Catálogo completo con fotos**: secciones 1 a 12 revisadas. Verificado en el
navegador (447 productos, 444 fotos que cargan sin fallos, búsqueda sin acentos,
añadir a la lista, totales y diálogo de producto, 0 errores en consola).

## Comprobación rápida

`node tools/check-catalogo.js` revisa sintaxis, categorías, unidades,
duplicados y total. No se publica en la web.

## Cómo se hicieron las fotos

1. `python tools/scrape-mercadona.py` — descarga el catálogo de Mercadona a
   `tools/mercadona-productos.json`.
2. `python tools/match-mercadona.py` — empareja nuestros productos con los de
   Mercadona (automático + sustituciones a mano). Salidas:
   `tools/emparejamiento.json` y `tools/emparejamiento.md`.
3. `python tools/descargar-imagenes.py` — baja cada foto a `img/` y escribe
   `tools/imagenes.json`.
4. `python tools/aplicar-imagenes.py` — mete la ruta de la foto en
   `mi-catalogo.js`.

Nada de esto (salvo `img/`) se publica en la web.

## Otras cosas pendientes

- **Publicar en GitHub Pages** (falta la URL del repositorio del usuario).
