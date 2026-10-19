"""Convierte un plan aprobado en un clip HTML autocontenido para el motor de animación."""
import importlib.util
import json
from pathlib import Path

from .config import MOTOR

_spec = importlib.util.spec_from_file_location("motor_build", MOTOR / "build.py")
_build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_build)


def fragmento(plan: dict, info: dict, paleta: dict) -> str:
    datos = {"W": info["W"], "H": info["H"], "T": info["duracion"], "elementos": plan["elementos"]}
    js_plan = json.dumps(datos, ensure_ascii=False).replace("</", "<\\/")
    js_pal = json.dumps(paleta["js"]).replace("</", "<\\/")
    variables = ";".join(f"{k}:{v}" for k, v in paleta["css"].items())
    css = (MOTOR / "runtime.css").read_text(encoding="utf-8")
    runtime = (MOTOR / "runtime.js").read_text(encoding="utf-8")
    escena = (
        "M.scene({W:%d,H:%d,T:%.3f,bg:null,center:[0,0],intro:null,"
        "SH:{dot:{w:2,h:2,r:1,bg:'#000000',cam:1}},start:'dot',SEQ:[],"
        "geom:(t,g)=>{g.op=0;return g;},extra:(t)=>window.RUNTIME_EXTRA(t)});"
    ) % (info["W"], info["H"], info["duracion"])
    return (
        "<title>clip</title>\n"
        f"<style>:root{{{variables}}}\n{css}</style>\n"
        '<div data-slot="world"></div><!--/world-->\n'
        '<div data-slot="shape"></div><!--/shape-->\n'
        f"<script>window.PLAN={js_plan};window.PAL={js_pal};\n{runtime}\n{escena}</script>\n"
    )


def construir(plan: dict, info: dict, paleta: dict, carpeta: Path) -> Path:
    frag = carpeta / "clip_fragmento.html"
    frag.write_text(fragmento(plan, info, paleta), encoding="utf-8")
    html = carpeta / "clip.html"
    _build.build(str(frag), str(html))
    return html
