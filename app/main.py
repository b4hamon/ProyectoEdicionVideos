"""Servidor web local: subir video + SRT → plan con Claude → vista previa → video editado."""
import json
import shutil
import threading
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import DURACION_MAXIMA, ESTATICOS, MODELO_POR_DEFECTO, MODELOS, TRABAJOS
from .palette import paleta
from .pipeline import construir_clip, nombre_salida, preparar, renderizar
from .plan_schema import ICONOS, limpiar_plan
from .planner import ErrorClaude, pedir_plan, verificar_llave

app = FastAPI(title="Editor de animaciones con Claude")
ESTADOS: dict = {}
_render_lock = threading.Lock()
EXT_VIDEO = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}


def _carpeta(tid: str) -> Path:
    c = TRABAJOS / tid
    if not tid.isalnum() or not (c / "trabajo.json").exists():
        raise HTTPException(404, "Trabajo no encontrado.")
    return c


def _datos(c: Path) -> dict:
    return json.loads((c / "trabajo.json").read_text(encoding="utf-8"))


def _guardar(c: Path, datos: dict):
    (c / "trabajo.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")


def _video(c: Path) -> Path:
    return next(p for p in c.iterdir() if p.stem == "entrada")


def _plan(c: Path) -> dict:
    p = c / "plan.json"
    if not p.exists():
        raise HTTPException(400, "Todavía no hay plan.")
    return json.loads(p.read_text(encoding="utf-8"))


@app.get("/api/config")
def config():
    return {"modelos": MODELOS, "modelo": MODELO_POR_DEFECTO, "duracion_maxima": DURACION_MAXIMA, "iconos": ICONOS}


class Llave(BaseModel):
    llave: str


@app.post("/api/llave")
def probar_llave(b: Llave):
    try:
        verificar_llave(b.llave)
    except ErrorClaude as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


@app.post("/api/trabajos")
async def crear_trabajo(video: UploadFile = File(...), subtitulos: UploadFile = File(...),
                        color: str = Form("#7C3AED"), modo: str = Form("claro"),
                        persona: str = Form(""), rol: str = Form("")):
    ext = Path(video.filename or "").suffix.lower()
    if ext not in EXT_VIDEO:
        raise HTTPException(400, "Sube un video .mp4, .mov, .m4v, .webm o .mkv.")
    tid = uuid.uuid4().hex[:12]
    c = TRABAJOS / tid
    c.mkdir(parents=True)
    ruta = c / f"entrada{ext}"
    with ruta.open("wb") as f:
        shutil.copyfileobj(video.file, f)
    srt = (await subtitulos.read()).decode("utf-8", errors="ignore")
    try:
        datos = preparar(c, ruta, srt, color, "oscuro" if modo == "oscuro" else "claro", persona.strip(), rol.strip())
    except (ValueError, RuntimeError) as e:
        shutil.rmtree(c, ignore_errors=True)
        raise HTTPException(400, str(e))
    datos["nombre_original"] = video.filename
    _guardar(c, datos)
    return {"id": tid, "info": datos["info"], "lineas": len(datos["cues"]), "salida": nombre_salida(video.filename)}


@app.get("/api/trabajos/{tid}/video")
def ver_video(tid: str):
    return FileResponse(_video(_carpeta(tid)))


class PedirPlan(BaseModel):
    llave: str
    modelo: str = MODELO_POR_DEFECTO
    cambios: str = ""


@app.post("/api/trabajos/{tid}/plan")
def generar_plan(tid: str, b: PedirPlan):
    c = _carpeta(tid)
    d = _datos(c)
    anterior = json.loads((c / "plan.json").read_text(encoding="utf-8")) if (b.cambios and (c / "plan.json").exists()) else None
    frames = [(t, Path(p)) for t, p in d["frames"]]
    try:
        plan, uso = pedir_plan(b.llave, b.modelo, d["info"], d["cues"], frames, d.get("persona", ""), d.get("rol", ""),
                               f"{d['color']} ({d['modo']})", anterior, b.cambios)
    except ErrorClaude as e:
        raise HTTPException(400, str(e))
    plan, avisos = limpiar_plan(plan, d["info"]["duracion"])
    (c / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"plan": plan, "avisos": avisos, "uso": uso}


class PlanEditado(BaseModel):
    plan: dict


@app.put("/api/trabajos/{tid}/plan")
def guardar_plan(tid: str, b: PlanEditado):
    c = _carpeta(tid)
    plan, avisos = limpiar_plan(b.plan, _datos(c)["info"]["duracion"])
    (c / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"plan": plan, "avisos": avisos}


class Paleta(BaseModel):
    color: str
    modo: str = "claro"


@app.post("/api/trabajos/{tid}/paleta")
def cambiar_paleta(tid: str, b: Paleta):
    c = _carpeta(tid)
    try:
        paleta(b.color, b.modo)
    except (ValueError, IndexError):
        raise HTTPException(400, "Color no válido. Usa formato #RRGGBB.")
    d = _datos(c)
    d["color"], d["modo"] = b.color, ("oscuro" if b.modo == "oscuro" else "claro")
    _guardar(c, d)
    return {"ok": True}


@app.get("/api/trabajos/{tid}/vista_previa", response_class=HTMLResponse)
def vista_previa(tid: str):
    c = _carpeta(tid)
    html = construir_clip(c, _plan(c), _datos(c))
    return HTMLResponse(html.read_text(encoding="utf-8"))


@app.post("/api/trabajos/{tid}/render")
def iniciar_render(tid: str):
    c = _carpeta(tid)
    plan, d = _plan(c), _datos(c)
    if ESTADOS.get(tid, {}).get("estado") in ("en_cola", "renderizando"):
        return ESTADOS[tid]
    salida = c / nombre_salida(d.get("nombre_original", "video.mp4"))
    ESTADOS[tid] = {"estado": "en_cola", "progreso": 0, "mensaje": "Esperando turno…", "archivo": salida.name}

    def tarea():
        with _render_lock:
            ESTADOS[tid].update(estado="renderizando", mensaje="Preparando la animación…")
            try:
                renderizar(c, _video(c), plan, d, salida,
                           lambda p, m: ESTADOS[tid].update(progreso=round(p, 3), mensaje=m))
                ESTADOS[tid].update(estado="listo", progreso=1, mensaje="Video listo")
            except Exception as e:  # noqa: BLE001
                ESTADOS[tid].update(estado="error", mensaje=str(e)[:500])

    threading.Thread(target=tarea, daemon=True).start()
    return ESTADOS[tid]


@app.get("/api/trabajos/{tid}/estado")
def estado(tid: str):
    _carpeta(tid)
    return ESTADOS.get(tid, {"estado": "sin_iniciar", "progreso": 0, "mensaje": ""})


@app.get("/api/trabajos/{tid}/resultado")
def resultado(tid: str):
    c = _carpeta(tid)
    nombre = nombre_salida(_datos(c).get("nombre_original", "video.mp4"))
    p = c / nombre
    if not p.exists():
        raise HTTPException(404, "El video todavía no está listo.")
    return FileResponse(p, media_type="video/mp4", filename=nombre)


@app.get("/")
def inicio():
    return FileResponse(ESTATICOS / "index.html")


app.mount("/static", StaticFiles(directory=ESTATICOS), name="static")
