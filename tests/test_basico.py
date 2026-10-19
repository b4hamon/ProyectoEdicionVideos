"""Pruebas rápidas: python -m pytest tests"""
from app.palette import paleta
from app.pipeline import nombre_salida
from app.plan_schema import limpiar_plan
from app.srt import leer_subtitulos

SRT = """1
00:00:01,369 --> 00:00:01,603
Es mi

2
00:00:01,603 --> 00:00:02,170
patria.
"""


def test_srt():
    c = leer_subtitulos("﻿" + SRT)
    assert len(c) == 2 and c[0]["inicio"] == 1.369 and c[1]["texto"] == "patria."


def test_nombre_salida():
    assert nombre_salida("Erika Torres Vélez.mp4") == "ERIKA_TORRES_VELEZ_EDITADO.mp4"


def test_paleta():
    p = paleta("#E0467E", "oscuro")
    assert p["css"]["--tx"] == "#FFFFFF" and p["tonos"]["c6"] == "#E0467E"


def test_limpiar_quita_cruces():
    plan = {"resumen": "x", "elementos": [
        {"tipo": "pantalla", "inicio": 2, "fin": 6, "diseno": "palabras", "numero": "", "icono": "nope", "titulo": "",
         "titulo_en": 2, "items": [{"texto": "Hola", "en": 1, "icono": "star"}], "motivo": ""},
        {"tipo": "pantalla", "inicio": 5, "fin": 6.5, "diseno": "lista", "numero": "", "icono": "star", "titulo": "B",
         "titulo_en": 5, "items": [], "motivo": ""},
        {"tipo": "tarjeta", "inicio": 0.5, "fin": 4, "titulo": "Nombre", "titulo_en": 0.6, "subtitulo": "", "subtitulo_en": 0,
         "icono": "user", "posicion": "abajo", "motivo": ""},
    ]}
    p, avisos = limpiar_plan(plan, 10)
    assert [e["tipo"] for e in p["elementos"]] == ["tarjeta", "pantalla"]
    assert p["elementos"][0]["fin"] <= 1.9
    assert p["elementos"][1]["icono"] == "sparkle"
    assert p["elementos"][1]["items"][0]["en"] >= 2.35
    assert avisos
