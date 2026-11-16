# 🛒 Mi compra

Lista de la compra para el móvil, con catálogo de productos y precios opcionales.

- **Sin coste**: es una web estática. No hay servidor, ni base de datos, ni cuentas.
- **Tus datos se quedan en tu móvil**: se guardan en el almacenamiento del navegador
  (`localStorage`). Nada sale de tu dispositivo.
- **Funciona sin conexión**: es una PWA (se puede instalar en la pantalla de inicio).
- **Publicada gratis en GitHub Pages.**

---

## Cómo se usa

### 1. Añadir productos a la lista

Arriba de la pestaña **Lista** hay un cuadro de texto:

- Escribe y te irá sugiriendo productos del catálogo. Toca uno para añadirlo.
- Si escribes algo que no existe (por ejemplo «Servilletas de tela»), aparecerá
  **＋ Crear «…»** y se añadirá como producto nuevo en la categoría *Otros*.

### 2. Ajustar cantidades

Cada línea tiene un `−` y un `+`. Puedes escribir directamente la cantidad
(acepta decimales, útil para kilos). La casilla de la izquierda marca el
producto como **comprado**.

### 3. Catálogo

En la pestaña **Catálogo** tienes **tu catálogo personal**: solo los productos
que hayas elegido tú (van en `mi-catalogo.js`).

- Busca por nombre (da igual las tildes: «platano» encuentra «Plátano»).
- Filtra por categoría con las etiquetas de arriba.
- Botón `+` para añadirlo a la lista; botón `✎` para editar nombre, categoría,
  unidad o **precio**.
- **+ Nuevo producto** para crear uno desde cero.

> Si pones precios, la app te mostrará el **total estimado** de la compra abajo.

### 4. Finalizar la compra

El botón **Finalizar compra** guarda la lista en el **Historial** y la vacía.
Desde el historial puedes recuperar una compra entera con **Añadir a la lista**.

### 5. Copias de seguridad ⚠️

Los datos viven **solo en este navegador de este dispositivo**. Si borras los
datos del navegador, desinstalas la app o cambias de móvil, se pierden.

Por eso, de vez en cuando entra en **⚙️ → Exportar copia de seguridad** y guarda
el `.json` (puedes mandártelo por correo o a la nube). Para recuperarlo:
**⚙️ → Importar copia**.

---

## Instalarla en el móvil

1. Abre la URL de GitHub Pages en el navegador del móvil.
2. **Android (Chrome)**: menú ⋮ → *Añadir a pantalla de inicio* / *Instalar app*.
3. **iPhone (Safari)**: botón Compartir → *Añadir a pantalla de inicio*.

A partir de ahí se abre como una app normal y funciona sin conexión.

---

## Publicarla en GitHub Pages (gratis)

### Opción A — con GitHub Actions (recomendada)

El repositorio ya incluye el flujo `.github/workflows/pages.yml`.

1. Crea un repositorio en GitHub y sube el proyecto a la rama `main`:

   ```bash
   git init
   git add .
   git commit -m "Primera versión de Mi compra"
   git branch -M main
   git remote add origin https://github.com/TU-USUARIO/TU-REPO.git
   git push -u origin main
   ```

2. En GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. Espera un minuto. La web estará en
   `https://TU-USUARIO.github.io/TU-REPO/`.

Cada vez que hagas `git push` a `main`, se republica sola.

### Opción B — sin Actions (la más simple)

1. Sube el proyecto a `main`.
2. **Settings → Pages → Source: Deploy from a branch → Branch: `main` / `(root)`**.
3. Listo.

---

## Desarrollo local

No hay dependencias ni compilación. Solo necesitas servir los archivos por HTTP
(el service worker no funciona con `file://`):

```bash
python -m http.server 8000
# luego abre http://localhost:8000
```

Regenerar los iconos (opcional, requiere Python 3, sin librerías extra):

```bash
python tools/make-icons.py
```

---

## Estructura

```
index.html              Interfaz (3 pestañas + diálogos)
styles.css              Estilos, tema claro/oscuro automático
app.js                  Toda la lógica y el guardado en localStorage
mi-catalogo.js          TU catálogo personal (lo que compras de verdad)
catalog.js              Categorías (secciones de Mercadona) y unidades
manifest.webmanifest    Configuración de la PWA
sw.js                   Service worker (uso sin conexión)
icons/                  Iconos de la app
tools/make-icons.py     Generador de iconos
tools/catalogo-generico.js  Biblioteca de referencia (no se carga en la app)
.github/workflows/      Publicación automática en GitHub Pages
```

## Ideas para más adelante

- Sincronizar entre dispositivos (requeriría un backend, ya no sería gratis del todo).
- Ordenar los productos según el recorrido real del supermercado.
- Recordar el precio de la última compra para comparar.
- Compartir la lista con otra persona por enlace.
