/* Mi compra — lógica de la app.
   Todo se guarda en localStorage del dispositivo. No hay servidor. */
'use strict';

const LS_KEY = 'mercalista.v1';
const APP_VERSION = 'v1.0.0';
const CAT_OTROS = 'Otros';
const PAGE_SIZE = 100;

/* ---------- estado ---------- */
let state = {
  version: 1,
  catalog: [],   // { id, name, cat, unit, price, base }
  list: [],      // { id, productId, name, cat, unit, qty, price, done }
  history: [],   // { id, date, items: [...] }
  removed: [],   // ids de productos base borrados por el usuario
  ui: { tab: 'lista' },
};

/* ---------- utilidades ---------- */
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 8);

const norm = (s) =>
  String(s || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim();

const eur = (n) =>
  Number(n || 0).toLocaleString('es-ES', { style: 'currency', currency: 'EUR' });

// Redondeo a céntimos evitando los típicos errores de coma flotante
// (0.35 * 1.5 = 0.5249999… debe dar 0,53 €, no 0,52 €).
const round2 = (n) => Math.round((Number(n) || 0) * 100 + 1e-6) / 100;

const esc = (s) =>
  String(s ?? '').replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const catOrder = (cat) => {
  const i = CATEGORIAS.indexOf(cat);
  return i === -1 ? CATEGORIAS.length : i;
};

let toastTimer = null;
function toast(msg) {
  const el = $('#toast');
  el.textContent = msg;
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.hidden = true; }, 2200);
}

/* ---------- persistencia ---------- */
function save() {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify(state));
  } catch (e) {
    toast('No se pudieron guardar los datos');
    console.error(e);
  }
}

function load() {
  let raw = null;
  try { raw = localStorage.getItem(LS_KEY); } catch (e) { /* modo privado */ }

  if (raw) {
    try {
      const parsed = JSON.parse(raw);
      state = Object.assign(state, parsed);
    } catch (e) {
      console.warn('Datos guardados ilegibles, se empieza de cero.', e);
    }
  }
  state.catalog = Array.isArray(state.catalog) ? state.catalog : [];
  state.list = Array.isArray(state.list) ? state.list : [];
  state.history = Array.isArray(state.history) ? state.history : [];
  state.removed = Array.isArray(state.removed) ? state.removed : [];
  state.ui = state.ui && typeof state.ui === 'object' ? state.ui : { tab: 'lista' };

  migrate();
  seedCatalog();
  save();
}

const slug = (s) => norm(s).replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

/* v1 -> v2: el catálogo deja de ser genérico y pasa a ser el personal.
   Se descartan los productos genéricos antiguos y se conserva lo que
   hayas creado tú. */
function migrate() {
  const miIds = new Set(MI_CATALOGO.map(([name]) => 'mi:' + slug(name)));
  state.catalog = state.catalog.filter((p) => !p.base || miIds.has(p.id));
  for (const p of state.catalog) if (p.img === undefined) p.img = null;
}

/* Vuelca tu catálogo personal (mi-catalogo.js) en el almacenamiento. */
function seedCatalog() {
  const ids = new Set(state.catalog.map((p) => p.id));
  const removed = new Set(state.removed);
  for (const [name, cat, unit, img] of MI_CATALOGO) {
    const id = 'mi:' + slug(name);
    if (ids.has(id) || removed.has(id)) continue;
    state.catalog.push({ id, name, cat, unit, price: 0, img: img || null, base: true });
    ids.add(id);
  }
}

/* ---------- catálogo ---------- */
const findProduct = (id) => state.catalog.find((p) => p.id === id);

function addToList(product, qty = 1) {
  const existing = state.list.find((i) => i.productId === product.id && !i.done);
  if (existing) {
    existing.qty = round2(existing.qty + qty);
    if (!existing.price) existing.price = product.price || 0;
  } else {
    state.list.push({
      id: uid(),
      productId: product.id,
      name: product.name,
      cat: product.cat,
      unit: product.unit,
      price: product.price || 0,
      img: product.img || null,
      qty: round2(qty),
      done: false,
    });
  }
  save();
  renderList();
  renderBadge();
}

function addFreeText(name) {
  const clean = String(name || '').trim();
  if (!clean) return;

  const n = norm(clean);
  const hit =
    state.catalog.find((p) => norm(p.name) === n) ||
    state.catalog.find((p) => norm(p.name).startsWith(n));

  if (hit) { addToList(hit, 1); toast(hit.name + ' añadido'); return; }

  const product = { id: 'user:' + uid(), name: clean, cat: CAT_OTROS, unit: 'ud', price: 0, base: false };
  state.catalog.push(product);
  addToList(product, 1);
  toast('«' + clean + '» creado y añadido');
}

function deleteProduct(id) {
  const p = findProduct(id);
  state.catalog = state.catalog.filter((x) => x.id !== id);
  if (p && p.base && !state.removed.includes(id)) state.removed.push(id);
  save();
  renderCatalog();
}

/* ---------- lista ---------- */
function setQty(id, qty) {
  const item = state.list.find((i) => i.id === id);
  if (!item) return;
  item.qty = Math.max(0, round2(qty));
  if (item.qty === 0) item.qty = 0.5;
  save();
  renderList();
}

function toggleDone(id) {
  const item = state.list.find((i) => i.id === id);
  if (!item) return;
  item.done = !item.done;
  save();
  renderList();
  renderBadge();
}

function removeItem(id) {
  state.list = state.list.filter((i) => i.id !== id);
  save();
  renderList();
  renderBadge();
}

function clearDone() {
  const n = state.list.filter((i) => i.done).length;
  if (!n) { toast('No hay nada marcado'); return; }
  state.list = state.list.filter((i) => !i.done);
  save();
  renderList();
  renderBadge();
  toast(n + (n === 1 ? ' producto quitado' : ' productos quitados'));
}

function finishShopping() {
  if (!state.list.length) return;
  const done = state.list.filter((i) => i.done).length;
  const msg = done
    ? '¿Guardar la compra en el historial y vaciar la lista?'
    : 'No has marcado nada como comprado. ¿Guardar igualmente y vaciar la lista?';
  if (!confirm(msg)) return;

  state.history.unshift({
    id: uid(),
    date: new Date().toISOString(),
    items: state.list.map((i) => ({ ...i })),
  });
  state.list = [];
  save();
  renderList();
  renderBadge();
  renderHistory();
  toast('Compra guardada en el historial');
}

function totalOf(items) {
  return round2(items.reduce((sum, i) => sum + (Number(i.price) || 0) * (Number(i.qty) || 0), 0));
}

/* ---------- render: lista ---------- */
function renderList() {
  const groupsEl = $('#listGroups');
  const emptyEl = $('#listEmpty');
  const actionsEl = $('#listActions');
  const progressEl = $('#progress');

  if (!state.list.length) {
    groupsEl.innerHTML = '';
    emptyEl.hidden = false;
    actionsEl.hidden = true;
    progressEl.hidden = true;
    renderTotals();
    return;
  }

  emptyEl.hidden = true;
  actionsEl.hidden = false;

  // Agrupar por categoría
  const byCat = new Map();
  for (const item of state.list) {
    const cat = item.cat || CAT_OTROS;
    if (!byCat.has(cat)) byCat.set(cat, []);
    byCat.get(cat).push(item);
  }
  const cats = Array.from(byCat.keys()).sort((a, b) => catOrder(a) - catOrder(b));

  groupsEl.innerHTML = cats.map((cat) => {
    const items = byCat.get(cat).slice().sort((a, b) => Number(a.done) - Number(b.done));
    const doneCount = items.filter((i) => i.done).length;
    return `
      <div class="group">
        <div class="group-head">
          <span>${esc(cat)}</span>
          <span class="count">${doneCount}/${items.length}</span>
        </div>
        <ul class="items">
          ${items.map(itemHTML).join('')}
        </ul>
      </div>`;
  }).join('');

  // Progreso
  const total = state.list.length;
  const done = state.list.filter((i) => i.done).length;
  progressEl.hidden = false;
  $('#progressFill').style.width = (total ? (done / total) * 100 : 0) + '%';
  $('#progressText').textContent = done + ' de ' + total + ' comprados';

  renderTotals();
}

function itemHTML(item) {
  const price = Number(item.price) || 0;
  const line = price > 0 ? eur(price) + '/' + esc(item.unit) + ' · ' + eur(price * item.qty) : esc(item.unit);
  return `
    <li class="item${item.done ? ' done' : ''}" data-id="${item.id}">
      <label class="check">
        <input type="checkbox" data-act="toggle" ${item.done ? 'checked' : ''}
               aria-label="Marcar ${esc(item.name)} como comprado">
      </label>
      <div class="item-main">
        ${item.img ? `<img class="thumb" src="${esc(item.img)}" alt="" loading="lazy">` : ''}
        <span class="item-text">
          <span class="item-name">${esc(item.name)}</span>
          <span class="item-sub">${line}</span>
        </span>
      </div>
      <div class="stepper">
        <button type="button" data-act="dec" aria-label="Menos">−</button>
        <input type="number" data-act="qty" value="${item.qty}" min="0" step="0.5" inputmode="decimal"
               aria-label="Cantidad de ${esc(item.name)}">
        <button type="button" data-act="inc" aria-label="Más">+</button>
      </div>
      <button type="button" class="del" data-act="del" aria-label="Quitar ${esc(item.name)}">×</button>
    </li>`;
}

function renderBadge() {
  const pending = state.list.filter((i) => !i.done).length;
  const badge = $('#badgeLista');
  badge.textContent = String(pending);
  badge.hidden = pending === 0;
}

function renderTotals() {
  const bar = $('#totalsBar');
  if (!state.list.length) { bar.hidden = true; return; }
  bar.hidden = false;

  const count = state.list.length;
  $('#totalsText').textContent = count + (count === 1 ? ' artículo' : ' artículos');

  const total = totalOf(state.list);
  const priceEl = $('#totalsPrice');
  if (total > 0) { priceEl.textContent = eur(total); priceEl.hidden = false; }
  else { priceEl.textContent = ''; priceEl.hidden = true; }
}

/* ---------- render: catálogo ---------- */
let catFilter = 'Todas';
let catQuery = '';
let catLimit = PAGE_SIZE;

function renderChips() {
  const cats = CATEGORIAS.filter((c) => state.catalog.some((p) => p.cat === c));
  const all = ['Todas', ...cats];
  $('#catChips').innerHTML = all.map((c) =>
    `<button type="button" class="chip${c === catFilter ? ' is-active' : ''}" data-cat="${esc(c)}">${esc(c)}</button>`
  ).join('');
}

function filteredCatalog() {
  const q = norm(catQuery);
  return state.catalog
    .filter((p) => catFilter === 'Todas' || p.cat === catFilter)
    .filter((p) => !q || norm(p.name).includes(q))
    .sort((a, b) => {
      const byCat = catOrder(a.cat) - catOrder(b.cat);
      return byCat !== 0 ? byCat : a.name.localeCompare(b.name, 'es');
    });
}

function renderCatalog() {
  renderChips();
  const list = filteredCatalog();
  const shown = list.slice(0, catLimit);

  const el = $('#catalogList');
  el.innerHTML = shown.map((p) => `
    <li class="prod" data-id="${p.id}">
      <div class="prod-main">
        ${p.img ? `<img class="thumb" src="${esc(p.img)}" alt="" loading="lazy">` : ''}
        <span class="item-text">
          <span class="prod-name">${esc(p.name)}</span>
          <span class="prod-meta">${esc(p.cat)} · ${esc(p.unit)}</span>
        </span>
      </div>
      <span class="price">${p.price > 0 ? eur(p.price) : ''}</span>
      <button type="button" class="icon-btn add" data-act="add" aria-label="Añadir ${esc(p.name)}">+</button>
      <button type="button" class="icon-btn" data-act="edit" aria-label="Editar ${esc(p.name)}">✎</button>
    </li>`).join('');

  $('#catEmpty').hidden = list.length > 0;
  $('#catEmpty').textContent = state.catalog.length
    ? 'No hay productos que coincidan.'
    : 'Tu catálogo está vacío. Crea productos con «+ Nuevo producto».';
  const more = $('#catMore');
  more.hidden = list.length <= catLimit;
  $('#catMoreBtn').textContent = 'Mostrar más (' + (list.length - catLimit) + ')';
}

/* ---------- render: historial ---------- */
function renderHistory() {
  const el = $('#historyList');
  const empty = $('#historyEmpty');

  if (!state.history.length) {
    el.innerHTML = '';
    empty.hidden = false;
    return;
  }
  empty.hidden = true;

  el.innerHTML = state.history.map((shop) => {
    const date = new Date(shop.date);
    const label = date.toLocaleDateString('es-ES', {
      day: 'numeric', month: 'long', year: 'numeric',
    });
    const total = totalOf(shop.items);
    return `
      <article class="shop" data-id="${shop.id}">
        <div class="shop-head">
          <strong>${esc(label)}</strong>
          <span>${shop.items.length} art.${total > 0 ? ' · ' + eur(total) : ''}</span>
        </div>
        <details class="shop-items">
          <summary>Ver productos</summary>
          <ul style="margin:8px 0 0;padding-left:18px">
            ${shop.items.map((i) => `<li>${esc(i.name)} — ${i.qty} ${esc(i.unit)}</li>`).join('')}
          </ul>
        </details>
        <div class="shop-actions">
          <button type="button" class="secondary-btn" data-act="repeat">Añadir a la lista</button>
          <button type="button" class="secondary-btn" data-act="delete">Borrar</button>
        </div>
      </article>`;
  }).join('');
}

function repeatShop(id) {
  const shop = state.history.find((s) => s.id === id);
  if (!shop) return;
  for (const item of shop.items) {
    const product = findProduct(item.productId) || {
      id: item.productId || 'user:' + uid(),
      name: item.name, cat: item.cat, unit: item.unit, price: item.price,
    };
    if (!findProduct(product.id)) state.catalog.push(product);
    const existing = state.list.find((i) => i.productId === product.id && !i.done);
    if (existing) existing.qty = round2(existing.qty + item.qty);
    else state.list.push({ ...item, id: uid(), done: false });
  }
  save();
  renderList();
  renderBadge();
  switchTab('lista');
  toast('Productos añadidos a la lista');
}

function deleteShop(id) {
  if (!confirm('¿Borrar esta compra del historial?')) return;
  state.history = state.history.filter((s) => s.id !== id);
  save();
  renderHistory();
}

/* ---------- pestañas ---------- */
function switchTab(tab) {
  state.ui.tab = tab;
  save();
  $$('.tab').forEach((b) => b.classList.toggle('is-active', b.dataset.tab === tab));
  $('#view-lista').hidden = tab !== 'lista';
  $('#view-catalogo').hidden = tab !== 'catalogo';
  $('#view-historial').hidden = tab !== 'historial';
  $('#totalsBar').hidden = tab !== 'lista' || !state.list.length;
  if (tab === 'catalogo') renderCatalog();
  if (tab === 'historial') renderHistory();
}

/* ---------- sugerencias del añadido rápido ---------- */
let suggestIndex = -1;
let suggestItems = [];

function renderSuggestions() {
  const input = $('#quickAdd');
  const box = $('#suggestions');
  const q = norm(input.value);

  if (!q) { box.hidden = true; suggestItems = []; suggestIndex = -1; return; }

  const matches = state.catalog
    .filter((p) => norm(p.name).includes(q))
    .sort((a, b) => {
      const an = norm(a.name), bn = norm(b.name);
      const as = an.startsWith(q) ? 0 : 1;
      const bs = bn.startsWith(q) ? 0 : 1;
      return as - bs || an.length - bn.length || an.localeCompare(bn, 'es');
    })
    .slice(0, 8);

  const exact = state.catalog.some((p) => norm(p.name) === q);
  suggestItems = matches;
  suggestIndex = -1;

  const rows = matches.map((p, i) =>
    `<li data-i="${i}" data-id="${p.id}">${esc(p.name)}<small>${esc(p.cat)}</small></li>`).join('');

  const newRow = exact ? '' :
    `<li class="new" data-new="1">＋ Crear «${esc(input.value.trim())}»</li>`;

  box.innerHTML = rows + newRow;
  box.hidden = false;
}

function applySuggestion(li) {
  const input = $('#quickAdd');
  if (li.dataset.new) {
    addFreeText(input.value);
  } else {
    const p = state.catalog.find((x) => x.id === li.dataset.id);
    if (p) { addToList(p, 1); toast(p.name + ' añadido'); }
  }
  input.value = '';
  $('#suggestions').hidden = true;
  suggestItems = [];
  suggestIndex = -1;
}

function moveSuggestion(delta) {
  const lis = $$('#suggestions li');
  if (!lis.length) return;
  suggestIndex = (suggestIndex + delta + lis.length) % lis.length;
  lis.forEach((li, i) => li.classList.toggle('is-active', i === suggestIndex));
  lis[suggestIndex].scrollIntoView({ block: 'nearest' });
}

/* ---------- diálogo producto ---------- */
let editingId = null;

function fillSelect(el, options, value) {
  el.innerHTML = options.map((o) =>
    `<option value="${esc(o)}"${o === value ? ' selected' : ''}>${esc(o)}</option>`).join('');
}

function openProductDialog(product) {
  editingId = product ? product.id : null;
  $('#productDialogTitle').textContent = product ? 'Editar producto' : 'Nuevo producto';
  $('#pfName').value = product ? product.name : '';
  fillSelect($('#pfCat'), CATEGORIAS, product ? product.cat : CAT_OTROS);
  fillSelect($('#pfUnit'), UNIDADES, product ? product.unit : 'ud');
  $('#pfPrice').value = product && product.price > 0 ? String(product.price) : '';
  $('#productDialog').showModal();
  setTimeout(() => $('#pfName').focus(), 50);
}

function saveProductDialog() {
  const name = $('#pfName').value.trim();
  if (!name) return;
  const cat = $('#pfCat').value;
  const unit = $('#pfUnit').value;
  const price = Math.max(0, round2(parseFloat($('#pfPrice').value) || 0));

  if (editingId) {
    const p = findProduct(editingId);
    if (p) { p.name = name; p.cat = cat; p.unit = unit; p.price = price; }
    // Refrescar los datos mostrados en la lista (sin tocar cantidades)
    for (const item of state.list) {
      if (item.productId === editingId) {
        item.name = name; item.cat = cat; item.unit = unit; item.price = price;
        item.img = p ? p.img : item.img;
      }
    }
  } else {
    const product = { id: 'user:' + uid(), name, cat, unit, price, base: false };
    state.catalog.push(product);
    addToList(product, 1);
  }
  save();
  renderList();
  renderCatalog();
  toast(editingId ? 'Producto actualizado' : 'Producto creado');
  editingId = null;
}

/* ---------- exportar / importar ---------- */
function exportData() {
  const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  const d = new Date().toISOString().slice(0, 10);
  a.href = url;
  a.download = 'mi-compra-' + d + '.json';
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  toast('Copia descargada');
}

function importData(file) {
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const data = JSON.parse(String(reader.result));
      if (!data || typeof data !== 'object') throw new Error('formato');
      state = Object.assign(state, data);
      state.catalog = Array.isArray(state.catalog) ? state.catalog : [];
      state.list = Array.isArray(state.list) ? state.list : [];
      state.history = Array.isArray(state.history) ? state.history : [];
      state.removed = Array.isArray(state.removed) ? state.removed : [];
      seedCatalog();
      save();
      renderAll();
      toast('Copia restaurada');
      $('#menuDialog').close();
    } catch (e) {
      console.error(e);
      toast('Ese archivo no es una copia válida');
    }
  };
  reader.readAsText(file);
}

function resetData() {
  if (!confirm('Se borrará todo: lista, productos propios e historial. ¿Continuar?')) return;
  try { localStorage.removeItem(LS_KEY); } catch (e) {}
  state = {
    version: 1, catalog: [], list: [], history: [], removed: [],
    ui: { tab: 'lista' },
  };
  seedCatalog();
  save();
  renderAll();
  $('#menuDialog').close();
  toast('Datos borrados');
}

/* ---------- arranque ---------- */
function renderAll() {
  renderList();
  renderBadge();
  renderCatalog();
  renderHistory();
  switchTab(state.ui.tab || 'lista');
}

function bindEvents() {
  // pestañas
  $('#tabs').addEventListener('click', (e) => {
    const btn = e.target.closest('.tab');
    if (btn) switchTab(btn.dataset.tab);
  });

  // lista
  $('#listGroups').addEventListener('click', (e) => {
    const li = e.target.closest('.item');
    if (!li) return;
    const id = li.dataset.id;
    const act = e.target.closest('[data-act]')?.dataset.act;
    const item = state.list.find((i) => i.id === id);
    if (!item) return;
    if (act === 'inc') setQty(id, item.qty + 0.5);
    else if (act === 'dec') setQty(id, item.qty - 0.5);
    else if (act === 'del') removeItem(id);
  });
  $('#listGroups').addEventListener('change', (e) => {
    const el = e.target.closest('[data-act="toggle"]');
    if (!el) return;
    toggleDone(el.closest('.item').dataset.id);
  });
  $('#listGroups').addEventListener('input', (e) => {
    const el = e.target.closest('[data-act="qty"]');
    if (!el) return;
    const item = state.list.find((i) => i.id === el.closest('.item').dataset.id);
    if (!item) return;
    item.qty = Math.max(0, round2(parseFloat(el.value) || 0));
    save();
    renderTotals();
  });

  $('#clearDone').addEventListener('click', clearDone);
  $('#finishBtn').addEventListener('click', finishShopping);

  // añadido rápido
  const input = $('#quickAdd');
  input.addEventListener('input', renderSuggestions);
  input.addEventListener('focus', renderSuggestions);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); moveSuggestion(1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); moveSuggestion(-1); }
    else if (e.key === 'Enter') {
      e.preventDefault();
      const lis = $$('#suggestions li');
      if (suggestIndex >= 0 && lis[suggestIndex]) applySuggestion(lis[suggestIndex]);
      else if (suggestItems.length && !input.value.trim()) applySuggestion(lis[0]);
      else addFreeText(input.value);
      input.value = '';
      $('#suggestions').hidden = true;
    } else if (e.key === 'Escape') {
      $('#suggestions').hidden = true;
    }
  });
  $('#suggestions').addEventListener('mousedown', (e) => {
    const li = e.target.closest('li');
    if (li) { e.preventDefault(); applySuggestion(li); }
  });
  $('#quickAddBtn').addEventListener('click', () => {
    if (input.value.trim()) { addFreeText(input.value); input.value = ''; }
    $('#suggestions').hidden = true;
    input.focus();
  });
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.quickadd')) $('#suggestions').hidden = true;
  });

  // catálogo
  $('#catSearch').addEventListener('input', (e) => {
    catQuery = e.target.value; catLimit = PAGE_SIZE; renderCatalog();
  });
  $('#catChips').addEventListener('click', (e) => {
    const chip = e.target.closest('.chip');
    if (!chip) return;
    catFilter = chip.dataset.cat; catLimit = PAGE_SIZE; renderCatalog();
  });
  $('#catMoreBtn').addEventListener('click', () => { catLimit += PAGE_SIZE; renderCatalog(); });
  $('#catalogList').addEventListener('click', (e) => {
    const btn = e.target.closest('[data-act]');
    if (!btn) return;
    const id = btn.closest('.prod').dataset.id;
    const p = findProduct(id);
    if (!p) return;
    if (btn.dataset.act === 'add') { addToList(p, 1); toast(p.name + ' añadido'); }
    else if (btn.dataset.act === 'edit') openProductDialog(p);
  });
  $('#newProductBtn').addEventListener('click', () => openProductDialog(null));

  // historial
  $('#historyList').addEventListener('click', (e) => {
    const btn = e.target.closest('[data-act]');
    if (!btn) return;
    const id = btn.closest('.shop').dataset.id;
    if (btn.dataset.act === 'repeat') repeatShop(id);
    else if (btn.dataset.act === 'delete') deleteShop(id);
  });

  // diálogo producto
  $('#productForm').addEventListener('submit', (e) => {
    e.preventDefault();
    saveProductDialog();
    $('#productDialog').close();
  });
  $('#pfCancel').addEventListener('click', () => $('#productDialog').close());

  // ajustes
  $('#menuBtn').addEventListener('click', () => $('#menuDialog').showModal());
  $('#menuClose').addEventListener('click', () => $('#menuDialog').close());
  $('#exportBtn').addEventListener('click', exportData);
  $('#importBtn').addEventListener('click', () => $('#importFile').click());
  $('#importFile').addEventListener('change', (e) => {
    const f = e.target.files && e.target.files[0];
    if (f) importData(f);
    e.target.value = '';
  });
  $('#resetBtn').addEventListener('click', resetData);
}

function registerServiceWorker() {
  if (!('serviceWorker' in navigator)) return;
  if (location.protocol !== 'http:' && location.protocol !== 'https:') return;
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js').catch((e) => console.warn('SW no registrado', e));
  });
}

load();
bindEvents();
renderAll();
$('#appVersion').textContent = 'Mi compra ' + APP_VERSION;
registerServiceWorker();
