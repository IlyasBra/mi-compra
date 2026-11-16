# Cómo subir "Mi compra" a GitHub y publicarla

Nota interna (la carpeta `tools/` no se publica en la web).

Todo el proyecto ya está **preparado y cometido** en la rama `main`, y el remoto
`origin` ya apunta a:

    https://github.com/IlyasBra/mi-compra.git

Solo falta subirlo y activar GitHub Pages.

---

## 1. Abrir una terminal en la carpeta del proyecto

Carpeta:

    C:\Users\5DAW2\Documents\Proyecto predeterminado

Forma rápida en Windows 11:

- Abre esa carpeta en el Explorador de Windows.
- Clic en la **barra de direcciones** de arriba, escribe `cmd` y pulsa **Enter**.
  (También vale: clic derecho en un hueco vacío → *Abrir en Terminal*.)

## 2. Subir el código

Escribe esto y pulsa Enter:

    git push -u origin main

- La primera vez se abrirá una ventana del navegador para **iniciar sesión en
  GitHub**. Entra con la cuenta **IlyasBra** (es la dueña del repositorio).
- Si la ventana se abre en Edge y aparece `Ilyas2914`: cierra esa ventana, ve a
  https://github.com, pulsa tu avatar arriba a la derecha → **Sign out**, y vuelve
  a iniciar sesión con **IlyasBra**. Luego repite `git push -u origin main`.
- Cuando termine verás algo como:
  `branch 'main' set up to track 'origin/main'.`

### Si el navegador sigue dando guerra (alternativa con token)

1. Con la sesión de **IlyasBra** abierta, entra en
   https://github.com/settings/tokens?type=beta → **Generate new token**.
2. Repository access: **Only select repositories** → `mi-compra`.
3. Permissions → **Contents: Read and write**.
4. Genera el token y cópialo (empieza por `github_pat_`).
5. En la terminal, pega esto **cambiando `TU_TOKEN`** por el token:

       "protocol=https`nhost=github.com`nusername=IlyasBra`npassword=TU_TOKEN`n" | git credential approve
       git push -u origin main

   (Así el token se guarda en Windows y no lo escribes en ningún chat.)

## 3. Activar GitHub Pages

1. Abre https://github.com/IlyasBra/mi-compra/settings/pages
2. En **Build and deployment** → **Source**, elige **GitHub Actions**.
3. Ve a la pestaña **Actions**: verás el flujo *"Publicar en GitHub Pages"*
   ejecutándose. Tarda 1-2 minutos.
4. Cuando acabe, tu app estará en:

       https://ilyasbra.github.io/mi-compra/

## 4. Comprobar

- El repositorio debe ser **público** (en cuenta gratuita, Pages solo funciona
  en repos públicos). Si no lo es: repo → *Settings* → *General* → abajo
  *Danger Zone* → *Change repository visibility* → **Public**.
- Abre la URL en el móvil y añádela a la pantalla de inicio (es una PWA).

---

## Alternativa sin comandos: GitHub Desktop

Si prefieres ratón en vez de terminal:

1. Instala **GitHub Desktop** (https://desktop.github.com) e inicia sesión con
   **IlyasBra**.
2. *File* → *Add local repository* → elige la carpeta
   `C:\Users\5DAW2\Documents\Proyecto predeterminado`.
3. Arriba aparecerá *Push origin*. Púlsalo.
4. Luego activa Pages igual que en el punto 3.

---

## Si algo falla

- **`Permission ... denied to Ilyas2914`** → estás autenticado con la cuenta
  equivocada. Cierra sesión en el navegador y entra con **IlyasBra** (o usa el
  token de arriba).
- **`src refspec main does not match any`** → no estás dentro de la carpeta del
  proyecto; comprueba con `git log --oneline -1` que ves el commit
  `Anadir fotos de Mercadona...`.
- **Avisos `LF will be replaced by CRLF`** → es normal en Windows, se pueden
  ignorar.
