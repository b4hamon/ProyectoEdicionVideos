"""Genera una paleta completa (tonos claros y oscuros) a partir de un solo color."""
import colorsys


def _hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(c * 255))):02X}" for c in rgb)


def _rgb(h):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _luz(color):
    r, g, b = _rgb(color)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def tonos(color: str):
    r, g, b = _rgb(color)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    t = lambda L: _hex(colorsys.hls_to_rgb(h, L, s))
    return {"c9": t(0.14), "c8": t(0.22), "c7": t(0.32), "c6": _hex((r, g, b)),
            "c5": t(min(l + 0.10, 0.72)), "c3": t(0.80), "c2": t(0.90), "c1": t(0.96)}


def paleta(color: str, modo: str = "claro"):
    """modo 'claro': fondos blancos con el color de acento. 'oscuro': fondos oscuros con texto blanco."""
    c = tonos(color)
    if modo == "oscuro":
        css = {
            "--wipe": c["c3"],
            "--fondo": f"radial-gradient(ellipse 90% 70% at 50% 40%,{c['c7']} 0%,{c['c8']} 55%,{c['c9']} 100%)",
            "--tx": "#FFFFFF", "--ac": c["c2"], "--num": c["c3"], "--badge": "#FFFFFF",
            "--cardbg": "#FFFFFF", "--cardbar": c["c8"], "--cardic": c["c8"], "--cardtx": c["c9"], "--cardsub": c["c7"],
        }
        js = {"badgeIcon": c["c8"], "cardIcon": "#FFFFFF"}
    else:
        css = {
            "--wipe": c["c6"],
            "--fondo": f"linear-gradient(180deg,#FFFFFF 0%,{c['c1']} 50%,{c['c2']} 100%)",
            "--tx": c["c9"], "--ac": c["c6"], "--num": c["c6"], "--badge": c["c6"],
            "--cardbg": c["c6"], "--cardbar": c["c1"], "--cardic": "#FFFFFF", "--cardtx": "#FFFFFF", "--cardsub": c["c1"],
        }
        js = {"badgeIcon": "#FFFFFF", "cardIcon": c["c6"]}
        if _luz(color) > 0.55:   # color muy claro (amarillo, blanco...): texto oscuro encima
            css.update({"--ac": c["c7"], "--cardtx": c["c9"], "--cardsub": c["c8"], "--cardbar": c["c8"]})
            js["badgeIcon"] = c["c9"]
    return {"css": css, "js": js, "tonos": c, "modo": modo, "color": c["c6"]}
