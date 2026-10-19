"""Utilidades de video con ffprobe / ffmpeg."""
import base64
import json
import subprocess
from pathlib import Path


def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[-800:] or "ffmpeg falló")
    return r.stdout


def probar(video: Path):
    """Resolución (ya rotada), fps como fracción, duración y si tiene audio."""
    d = json.loads(_run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(video)]))
    v = next((s for s in d["streams"] if s.get("codec_type") == "video"), None)
    if not v:
        raise ValueError("El archivo no tiene pista de video.")
    w, h = int(v["width"]), int(v["height"])
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(float(sd["rotation"]))
    rot = int(v.get("tags", {}).get("rotate", rot) or 0)
    if abs(rot) % 180 == 90:
        w, h = h, w
    fps = v.get("avg_frame_rate") or v.get("r_frame_rate") or "30/1"
    if fps in ("0/0", "0/1"):
        fps = v.get("r_frame_rate", "30/1")
    n, dd = (int(x) for x in fps.split("/"))
    if n / max(dd, 1) > 120 or n / max(dd, 1) < 10:   # fps raros de celular: se normaliza
        fps = "30/1"
    dur = float(d["format"].get("duration") or v.get("duration") or 0)
    audio = any(s.get("codec_type") == "audio" for s in d["streams"])
    return {"W": w, "H": h, "fps": fps, "duracion": round(dur, 3), "audio": audio}


def fotogramas(video: Path, carpeta: Path, duracion: float, n: int = 4, ancho: int = 360):
    """Extrae n fotogramas JPEG repartidos en el video. Devuelve rutas."""
    carpeta.mkdir(parents=True, exist_ok=True)
    rutas = []
    for i in range(n):
        t = duracion * (0.1 + 0.8 * i / max(n - 1, 1))
        out = carpeta / f"f{i}.jpg"
        _run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
              "-vf", f"scale={ancho}:-2", "-q:v", "4", str(out)])
        rutas.append((round(t, 2), out))
    return rutas


def b64(path: Path):
    return base64.b64encode(path.read_bytes()).decode()


def componer(video: Path, clip: Path, salida: Path, audio: bool):
    """Pone el clip transparente encima del video y conserva el audio original."""
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(clip), "-filter_complex",
           "[0:v][1:v]overlay=0:0:format=auto:eof_action=pass,scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p[v]",
           "-map", "[v]"]
    if audio:
        cmd += ["-map", "0:a:0", "-c:a", "copy"]
    cmd += ["-c:v", "libx264", "-crf", "18", "-preset", "medium", "-movflags", "+faststart", str(salida)]
    _run(cmd)
