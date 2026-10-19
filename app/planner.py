"""Le pide a Claude (API de Anthropic) el plan de edición en JSON."""
import json

import anthropic

from .config import PROMPTS
from .media import b64
from .plan_schema import ESQUEMA_PLAN, ICONOS
from .srt import como_texto


class ErrorClaude(Exception):
    pass


def cliente(api_key: str):
    if not api_key or not api_key.strip():
        raise ErrorClaude("Falta la llave de la API de Claude.")
    return anthropic.Anthropic(api_key=api_key.strip(), max_retries=2, timeout=180)


def _traducir(e: Exception) -> ErrorClaude:
    msg = str(e)
    if isinstance(e, anthropic.AuthenticationError):
        return ErrorClaude("La llave no es válida. Revisa que empiece por sk-ant- y que no esté vencida.")
    if isinstance(e, anthropic.PermissionDeniedError):
        return ErrorClaude("La llave no tiene permiso para usar este modelo.")
    if isinstance(e, anthropic.RateLimitError):
        return ErrorClaude("Demasiadas peticiones seguidas. Espera un minuto e inténtalo otra vez.")
    if "credit balance" in msg.lower():
        return ErrorClaude("Tu cuenta de la API no tiene créditos. Cárgalos en platform.claude.com → Billing.")
    if isinstance(e, anthropic.NotFoundError):
        return ErrorClaude("Ese modelo no existe o tu cuenta no tiene acceso a él.")
    if isinstance(e, anthropic.APIConnectionError):
        return ErrorClaude("No hay conexión con la API de Claude. Revisa tu internet.")
    return ErrorClaude(f"Error de la API de Claude: {msg[:300]}")


def verificar_llave(api_key: str):
    """Comprueba la llave sin gastar tokens (lista de modelos)."""
    try:
        cliente(api_key).models.list(limit=1)
    except anthropic.APIError as e:
        raise _traducir(e)


def pedir_plan(api_key, modelo, info, cues, frames, persona="", rol="", paleta_txt="",
               plan_anterior=None, cambios=""):
    estilo = (PROMPTS / "estilo.md").read_text(encoding="utf-8")
    contenido = []
    for t, ruta in frames:
        contenido.append({"type": "text", "text": f"Fotograma en el segundo {t}:"})
        contenido.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64(ruta)}})
    datos = [
        f"Video: {info['W']}x{info['H']} px, {info['duracion']:.2f} s.",
        f"Persona: {persona or '(no se indicó; usa el nombre si lo dice en el video)'}.",
        f"Rol o tema: {rol or '(no se indicó)'}.",
        f"Paleta elegida: {paleta_txt}. (El color ya lo pone el programa; tú solo decides contenido y tiempos.)",
        f"Íconos disponibles: {', '.join(ICONOS)}.",
        "",
        "Transcripción con tiempos (segundos):",
        como_texto(cues),
    ]
    if plan_anterior:
        datos += ["", "Plan anterior:", json.dumps(plan_anterior, ensure_ascii=False),
                  "", f"Cambios que pide el usuario: {cambios or '(ninguno)'}",
                  "Devuelve el plan completo corregido."]
    else:
        datos += ["", "Diseña el plan de animaciones para este video."]
    contenido.append({"type": "text", "text": "\n".join(datos)})

    try:
        r = cliente(api_key).messages.create(
            model=modelo,
            max_tokens=16000,
            system=estilo,
            messages=[{"role": "user", "content": contenido}],
            extra_body={"output_config": {"format": {"type": "json_schema", "schema": ESQUEMA_PLAN}}},
        )
    except anthropic.APIError as e:
        raise _traducir(e)
    if r.stop_reason == "refusal":
        raise ErrorClaude("Claude no quiso generar el plan para este video.")
    if r.stop_reason == "max_tokens":
        raise ErrorClaude("La respuesta se cortó. Vuelve a intentarlo.")
    texto = next((b.text for b in r.content if getattr(b, "type", "") == "text"), "")
    try:
        plan = json.loads(texto)
    except json.JSONDecodeError:
        raise ErrorClaude("Claude devolvió un plan que no se pudo leer. Vuelve a intentarlo.")
    uso = {"entrada": r.usage.input_tokens, "salida": r.usage.output_tokens}
    return plan, uso
