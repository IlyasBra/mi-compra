/* Comprobación del catálogo personal. No se publica en la web.
   Uso:  node tools/check-catalogo.js            (desde la raíz del proyecto)
   Revisa:
     - que catalog.js y mi-catalogo.js no tengan errores de sintaxis
     - que cada categoría exista en CATEGORIAS
     - que cada unidad exista en UNIDADES
     - que no haya nombres duplicados
     - el total de productos
*/

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const raiz = path.resolve(__dirname, '..');

function leer(archivo) {
  return fs.readFileSync(path.join(raiz, archivo), 'utf8');
}

/* Los archivos usan `const` en la raíz, así que no quedan en el objeto
   global: hay que evaluarlos juntos dentro de una función y devolverlos. */
function cargar(archivos) {
  const src = archivos.map(leer).join('\n');
  const envuelto =
    '(function(){\n' + src + '\nreturn {\n' +
    '  CATEGORIAS: typeof CATEGORIAS !== "undefined" ? CATEGORIAS : undefined,\n' +
    '  UNIDADES: typeof UNIDADES !== "undefined" ? UNIDADES : undefined,\n' +
    '  MI_CATALOGO: typeof MI_CATALOGO !== "undefined" ? MI_CATALOGO : undefined\n' +
    '};\n})()';
  return vm.runInNewContext(envuelto, {});
}

let fallos = 0;
const err = (msg) => { fallos++; console.log('  ✗ ' + msg); };

console.log('Comprobando catálogo personal…\n');

// --- catalog.js + mi-catalogo.js ---
let datos;
try {
  datos = cargar(['catalog.js', 'mi-catalogo.js']);
} catch (e) {
  console.log('No se pudieron cargar los archivos: ' + e.message);
  process.exit(1);
}
const CATEGORIAS = datos.CATEGORIAS || [];
const UNIDADES = datos.UNIDADES || [];
console.log('catalog.js  →  ' + CATEGORIAS.length + ' categorías, ' + UNIDADES.length + ' unidades');

const LISTA = datos.MI_CATALOGO;
if (!Array.isArray(LISTA)) {
  console.log('mi-catalogo.js no define MI_CATALOGO como array.');
  process.exit(1);
}

console.log('mi-catalogo.js  →  ' + LISTA.length + ' productos\n');

const vistos = new Map();
const porCat = {};
let conImagen = 0;

LISTA.forEach((entrada, i) => {
  const n = i + 1;
  if (!Array.isArray(entrada) || entrada.length < 3) {
    return err('entrada ' + n + ': no tiene [nombre, categoría, unidad]');
  }
  const [nombre, cat, unidad, img] = entrada;
  if (typeof nombre !== 'string' || !nombre.trim()) err('entrada ' + n + ': nombre vacío');
  if (!CATEGORIAS.includes(cat)) err('entrada ' + n + ' («' + nombre + '»): categoría desconocida «' + cat + '»');
  if (!UNIDADES.includes(unidad)) err('entrada ' + n + ' («' + nombre + '»): unidad desconocida «' + unidad + '»');
  if (entrada.length >= 4 && img) conImagen++;

  const clave = nombre.toLowerCase();
  if (vistos.has(clave)) err('nombre duplicado «' + nombre + '» (entradas ' + vistos.get(clave) + ' y ' + n + ')');
  else vistos.set(clave, n);

  porCat[cat] = (porCat[cat] || 0) + 1;
});

console.log('Reparto por categoría:');
Object.keys(porCat).sort().forEach((c) => console.log('  ' + String(porCat[c]).padStart(3) + '  ' + c));
if (conImagen) console.log('\nCon imagen: ' + conImagen);

console.log('\nTotal: ' + LISTA.length + ' productos');

if (fallos) {
  console.log('\n' + fallos + ' problema(s) encontrado(s).');
  process.exit(1);
}
console.log('\nTodo correcto.');
