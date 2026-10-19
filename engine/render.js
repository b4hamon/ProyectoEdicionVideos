// Renderiza un clip HTML cuadro por cuadro con desenfoque de movimiento.
// uso: node engine/render.js clip.html salida.mov <fps, ej. 30/1 | 30000/1001> [subcuadros]
// Clips con fondo transparente -> ProRes 4444 (.mov) con canal alfa.
// Basado en el render.js del motor motion-broll; añade subcuadros configurables y progreso.
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const { pathToFileURL } = require('url');

(async () => {
  const [html, out, fpsArg = '30/1', kArg] = process.argv.slice(2);
  const [num, den] = fpsArg.includes('/') ? fpsArg.split('/').map(Number) : [Number(fpsArg), 1];
  const FPS = num / den;
  const K = Math.max(1, Math.min(8, Number(kArg || process.env.SUBCUADROS || 4)));

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  const errs = [];
  page.on('pageerror', e => errs.push(e.message));
  await page.goto(pathToFileURL(path.resolve(html)).href + '?render');
  await page.evaluate(() => document.fonts.load('700 32px Geist'));
  await page.evaluate(() => document.fonts.ready);
  const info = await page.evaluate(() => ({
    T: window.DURATION,
    W: document.getElementById('stage').offsetWidth,
    H: document.getElementById('stage').offsetHeight,
    alpha: document.documentElement.classList.contains('alpha'),
  }));
  await page.setViewportSize({ width: info.W, height: info.H });

  const N = Math.round(info.T * FPS);
  const sub = 1 / (FPS * 2 * K); // obturador de 180°
  const inRate = `${num * K}/${den}`;
  const vf = K > 1
    ? `format=gbrap,tmix=frames=${K}:weights='${Array(K).fill(1).join(' ')}',select='eq(mod(n\\,${K})\\,${K - 1})',setpts=N/(${num}/${den})/TB`
    : 'format=gbrap';
  const enc = info.alpha
    ? ['-c:v', 'prores_ks', '-profile:v', '4', '-pix_fmt', 'yuva444p10le', '-vendor', 'apl0']
    : ['-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-movflags', '+faststart'];
  const ff = spawn('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', inRate, '-c:v', 'png', '-i', '-',
    '-vf', vf, '-r', `${num}/${den}`, ...enc, out]);
  ff.stderr.on('data', d => process.stderr.write(d));

  for (let f = 0; f < N; f++) {
    for (let k = 0; k < K; k++) {
      const t = Math.max(0, f / FPS + (k - (K - 1) / 2) * sub);
      await page.evaluate(t => seek(t), t);
      const buf = await page.screenshot({ type: 'png', omitBackground: info.alpha });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    }
    if (f % 5 === 0 || f === N - 1) process.stdout.write(`PROGRESO ${f + 1} ${N}\n`);
  }
  ff.stdin.end();
  const code = await new Promise(r => ff.on('close', r));
  await browser.close();
  if (errs.length) console.error('ERROR_PAGINA ' + errs[0]);
  console.log('LISTO', out, N, 'cuadros');
  process.exit(code === 0 && !errs.length ? 0 : 1);
})().catch(e => { console.error(e); process.exit(1); });
