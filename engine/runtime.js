/* Arma el clip de animaciones a partir de window.PLAN (plan aprobado) y window.PAL (paleta).
   Todo es una función pura del tiempo t: el render puede pedir cualquier instante en cualquier orden.
   Lienzo base 478x850 (vertical); se escala para la resolución real del video. */
(function () {
  const P = window.PLAN, C = window.PAL;
  const W = P.W, H = P.H, T = P.T, BW = 478, BH = 850;
  const k = (W / H) <= (BW / BH) ? W / BW : H / BH;
  const OX = (W - BW * k) / 2, OY = (H - BH * k) / 2;
  const cl = x => Math.max(0, Math.min(1, x));
  const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const $ = id => document.getElementById(id);

  // Iconos extra (misma familia de trazo que el motor)
  Object.assign(M.IC, {
    user: ['M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2', 'M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z'],
    users: ['M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2', 'M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z', 'M22 21v-2a4 4 0 0 0-3-3.87', 'M16 3.13a4 4 0 0 1 0 7.75'],
    shield: ['M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z', 'm9 12 2 2 4-4'],
    lock: ['M5 11h14a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2Z', 'M7 11V7a5 5 0 0 1 10 0v4'],
    heart: ['M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z'],
    star: ['M12 3l2.4 6.1L21 10l-5 4.2L17.6 21 12 17.5 6.4 21 8 14.2 3 10l6.6-.9Z'],
    leaf: ['M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z', 'M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12'],
    paw: ['M11 2a2 2 0 1 0 0 4 2 2 0 0 0 0-4Z', 'M18 6a2 2 0 1 0 0 4 2 2 0 0 0 0-4Z', 'M20 14a2 2 0 1 0 0 4 2 2 0 0 0 0-4Z', 'M4 4a2 2 0 1 0 0 4 2 2 0 0 0 0-4Z', 'M9 10a5 5 0 0 1 5 5v3.5a3.5 3.5 0 0 1-6.84 1.045Q6.52 17.48 4.46 16.84A3.5 3.5 0 0 1 5.5 10Z'],
    tree: ['M12 22v-7', 'M12 15c3.9 0 7-2.7 7-6.5S15.9 2 12 2 5 4.7 5 8.5 8.1 15 12 15Z'],
    mountain: ['m8 3 4 8 5-5 5 15H2L8 3z'],
    house: ['M3 10.5 12 3l9 7.5', 'M5 9v11h14V9', 'M10 20v-6h4v6'],
    briefcase: ['M4 7h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2Z', 'M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2', 'M2 13h20'],
    trend: ['m22 7-8.5 8.5-5-5L2 17', 'M16 7h6v6'],
    code: ['m8 7-5 5 5 5', 'm16 7 5 5-5 5', 'M14 4l-4 16'],
    bulb: ['M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5', 'M9 18h6', 'M10 22h4'],
    monitor: ['M4 4h16a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z', 'M8 21h8', 'M12 17v4'],
    cap: ['M22 10 12 5 2 10l10 5 10-5Z', 'M6 12v5c3 2 9 2 12 0v-5', 'M22 10v6'],
    book: ['M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20'],
    plane: ['M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z'],
    ball: ['M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Z', 'm12 8 4 3-1.5 4.5h-5L8 11z', 'M12 2v6', 'm16 11 5.5-1.5', 'm14.5 15.5 3 4', 'm9.5 15.5-3 4', 'M8 11 2.5 9.5'],
    cross: ['M12 2v20', 'M5 8h14'],
    dna: ['M2 15c6.667-6 13.333 0 20-6', 'M9 22c1.798-1.998 2.518-3.995 2.807-5.993', 'M15 2c-1.798 1.998-2.518 3.995-2.807 5.993', 'm17 6-2.5-2.5', 'm14 8-1-1', 'm7 18 2.5 2.5', 'm10 16 1.5 1.5'],
    globe: ['M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Z', 'M2 12h20', 'M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z'],
    target: ['M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Z', 'M12 18a6 6 0 1 0 0-12 6 6 0 0 0 0 12Z', 'M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z'],
    rocket: ['M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z', 'm12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z', 'M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0', 'M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5'],
    chat: ['M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z'],
    flag: ['M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z', 'M4 22v-7'],
    music: ['M9 18V5l12-2v13', 'M6 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z', 'M18 19a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z'],
    camera: ['M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z', 'M12 16a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z'],
  });
  const icon = (n, size, color, sw = 2.2) => M.icon(M.IC[n] ? n : 'sparkle', size, color, sw);

  // ---------- capas base ----------
  const world = $('world');
  const box = id => `<div id="${id}" class="box" style="left:${OX}px;top:${OY}px;transform:scale(${k})"></div>`;
  world.insertAdjacentHTML('afterbegin', `<div id="wG"></div><div id="wM">${box('SL')}</div>${box('CL')}`);
  // Una fila transparente abajo: si el cuadro queda 100% opaco el PNG pierde el alfa.
  for (const id of ['wG', 'wM']) { $(id).style.width = W + 'px'; $(id).style.height = (H - 1) + 'px'; }
  const SL = $('SL'), CL = $('CL');
  const mk = (parent, cls, style, html) => {
    const e = document.createElement('div'); e.className = cls;
    if (style) e.style.cssText = style; if (html != null) e.innerHTML = html;
    parent.appendChild(e); return e;
  };

  // ---------- animaciones elementales ----------
  const rev = (el, t, t0, dy = 16, lin = 0.3) => {
    const v = M.vis(t, t0, null, { din: 0, lin });
    el.style.opacity = v.o.toFixed(4);
    el.style.filter = v.blur > 0.05 ? `blur(${(v.blur * 0.5).toFixed(2)}px)` : 'none';
    el.style.transform = `translateY(${((1 - v.a) * dy).toFixed(2)}px)`;
  };
  const pop = (el, t, t0, lin = 0.38) => {
    const a = M.eo((t - t0) / lin);
    el.style.opacity = cl((t - t0) / 0.12).toFixed(3);
    el.style.transform = `scale(${(0.6 + 0.4 * a).toFixed(4)})`;
  };
  const slide = (el, t, t0, lin = 0.4) => {
    const a = M.eo((t - t0) / lin);
    el.style.opacity = cl((t - t0) / 0.15).toFixed(3);
    el.style.transform = `translateX(${((1 - a) * -70).toFixed(1)}px)`;
  };
  const grow = (el, t, t0) => { el.style.transform = `scaleX(${M.eio(cl((t - t0) / 0.5)).toFixed(3)})`; };
  const CARD = (el, t, t0, t1) => {
    const a = M.eio(cl((t - t0) / 0.4)), b = M.eio(cl((t - t1) / 0.3));
    el.style.clipPath = `inset(0 ${((1 - a) * 100).toFixed(2)}% 0 ${(b * 100).toFixed(2)}% round 20px)`;
    el.style.display = (t < t0 || b >= 1) ? 'none' : 'block';
  };
  // Cortina: capa de color fuerte + capa de fondo; entran desde abajo, salen hacia arriba.
  const wipe = (t, wi, wo) => {
    const gi = M.eio(cl((t - wi) / 0.30)), mi = M.eio(cl((t - wi - 0.10) / 0.30));
    const go = M.eio(cl((t - wo - 0.10) / 0.30)), mo = M.eio(cl((t - wo) / 0.30));
    return {
      g: `inset(${((1 - gi) * 100).toFixed(2)}% 0 ${(go * 100).toFixed(2)}% 0)`,
      m: `inset(${((1 - mi) * 100).toFixed(2)}% 0 ${(mo * 100).toFixed(2)}% 0)`,
      gOn: !(t < wi || go >= 1), mOn: !(t < wi + 0.1 || mo >= 1),
    };
  };

  const anims = []; // funciones f(t)
  const at = (x, lo) => Math.max(Number(x) || 0, lo);

  // ---------- pantallas completas ----------
  const scenes = P.elementos.filter(e => e.tipo === 'pantalla').sort((a, b) => a.inicio - b.inicio);
  scenes.forEach((s, i) => {
    const d = mk(SL, 'scene'); s._el = d;
    s._wo = s.fin >= T - 0.15 ? 1e9 : s.fin;   // la última puede quedarse hasta el final
    s._end = s._wo + 0.6;
    const t0 = s.inicio + 0.35;
    const items = (s.items || []).slice(0, s.diseno === 'numero' ? 3 : 4);
    const blocks = []; // {h, gap, make(y)}
    if (s.diseno === 'numero' && s.numero) {
      blocks.push({ h: 250, gap: 24, make: y => { const e = mk(d, 'num', `top:${y}px;font-size:260px`, esc(s.numero)); anims.push(t => pop(e, t, at(s.inicio + 0.45, t0), 0.45)); } });
    }
    if (s.icono && s.icono !== 'ninguno' && s.diseno !== 'lista') {
      blocks.push({ h: 112, gap: 36, make: y => { const e = mk(d, 'badge', `top:${y}px`, icon(s.icono, 60, C.badgeIcon, 2.4)); anims.push(t => pop(e, t, at(s.diseno === 'numero' ? s.inicio + 0.8 : s.inicio + 0.45, t0), 0.4)); } });
    }
    if (s.titulo) {
      if (s.diseno === 'lista') {
        blocks.push({ h: 56, gap: 18, make: y => { const e = mk(d, 'big fit', `top:${y}px;font-size:54px`, `<span>${esc(s.titulo)}</span>`); anims.push(t => rev(e, t, at(s.titulo_en, t0), 20, 0.34)); } });
        blocks.push({ h: 6, gap: 44, make: y => { const e = mk(d, 'uline', `top:${y}px`); anims.push(t => grow(e, t, at(s.titulo_en, t0) + 0.3)); } });
      } else {
        blocks.push({ h: 46, gap: 22, make: y => { const e = mk(d, 'big sm fit', `top:${y}px;font-size:42px`, `<span>${esc(s.titulo)}</span>`); anims.push(t => rev(e, t, at(s.titulo_en, t0), 16, 0.3)); } });
      }
    }
    items.forEach((it, j) => {
      const te = at(it.en, t0);
      if (s.diseno === 'lista') {
        blocks.push({ h: 100, gap: 22, make: y => {
          const r = mk(d, 'lrow', `top:${y}px`);
          mk(r, 'ri', '', icon(it.icono, 46, C.badgeIcon, 2.3));
          mk(r, 'rt fit', '', `<span>${esc(it.texto)}</span>`);
          anims.push(t => slide(r, t, te));
        } });
      } else {
        const fs = s.diseno === 'numero' ? 80 : 86;
        blocks.push({ h: fs + 6, gap: 8, make: y => { const e = mk(d, 'big fit' + (j % 2 ? ' ac' : ''), `top:${y}px;font-size:${fs}px`, `<span>${esc(it.texto)}</span>`); anims.push(t => rev(e, t, te, 22, 0.34)); } });
      }
    });
    const total = blocks.reduce((a, b, j) => a + b.h + (j < blocks.length - 1 ? b.gap : 0), 0);
    let y = Math.max(40, (BH - total) / 2 - 10);
    for (const b of blocks) { b.make(y); y += b.h + b.gap; }
  });

  // ---------- tarjetas (nombre, ideas cortas) ----------
  const cards = P.elementos.filter(e => e.tipo === 'tarjeta');
  cards.forEach(c => {
    const top = c.posicion === 'medio' ? 540 : 690;
    const e = mk(CL, 'card', `top:${top}px`); c._el = e;
    mk(e, 'bar');
    const ic = mk(e, 'ic', '', icon(c.icono, 34, C.cardIcon, 2.2));
    const sub = (c.subtitulo || '').trim();
    const t1 = mk(e, 't1 fit', `top:${sub ? 16 : 32}px`, `<span>${esc(c.titulo)}</span>`);
    const t2 = sub ? mk(e, 't2 fit', 'top:60px', `<span>${esc(sub)}</span>`) : null;
    const tt = at(c.titulo_en, c.inicio + 0.12);
    anims.push(t => {
      CARD(e, t, c.inicio, c.fin);
      rev(ic, t, c.inicio + 0.12, 8, 0.26); rev(t1, t, tt, 8, 0.26);
      if (t2) rev(t2, t, at(c.subtitulo_en, tt), 8, 0.26);
    });
  });

  // ---------- ajuste de textos largos (una vez cargada la fuente) ----------
  let fitted = false;
  const doFit = () => {
    const shown = [$('wG'), $('wM'), ...scenes.map(s => s._el), ...cards.map(c => c._el)];
    shown.forEach(e => { e.style.display = 'block'; });
    document.querySelectorAll('.fit').forEach(el => {
      const span = el.firstElementChild; if (!span) return;
      let fs = parseFloat(getComputedStyle(el).fontSize); const f0 = fs;
      while (span.offsetWidth > el.clientWidth && fs > 12) { fs -= 2; el.style.fontSize = fs + 'px'; }
      if (fs < f0 && el.classList.contains('big')) el.style.top = (parseFloat(el.style.top) + (f0 - fs) / 2) + 'px';
    });
  };

  window.RUNTIME_EXTRA = (t) => {
    if (!fitted && document.fonts.check('700 32px Geist')) { doFit(); fitted = true; }
    let act = null;
    for (const s of scenes) if (t >= s.inicio - 0.01 && t < s._end) { act = s; break; }
    const G = $('wG'), Mm = $('wM');
    if (act) {
      const w = wipe(t, act.inicio, act._wo);
      G.style.clipPath = w.g; Mm.style.clipPath = w.m;
      G.style.display = w.gOn ? 'block' : 'none'; Mm.style.display = w.mOn ? 'block' : 'none';
    } else { G.style.display = 'none'; Mm.style.display = 'none'; }
    for (const s of scenes) s._el.style.display = s === act ? 'block' : 'none';
    for (const f of anims) f(t);
  };
  document.fonts.load('700 32px Geist');
})();
