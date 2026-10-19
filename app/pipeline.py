"""Pasos del trabajo: preparar video, renderizar animaciones y componer el video final."""
import json
import re
import shutil
import subprocess
import time
import unicodedata
from pathlib import Path

from . import clipgen, media
from .config import DURACION_MAXIMA, MOTOR, RAIZ, SUBCUADROS
from .palette import paleta
from .srt import leer_subtitulos


def nombre_salida(nombre_original: str) -> str:
    base = Path(nombre_original).stem
    base = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode()
    base = re.sub(r"[^A-Za-z0-9]+", "_", base).strip("_") or "VIDEO"
    return f"{base.upper()}_EDITADO.mp4"


def preparar(carpeta: Path, video: Path, srt_texto: str, color: str, modo: str, persona: str = "", rol: str = ""):
    info = media.probar(video)
    if info["duracion"] > DURACION_MAXIMA + 0.5:
        raise ValueError(f"El video dura {info['duracion']:.1f} s; el máximo es {DURACION_MAXIMA:.0f} s.")
    cues = leer_subtitulos(srt_texto)
    if not cues:
        raise ValueError("No se encontraron líneas con tiempos en el archivo de subtítulos (SRT o VTT).")
    frames = media.fotogramas(video, carpeta / "fotogramas", info["duracion"])
    datos = {"info": info, "cues": cues, "color": color, "modo": modo, "persona": persona, "rol": rol,
             "frames": [[t, str(p)] for t, p in frames]}
    (carpeta / "trabajo.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    return datos


def construir_clip(carpeta: Path, plan: dict, datos: dict) -> Path:
    return clipgen.construir(plan, datos["info"], paleta(datos["color"], datos["modo"]), carpeta)


def renderizar(carpeta: Path, video: Path, plan: dict, datos: dict, salida: Path, progreso=lambda p, m: None):
    """Renderiza el clip con alfa y lo compone sobre el video. progreso(fraccion, mensaje)."""
    html = construir_clip(carpeta, plan, datos)
    mov = carpeta / "animacion.mov"
    node = shutil.which("node")
    if not node:
        raise RuntimeError("No se encontró Node.js. Instálalo (versión 18 o superior).")
    proc = subprocess.Popen([node, str(MOTOR / "render.js"), str(html), str(mov), datos["info"]["fps"], str(SUBCUADROS)],
                            cwd=str(RAIZ), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            encoding="utf-8", errors="replace")
    t0 = time.time()
    for linea in proc.stdout:
        m = re.match(r"PROGRESO (\d+) (\d+)", linea)
        if m:
            f, n = int(m.group(1)), int(m.group(2))
            seg = (time.time() - t0) / max(f, 1) * (n - f)
            progreso(0.9 * f / n, f"Animando cuadro {f} de {n} (faltan ~{int(seg)} s)")
    err = proc.stderr.read()
    if proc.wait() != 0:
        raise RuntimeError("Falló el render de la animación: " + err[-600:])
    progreso(0.92, "Uniendo la animación con tu video…")
    media.componer(video, mov, salida, datos["info"]["audio"])
    progreso(1.0, "Listo")
    return salida
