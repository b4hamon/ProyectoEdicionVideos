"""Arranca el editor: python -m app  (abre el navegador en http://127.0.0.1:8000)."""
import os
import threading
import webbrowser

import uvicorn

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    if host == "127.0.0.1" and not os.environ.get("NO_ABRIR"):
        threading.Timer(1.5, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
    print(f"Editor de animaciones en http://{host}:{port}  (Ctrl+C para cerrar)")
    uvicorn.run("app.main:app", host=host, port=port, log_level="warning")
