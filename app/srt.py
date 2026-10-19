"""Lectura de subtítulos SRT / VTT."""
import re

_T = r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})"


def _seg(h, m, s, ms):
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms.ljust(3, "0")) / 1000


def leer_subtitulos(texto: str):
    """Devuelve una lista de {inicio, fin, texto} ordenada por tiempo."""
    texto = texto.replace("﻿", "").replace("\r\n", "\n").replace("\r", "\n")
    cues = []
    for bloque in re.split(r"\n\s*\n", texto):
        lineas = [l.strip() for l in bloque.strip().split("\n") if l.strip()]
        for i, l in enumerate(lineas):
            m = re.search(_T + r"\s*-->\s*" + _T, l)
            if m:
                g = m.groups()
                txt = " ".join(re.sub(r"<[^>]+>", "", x) for x in lineas[i + 1:]).strip()
                if txt:
                    cues.append({"inicio": round(_seg(*g[:4]), 3), "fin": round(_seg(*g[4:]), 3), "texto": txt})
                break
    cues.sort(key=lambda c: c["inicio"])
    return cues


def como_texto(cues):
    return "\n".join(f"[{c['inicio']:.2f} – {c['fin']:.2f}] {c['texto']}" for c in cues)
