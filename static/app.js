// Interfaz del editor: llave → subir → plan (vista previa en vivo) → exportar.
const $ = id => document.getElementById(id);
const S = { llave: '', modelo: '', id: null, info: null, plan: null, color: '#7C3AED', modo: 'claro' };
const MUESTRAS = [
  ['Púrpura', '#7C3AED'], ['Rosa', '#E0467E'], ['Rojo', '#D1193B'], ['Naranja', '#F97316'],
  ['Verde', '#1F9D55'], ['Verde oscuro', '#14573A'], ['Azul', '#2563EB'], ['Gris', '#4B5563'], ['Negro', '#111111'],
];

const guardado = (() => { try { return localStorage.getItem('llave_claude') || sessionStorage.getItem('llave_claude') || ''; } catch { return ''; } })();

async function api(ruta, opts = {}) {
  const r = await fetch(ruta, opts);
  let datos = null;
  try { datos = await r.json(); } catch { /* respuesta sin JSON */ }
  if (!r.ok) throw new Error((datos && datos.detail) || `Error ${r.status}`);
  return datos;
}
const json = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
function msg(el, texto, tipo = '') { const e = $(el); e.textContent = texto; e.className = 'msg ' + tipo; }
function paso(n) {
  for (let i = 1; i <= 4; i++) $('s' + i).classList.toggle('bloqueada', i > n);
  document.querySelectorAll('#pasos span').forEach(s => s.classList.toggle('on', +s.dataset.p <= n));
}
function ocupado(btn, si, texto) {
  const b = $(btn); b.disabled = si;
  if (si) { b.dataset.t = b.textContent; b.textContent = texto || 'Trabajando…'; } else if (b.dataset.t) b.textContent = b.dataset.t;
}
function setAcento(c) { document.documentElement.style.setProperty('--acento', c); }

// ---------- 1. Llave ----------
(async () => {
  const cfg = await api('/api/config');
  $('modelo').innerHTML = cfg.modelos.map(([id, n]) => `<option value="${id}">${n}</option>`).join('');
  $('modelo').value = cfg.modelo;
  if (guardado) { $('llave').value = guardado; $('recordar').checked = true; }
})();

$('btnLlave').onclick = async () => {
  const llave = $('llave').value.trim();
  if (!llave) return msg('msgLlave', 'Pega tu llave primero.', 'err');
  ocupado('btnLlave', true, 'Verificando…');
  try {
    await api('/api/llave', json('POST', { llave }));
    S.llave = llave; S.modelo = $('modelo').value;
    try {
      sessionStorage.setItem('llave_claude', llave);
      if ($('recordar').checked) localStorage.setItem('llave_claude', llave); else localStorage.removeItem('llave_claude');
    } catch { /* almacenamiento no disponible */ }
    msg('msgLlave', 'Llave válida. Ya puedes subir tu video.', 'ok');
    paso(Math.max(2, S.id ? 3 : 2));
  } catch (e) { msg('msgLlave', e.message, 'err'); }
  ocupado('btnLlave', false);
};
$('modelo').onchange = () => { S.modelo = $('modelo').value; };

// ---------- 2. Video + paleta ----------
$('muestras').innerHTML = MUESTRAS.map(([n, c]) => `<button title="${n}" data-c="${c}" style="background:${c}"></button>`).join('');
function elegirColor(c) {
  S.color = c; $('color').value = c; setAcento(c);
  document.querySelectorAll('#muestras button').forEach(b => b.classList.toggle('on', b.dataset.c.toLowerCase() === c.toLowerCase()));
  if (S.id) cambiarPaleta();
}
$('muestras').onclick = e => { if (e.target.dataset.c) elegirColor(e.target.dataset.c); };
$('color').oninput = e => elegirColor(e.target.value);
$('modo').onclick = e => {
  const m = e.target.dataset.m; if (!m) return;
  S.modo = m; document.querySelectorAll('#modo button').forEach(b => b.classList.toggle('on', b.dataset.m === m));
  if (S.id) cambiarPaleta();
};
elegirColor(S.color);
for (const [inp, lab] of [['fVideo', 'nVideo'], ['fSrt', 'nSrt']]) {
  $(inp).onchange = () => { const f = $(inp).files[0]; $(lab).textContent = f ? f.name : 'Elegir archivo…'; $(lab).classList.toggle('lleno', !!f); };
}

$('btnSubir').onclick = async () => {
  const v = $('fVideo').files[0], s = $('fSrt').files[0];
  if (!v || !s) return msg('msgSubir', 'Elige el video y el archivo SRT.', 'err');
  const fd = new FormData();
  fd.append('video', v); fd.append('subtitulos', s);
  fd.append('color', S.color); fd.append('modo', S.modo);
  fd.append('persona', $('persona').value); fd.append('rol', $('rol').value);
  ocupado('btnSubir', true, 'Subiendo…');
  try {
    const r = await api('/api/trabajos', { method: 'POST', body: fd });
    S.id = r.id; S.info = r.info; S.plan = null;
    msg('msgSubir', `Listo: ${r.info.W}×${r.info.H}, ${r.info.duracion.toFixed(1)} s, ${r.lineas} líneas de transcripción. Se exportará como ${r.salida}.`, 'ok');
    $('vid').src = `/api/trabajos/${S.id}/video`;
    $('zonaPlan').hidden = true;
    paso(3);
  } catch (e) { msg('msgSubir', e.message, 'err'); }
  ocupado('btnSubir', false);
};

let tPaleta = null;
function cambiarPaleta() {
  clearTimeout(tPaleta);
  tPaleta = setTimeout(async () => {
    try { await api(`/api/trabajos/${S.id}/paleta`, json('POST', { color: S.color, modo: S.modo })); if (S.plan) recargarVista(); }
    catch (e) { msg('msgSubir', e.message, 'err'); }
  }, 250);
}

// ---------- 3. Plan ----------
async function pedirPlan(cambios = '') {
  if (!S.llave) { paso(1); return msg('msgLlave', 'Verifica tu llave primero.', 'err'); }
  const btn = cambios ? 'btnCambios' : 'btnPlan';
  ocupado(btn, true, 'Claude está pensando el plan…');
  msg('msgPlan', 'Esto tarda entre 20 segundos y un minuto.');
  try {
    const r = await api(`/api/trabajos/${S.id}/plan`, json('POST', { llave: S.llave, modelo: S.modelo, cambios }));
    msg('msgPlan', `Plan listo (${r.uso.entrada + r.uso.salida} tokens).`, 'ok');
    mostrarPlan(r.plan, r.avisos);
    paso(4);
  } catch (e) { msg('msgPlan', e.message, 'err'); }
  ocupado(btn, false);
}
$('btnPlan').onclick = () => pedirPlan();
$('btnCambios').onclick = () => {
  const t = $('txtCambios').value.trim();
  if (!t) return msg('msgPlan', 'Escribe qué quieres cambiar.', 'err');
  pedirPlan(t);
};
$('btnJson').onclick = async () => {
  try { await guardarPlan(JSON.parse($('txtJson').value)); msg('msgPlan', 'Plan actualizado.', 'ok'); }
  catch (e) { msg('msgPlan', 'JSON no válido: ' + e.message, 'err'); }
};

const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
function mostrarPlan(plan, avisos = []) {
  S.plan = plan;
  $('zonaPlan').hidden = false;
  $('resumen').textContent = plan.resumen || '';
  $('avisos').innerHTML = avisos.map(a => `<li>${esc(a)}</li>`).join('');
  $('txtJson').value = JSON.stringify(plan, null, 1);
  const T = S.info.duracion;
  $('linea').innerHTML = plan.elementos.map(e => {
    const izq = e.inicio / T * 100, an = (e.fin - e.inicio) / T * 100;
    const txt = e.tipo === 'tarjeta' ? e.titulo : (e.items[0]?.texto || e.titulo);
    return `<div style="left:${izq}%;width:${an}%;background:${e.tipo === 'tarjeta' ? '#16151A' : 'var(--acento)'}" title="${esc(txt)}">${esc(txt)}</div>`;
  }).join('') + '<div class="cursor" id="cursorT"></div>';
  $('elementos').innerHTML = plan.elementos.map((e, i) => {
    const tiempos = `<input type="number" step="0.05" data-i="${i}" data-k="inicio" value="${e.inicio}"> – <input type="number" step="0.05" data-i="${i}" data-k="fin" value="${e.fin}"> s`;
    let campos;
    if (e.tipo === 'tarjeta') {
      campos = `<input data-i="${i}" data-k="titulo" value="${esc(e.titulo)}" placeholder="Título"><input data-i="${i}" data-k="subtitulo" value="${esc(e.subtitulo)}" placeholder="Subtítulo (opcional)">`;
    } else {
      campos = (e.titulo || e.diseno === 'lista' ? `<input data-i="${i}" data-k="titulo" value="${esc(e.titulo)}" placeholder="Encabezado">` : '')
        + (e.diseno === 'numero' ? `<input data-i="${i}" data-k="numero" value="${esc(e.numero)}" style="flex:0 0 60px">` : '')
        + e.items.map((it, j) => `<input data-i="${i}" data-j="${j}" value="${esc(it.texto)}" title="aparece en ${it.en}s">`).join('');
    }
    const nombre = e.tipo === 'tarjeta' ? 'Tarjeta' : `Pantalla · ${e.diseno}`;
    return `<div class="el"><header><span class="tag" style="background:${e.tipo === 'tarjeta' ? '#16151A' : 'var(--acento)'}">${nombre}</span>${tiempos}
      <button class="borrar" data-borrar="${i}">Quitar</button></header><div class="campos">${campos}</div><p class="motivo">${esc(e.motivo)}</p></div>`;
  }).join('');
  recargarVista();
}

let tEdit = null;
$('elementos').addEventListener('input', e => {
  const el = e.target, i = +el.dataset.i; if (isNaN(i)) return;
  const item = S.plan.elementos[i];
  if (el.dataset.j !== undefined) item.items[+el.dataset.j].texto = el.value;
  else if (el.dataset.k === 'inicio' || el.dataset.k === 'fin') item[el.dataset.k] = parseFloat(el.value) || 0;
  else item[el.dataset.k] = el.value;
  clearTimeout(tEdit);
  tEdit = setTimeout(() => guardarPlan(S.plan, true), 700);
});
$('elementos').addEventListener('click', e => {
  const i = e.target.dataset.borrar; if (i === undefined) return;
  S.plan.elementos.splice(+i, 1); guardarPlan(S.plan);
});
async function guardarPlan(plan, silencioso = false) {
  const r = await api(`/api/trabajos/${S.id}/plan`, json('PUT', { plan }));
  if (silencioso && r.plan.elementos.length === plan.elementos.length) { S.plan = r.plan; $('txtJson').value = JSON.stringify(r.plan, null, 1); recargarVista(); }
  else mostrarPlan(r.plan, r.avisos);
}

// Vista previa: el clip HTML encima del video, sincronizado con su tiempo.
function recargarVista() { $('capa').src = `/api/trabajos/${S.id}/vista_previa?render&v=${Date.now()}`; }
function ajustarCapa() {
  if (!S.info) return;
  const v = $('vid'), c = $('capa');
  c.style.width = S.info.W + 'px'; c.style.height = S.info.H + 'px';
  c.style.transform = `scale(${v.clientWidth / S.info.W})`;
}
$('vid').addEventListener('loadedmetadata', ajustarCapa);
addEventListener('resize', ajustarCapa);
new ResizeObserver(ajustarCapa).observe($('vid'));
(function sincronizar() {
  const v = $('vid'), w = $('capa').contentWindow;
  try { if (w && typeof w.seek === 'function') w.seek(v.currentTime); } catch { /* aún cargando */ }
  const cur = $('cursorT'); if (cur && S.info) cur.style.left = (v.currentTime / S.info.duracion * 100) + '%';
  requestAnimationFrame(sincronizar);
})();

// ---------- 4. Exportar ----------
$('btnRender').onclick = async () => {
  ocupado('btnRender', true, 'Exportando…');
  $('barra').hidden = false; $('zonaFinal').hidden = true;
  try {
    await api(`/api/trabajos/${S.id}/render`, { method: 'POST' });
    const r = await esperar();
    $('vidFinal').src = `/api/trabajos/${S.id}/resultado?v=${Date.now()}`;
    $('descargar').href = `/api/trabajos/${S.id}/resultado`;
    $('descargar').download = r.archivo;
    $('descargar').textContent = `Descargar ${r.archivo}`;
    $('zonaFinal').hidden = false;
    msg('msgRender', 'Video listo.', 'ok');
  } catch (e) { msg('msgRender', e.message, 'err'); }
  ocupado('btnRender', false);
};
async function esperar() {
  for (;;) {
    const r = await api(`/api/trabajos/${S.id}/estado`);
    $('barraIn').style.width = Math.round(r.progreso * 100) + '%';
    msg('msgRender', r.mensaje);
    if (r.estado === 'listo') return r;
    if (r.estado === 'error') throw new Error(r.mensaje);
    await new Promise(ok => setTimeout(ok, 1000));
  }
}
