# Editor de animaciones con Claude en su versión Free

Programa local para editar videos cortos de una persona hablando a cámara (máximo 30 s). Le subes el video y su transcripción con tiempos (SRT). Claude, a través de su API, propone un **plan de edición**. Tú lo revisas con una vista previa en vivo, lo corriges si hace falta y, al aprobarlo, el programa exporta el **video editado** con las animaciones encima y el audio original.

Estas son las animaciones que se usaron en los videos de presentación:

- **Tarjeta**: rótulo con ícono, nombre o idea clave y subtítulo. Entra de izquierda a derecha mientras la persona sigue en cámara.
- **Pantalla completa**: entra con una cortina de dos capas que sube desde abajo y sale hacia arriba. Tiene tres diseños:
  - `palabras`: ícono y palabras grandes apiladas.
  - `lista`: encabezado y filas con ícono.
  - `numero`: "1, 2, 3" para razones enumeradas.
- Cada texto aparece justo en la palabra que se dice, con desenfoque suave y sin rebotes.
- La paleta se arma sola a partir de **un color**, con fondo claro u oscuro.
- El nombre del archivo exportado va en mayúsculas: `NOMBRE_DEL_VIDEO_EDITADO.mp4`.

## Antes de empezar: la llave de la API

> **La API de Claude no viene incluida en las cuentas gratuitas (ni en Pro) de claude.ai.** Se paga aparte con créditos prepagados.

1. Entra a [platform.claude.com](https://platform.claude.com) con tu cuenta y carga créditos en **Settings → Billing**.
2. Crea una llave en [platform.claude.com/settings/keys](https://platform.claude.com/settings/keys). Empieza por `sk-ant-`.
3. Pégala en el programa. Solo viaja de tu navegador a tu propio computador y de ahí a la API de Anthropic. El servidor no la guarda.

**Costo aproximado:** Claude solo se usa para el plan, y la animación se hace en tu computador. Cada plan cuesta del orden de 2 a 10 centavos de dólar con Claude Sonnet 5.5. Con Claude Haiku 5.5 sale más barato. Los precios actualizados están en [la página de precios](https://platform.claude.com/docs/en/about-claude/pricing).

## Requisitos

- **Python 3.10 o superior**
- **Node.js 18 o superior** (para el motor de render con Chromium)
- **ffmpeg** en el PATH:
  - Windows: `winget install Gyan.FFmpeg`
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

## Instalación y uso

### Paso a paso en Windows

1. Abre PowerShell e instala lo necesario (solo la primera vez):
   ```
   winget install Python.Python.3.12
   winget install OpenJS.NodeJS.LTS
   winget install Gyan.FFmpeg
   ```
2. Cierra y vuelve a abrir PowerShell. Comprueba que `python --version`, `node --version` y `ffmpeg -version` muestren una versión.
3. Descomprime el proyecto y haz doble clic en `iniciar.bat`. La primera vez tarda unos minutos.
4. Se abre el navegador en `http://127.0.0.1:8000`. No cierres la ventana negra mientras uses el editor; ciérrala (o presiona Ctrl+C) para apagarlo.

Si dice que falta Python, Node o ffmpeg, reinicia el computador después de instalarlos. Al instalar Python a mano, marca la casilla *Add Python to PATH*.

### Forma rápida

- Windows: doble clic en `iniciar.bat`.
- macOS / Linux: `./iniciar.sh`.

La primera vez instala todo (entorno de Python, Playwright y Chromium). Después abre el editor en el navegador, en `http://127.0.0.1:8000`.

### A mano

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
npm install
npx playwright install chromium
python -m app
```

### Con Docker

```bash
docker build -t editor-animaciones .
docker run -p 8000:8000 editor-animaciones
```

Luego abre `http://localhost:8000`.

## Cómo se usa

1. **Llave**: pega tu llave `sk-ant-...`, elige el modelo y pulsa *Verificar*. La verificación no gasta tokens.
2. **Video**: sube el `.mp4` (30 s como máximo) y el `.srt`. Puedes escribir el nombre correcto de la persona y su rol o tema, que es útil cuando la transcripción escribe mal el nombre. Elige el color y si quieres el fondo claro u oscuro.
3. **Plan**: pulsa *Pedir el plan a Claude*. Vas a ver:
   - un resumen y una línea de tiempo;
   - cada tarjeta o pantalla, con sus tiempos y textos editables y el motivo de cada decisión;
   - la **vista previa en vivo**: dale play al video y las animaciones corren encima, sincronizadas.

   Puedes corregir textos y tiempos a mano, quitar elementos, cambiar el color, pedirle cambios a Claude en lenguaje normal (por ejemplo, "quita la segunda pantalla") o editar el JSON directamente.
4. **Exportar**: pulsa *Aprobar plan y exportar*. Se renderiza cuadro por cuadro con desenfoque de movimiento y se une a tu video con el audio original. Al terminar lo puedes ver y descargar.

El render toma alrededor de 1 a 3 minutos para un video vertical de 30 s, según tu computador. Para que sea más rápido (con menos desenfoque de movimiento), arranca con `SUBCUADROS=1`.

### ¿Cómo saco el SRT?

En Premiere: *Texto → Transcribir → Crear subtítulos → Exportar a SRT*. En CapCut: *Subtítulos automáticos → Exportar → SRT*. Claude no puede oír el audio, así que los tiempos salen del SRT.

### Por consola (sin interfaz)

```bash
# Pide el plan a Claude, te lo muestra y pregunta antes de renderizar
python -m app.cli video.mp4 video.srt --color "#7C3AED" --persona "Nombre Apellido" --llave sk-ant-...

# Usa un plan ya hecho (no llama a la API)
python -m app.cli video.mp4 video.srt --color "#E0467E" --plan ejemplos/plan_ejemplo.json --si
```

## Cómo funciona

```
video + SRT ──► ffprobe (resolución, fps, duración) + 4 fotogramas
                    │
                    ▼
        API de Claude (texto + imágenes) ──► plan JSON con esquema fijo (structured outputs)
                    │
                    ▼
        limpieza del plan (tiempos, cruces, íconos) ──► vista previa en vivo (iframe sobre el video)
                    │  aprobado
                    ▼
        engine/runtime.js arma el clip HTML ──► Playwright/Chromium lo renderiza a .mov con alfa
                    │
                    ▼
        ffmpeg lo pone encima del video original (audio intacto) ──► NOMBRE_EDITADO.mp4
```

| Carpeta / archivo | Qué hace |
|---|---|
| `app/main.py` | Servidor web (FastAPI) y rutas de la API local |
| `app/planner.py` | Llamada a la API de Claude con salida JSON estructurada |
| `app/plan_schema.py` | Esquema del plan, lista de íconos y limpieza de tiempos |
| `app/pipeline.py`, `app/media.py` | Preparación del video, render y composición con ffmpeg |
| `app/palette.py` | Paleta completa a partir de un color |
| `engine/` | Motor de animación (motion-broll) + `runtime.js` con las tarjetas, pantallas y cortinas |
| `prompts/estilo.md` | **Las reglas de estilo que sigue Claude.** Edítalo para cambiar cómo planea |
| `static/` | Interfaz web |
| `trabajos/` | Archivos de cada video procesado (se crea solo; puedes borrarla) |

## Personalizar

- **Estilo del plan**: edita `prompts/estilo.md`.
- **Modelo por defecto**: variable de entorno `MODELO_CLAUDE` (por ejemplo, `claude-haiku-5-5`).
- **Íconos**: agrega trazos en `engine/runtime.js` (objeto `M.IC`) y el nombre en `ICONOS` de `app/plan_schema.py`.
- **Animaciones**: tiempos, tamaños y cortina están en `engine/runtime.js` y `engine/runtime.css`.
- **Duración máxima**: `DURACION_MAXIMA` en `app/config.py`.

## Seguridad y privacidad

- Por defecto el servidor solo escucha en `127.0.0.1`, así que nadie más de tu red puede usarlo. Si cambias `HOST=0.0.0.0` (como en Docker), cualquiera con acceso a esa red podría usarlo.
- La llave no se escribe en disco. Si marcas *Recordar*, queda guardada en el `localStorage` de tu navegador.
- A la API de Anthropic solo se envían la transcripción y 4 fotogramas pequeños del video, nunca el video completo.

## Pruebas

```bash
pip install pytest
python -m pytest tests
```

## Créditos y licencias

- Motor de animación basado en la habilidad **motion-broll** (`Barty-Bart/motion-graphics`). Revisa su licencia antes de publicar; los detalles están en `engine/LEEME.md`.
- Fuentes Geist y Geist Mono bajo la SIL Open Font License.
