"""Uso por consola (sin interfaz):

  python -m app.cli video.mp4 subtitulos.srt --color "#7C3AED" --modo claro --persona "Nombre" \\
      --llave sk-ant-...            # pide el plan a Claude, lo muestra y pregunta antes de renderizar
  python -m app.cli video.mp4 subtitulos.srt --plan plan.json   # usa un plan ya hecho (sin API)
"""
import argparse
import json
import os
import uuid
from pathlib import Path

from .config import MODELO_POR_DEFECTO, TRABAJOS
from .pipeline import nombre_salida, preparar, renderizar
from .plan_schema import limpiar_plan


def main():
    a = argparse.ArgumentParser(description="Edita un video con animaciones planeadas por Claude.")
    a.add_argument("video"); a.add_argument("srt")
    a.add_argument("--color", default="#7C3AED"); a.add_argument("--modo", default="claro", choices=["claro", "oscuro"])
    a.add_argument("--persona", default=""); a.add_argument("--rol", default="")
    a.add_argument("--plan", help="plan JSON ya hecho (no llama a la API)")
    a.add_argument("--llave", default=os.environ.get("ANTHROPIC_API_KEY", ""))
    a.add_argument("--modelo", default=MODELO_POR_DEFECTO)
    a.add_argument("--si", action="store_true", help="no preguntar antes de renderizar")
    a.add_argument("--salida", default=".")
    x = a.parse_args()

    carpeta = TRABAJOS / uuid.uuid4().hex[:10]; carpeta.mkdir(parents=True)
    video = Path(x.video)
    datos = preparar(carpeta, video, Path(x.srt).read_text(encoding="utf-8", errors="ignore"), x.color, x.modo, x.persona, x.rol)
    if x.plan:
        plan = json.loads(Path(x.plan).read_text(encoding="utf-8"))
    else:
        from .planner import pedir_plan
        frames = [(t, Path(p)) for t, p in datos["frames"]]
        plan, uso = pedir_plan(x.llave, x.modelo, datos["info"], datos["cues"], frames, x.persona, x.rol, f"{x.color} ({x.modo})")
        print(f"Tokens usados: {uso}")
    plan, avisos = limpiar_plan(plan, datos["info"]["duracion"])
    print("\nPLAN:", plan["resumen"])
    for e in plan["elementos"]:
        txt = e["titulo"] if e["tipo"] == "tarjeta" else " / ".join([e["titulo"]] + [i["texto"] for i in e["items"]]).strip(" /")
        print(f"  {e['inicio']:5.2f}–{e['fin']:5.2f}  {e['tipo']:8} {txt}")
    for av in avisos:
        print("  aviso:", av)
    (carpeta / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    if not x.si and input("\n¿Renderizar? [s/N] ").strip().lower() not in ("s", "si", "sí", "y"):
        print("Plan guardado en", carpeta / "plan.json"); return
    salida = Path(x.salida) / nombre_salida(video.name)
    renderizar(carpeta, video, plan, datos, salida, lambda p, m: print(f"\r{int(p*100):3d}%  {m}", end="", flush=True))
    print("\nVideo listo:", salida)


if __name__ == "__main__":
    main()
