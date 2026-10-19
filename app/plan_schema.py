"""Formato del plan de edición: esquema JSON (para Claude) y limpieza/validación."""
import copy

ICONOS = ["user", "users", "shield", "lock", "heart", "check", "star", "sparkle", "leaf", "paw", "tree",
          "mountain", "house", "briefcase", "trend", "code", "bulb", "monitor", "chip", "cap", "book",
          "search", "plane", "ball", "cross", "dna", "globe", "target", "rocket", "chat", "flag", "music",
          "camera", "clock", "coin"]

DISENOS = ["palabras", "lista", "numero"]

_ITEM = {
    "type": "object",
    "properties": {
        "texto": {"type": "string", "description": "1 a 3 palabras dichas en el video"},
        "en": {"type": "number", "description": "segundo en que aparece (inicio de esa palabra en el SRT)"},
        "icono": {"type": "string", "enum": ICONOS},
    },
    "required": ["texto", "en", "icono"],
    "additionalProperties": False,
}

_TARJETA = {
    "type": "object",
    "properties": {
        "tipo": {"type": "string", "const": "tarjeta"},
        "inicio": {"type": "number"},
        "fin": {"type": "number"},
        "titulo": {"type": "string"},
        "titulo_en": {"type": "number"},
        "subtitulo": {"type": "string", "description": "vacío si no hace falta"},
        "subtitulo_en": {"type": "number"},
        "icono": {"type": "string", "enum": ICONOS},
        "posicion": {"type": "string", "enum": ["abajo", "medio"]},
        "motivo": {"type": "string", "description": "por qué va aquí, en una frase"},
    },
    "required": ["tipo", "inicio", "fin", "titulo", "titulo_en", "subtitulo", "subtitulo_en", "icono", "posicion", "motivo"],
    "additionalProperties": False,
}

_PANTALLA = {
    "type": "object",
    "properties": {
        "tipo": {"type": "string", "const": "pantalla"},
        "inicio": {"type": "number"},
        "fin": {"type": "number"},
        "diseno": {"type": "string", "enum": DISENOS},
        "numero": {"type": "string", "description": "solo para diseno 'numero' (ej. '1'); si no, vacío"},
        "icono": {"type": "string", "enum": ICONOS},
        "titulo": {"type": "string", "description": "encabezado corto; puede ir vacío en 'palabras'"},
        "titulo_en": {"type": "number"},
        "items": {"type": "array", "items": _ITEM},
        "motivo": {"type": "string"},
    },
    "required": ["tipo", "inicio", "fin", "diseno", "numero", "icono", "titulo", "titulo_en", "items", "motivo"],
    "additionalProperties": False,
}

ESQUEMA_PLAN = {
    "type": "object",
    "properties": {
        "resumen": {"type": "string", "description": "2-3 frases sobre la idea del montaje"},
        "elementos": {"type": "array", "items": {"anyOf": [_TARJETA, _PANTALLA]}},
    },
    "required": ["resumen", "elementos"],
    "additionalProperties": False,
}


def _num(x, d=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return d


def limpiar_plan(plan: dict, duracion: float):
    """Corrige tiempos, quita solapes y valores fuera de rango. Devuelve (plan, avisos)."""
    avisos = []
    plan = copy.deepcopy(plan or {})
    T = float(duracion)
    elems = []
    for e in plan.get("elementos", []) or []:
        if not isinstance(e, dict) or e.get("tipo") not in ("tarjeta", "pantalla"):
            continue
        e["inicio"] = round(max(0.15, min(_num(e.get("inicio")), T - 0.5)), 2)
        e["fin"] = round(max(e["inicio"] + 0.8, min(_num(e.get("fin"), T), T)), 2)
        if e.get("icono") not in ICONOS:
            e["icono"] = "sparkle"
        if e["tipo"] == "tarjeta":
            e["titulo"] = str(e.get("titulo", "")).strip()
            e["subtitulo"] = str(e.get("subtitulo", "") or "").strip()
            e["titulo_en"] = round(min(max(_num(e.get("titulo_en"), e["inicio"]), e["inicio"] + 0.12), e["fin"] - 0.3), 2)
            e["subtitulo_en"] = round(min(max(_num(e.get("subtitulo_en"), e["titulo_en"]), e["titulo_en"]), e["fin"] - 0.3), 2)
            e["posicion"] = e.get("posicion") if e.get("posicion") in ("abajo", "medio") else "abajo"
            if not e["titulo"]:
                continue
        else:
            e["diseno"] = e.get("diseno") if e.get("diseno") in DISENOS else "palabras"
            e["numero"] = str(e.get("numero", "") or "").strip()[:3]
            e["titulo"] = str(e.get("titulo", "") or "").strip()
            lo, hi = e["inicio"] + 0.35, max(e["inicio"] + 0.4, e["fin"] - 0.25)
            e["titulo_en"] = round(min(max(_num(e.get("titulo_en"), lo), lo), hi), 2)
            maxi = 3 if e["diseno"] == "numero" else 4
            items = []
            for it in (e.get("items") or [])[:maxi]:
                if not isinstance(it, dict) or not str(it.get("texto", "")).strip():
                    continue
                items.append({"texto": str(it["texto"]).strip(),
                              "en": round(min(max(_num(it.get("en"), lo), lo), hi), 2),
                              "icono": it.get("icono") if it.get("icono") in ICONOS else "sparkle"})
            items.sort(key=lambda i: i["en"])
            e["items"] = items
            if not items and not e["titulo"]:
                continue
        e["motivo"] = str(e.get("motivo", "") or "")
        elems.append(e)

    elems.sort(key=lambda e: e["inicio"])
    # Pantallas: sin cruces entre ellas (se deja al menos 0.7 s de cámara entre una y otra)
    pantallas = []
    for e in [x for x in elems if x["tipo"] == "pantalla"]:
        if pantallas and e["inicio"] < pantallas[-1]["fin"] + 0.7:
            nuevo = pantallas[-1]["fin"] + 0.7
            if e["fin"] - nuevo < 1.2:
                avisos.append(f"Se quitó la pantalla de {e['inicio']}s porque se cruzaba con otra.")
                continue
            avisos.append(f"La pantalla de {e['inicio']}s se movió a {nuevo:.2f}s para no cruzarse.")
            e["inicio"] = round(nuevo, 2)
        pantallas.append(e)
    # Tarjetas: no pueden quedar encima de una pantalla completa
    tarjetas = []
    for c in [x for x in elems if x["tipo"] == "tarjeta"]:
        for p in pantallas:
            if c["inicio"] < p["fin"] + 0.5 and c["fin"] > p["inicio"]:
                if c["inicio"] < p["inicio"]:
                    c["fin"] = min(c["fin"], p["inicio"] - 0.1)
                else:
                    c["inicio"] = p["fin"] + 0.5 if p["fin"] < T - 0.15 else T
        if c["fin"] - c["inicio"] < 1.0:
            avisos.append(f"Se quitó la tarjeta '{c['titulo']}' porque quedaba encima de una pantalla completa.")
            continue
        c["titulo_en"] = round(min(max(c["titulo_en"], c["inicio"] + 0.12), c["fin"] - 0.3), 2)
        c["subtitulo_en"] = round(min(max(c["subtitulo_en"], c["titulo_en"]), c["fin"] - 0.3), 2)
        tarjetas.append(c)
    plan["elementos"] = sorted(pantallas + tarjetas, key=lambda e: e["inicio"])
    plan["resumen"] = str(plan.get("resumen", "") or "")
    return plan, avisos
