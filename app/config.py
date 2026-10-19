"""Rutas y ajustes generales del programa."""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MOTOR = RAIZ / "engine"
ESTATICOS = RAIZ / "static"
PROMPTS = RAIZ / "prompts"
TRABAJOS = Path(os.environ.get("CARPETA_TRABAJOS", RAIZ / "trabajos"))
TRABAJOS.mkdir(parents=True, exist_ok=True)

DURACION_MAXIMA = 30.0          # segundos
MODELO_POR_DEFECTO = os.environ.get("MODELO_CLAUDE", "claude-sonnet-5-5")
MODELOS = [
    ("claude-sonnet-5-5", "Claude Sonnet 5.5 (recomendado)"),
    ("claude-haiku-5-5", "Claude Haiku 5.5 (el más barato)"),
    ("claude-opus-5-5", "Claude Opus 5.5 (el más cuidadoso)"),
]
SUBCUADROS = int(os.environ.get("SUBCUADROS", "4"))   # desenfoque de movimiento (1 = más rápido)
