"""Agente de escritorio para MultiScreenPi.

Corre este script en tu PC (misma red que la Raspberry Pi) para que el
panel pueda abrir sitios web, lanzar apps, y cambiar el dispositivo de
salida de audio aqui.

Dependencias (solo para el cambio de audio, todo lo demas es libreria
estandar): pip install pycaw comtypes

Uso:
    python agent.py

Autoarranque con Windows: copia start_agent.vbs a tu carpeta de Inicio
(shell:startup) para que se ejecute solo al iniciar sesion, sin ventana
de consola.

Configura TOKEN y APPS abajo, y copia esa misma URL/token en
config/config.yaml del panel, seccion "pc_control".

Seguridad: este servidor escucha en todas las interfaces de red (0.0.0.0)
y ejecuta lo que le pidan sin mas verificacion que el token. Es aceptable
en tu red domestica, pero NO expongas este puerto a internet (sin
port-forwarding en el router) y manten el token en secreto.
"""

import http.server
import json
import os
import webbrowser

import audio
import desktop_switch

PORT = 5566
TOKEN = "eldv71998"

# Nombre -> ruta a la app o acceso directo (.exe o .lnk). os.startfile la abre
# igual que si le dieras doble clic, asi que los .lnk funcionan sin problema.
APPS = {
    "android_studio": r"C:\Users\chris\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\JetBrains Toolbox\Android Studio.lnk",
}


class Handler(http.server.BaseHTTPRequestHandler):
    def _authorized(self):
        return self.headers.get("Authorization") == f"Bearer {TOKEN}"

    def _respond(self, status, message=""):
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        if message:
            self.wfile.write(message.encode("utf-8"))

    def do_GET(self):
        if not self._authorized():
            self._respond(401, "unauthorized")
            return

        if self.path == "/audio-devices":
            devices = audio.list_active_devices()
            current = audio.get_current_device_name()
            body = json.dumps({"devices": devices, "current": current})
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(body.encode("utf-8"))
            return

        self._respond(404, "ruta no encontrada")

    def do_POST(self):
        if not self._authorized():
            self._respond(401, "unauthorized")
            return

        length = int(self.headers.get("Content-Length", 0) or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._respond(400, "json invalido")
            return

        if self.path == "/open-url":
            url = body.get("url", "")
            if not url:
                self._respond(400, "falta 'url'")
                return
            webbrowser.open(url)
            self._respond(200, "ok")
            return

        if self.path == "/launch":
            app = body.get("app", "")
            command = APPS.get(app)
            if not command:
                self._respond(404, f"app '{app}' no configurada en APPS")
                return
            os.startfile(command)
            self._respond(200, "ok")
            return

        if self.path == "/set-audio-device":
            name = body.get("name", "")
            if not name:
                self._respond(400, "falta 'name'")
                return
            result = audio.set_default_device(name)
            if result is None:
                self._respond(404, f"no se encontro un dispositivo activo que contenga '{name}'")
                return
            self._respond(200, result)
            return

        if self.path == "/switch-desktop":
            direction = body.get("direction", "")
            if direction not in ("left", "right"):
                self._respond(400, "'direction' debe ser 'left' o 'right'")
                return
            desktop_switch.switch_desktop(direction)
            self._respond(200, "ok")
            return

        self._respond(404, "ruta no encontrada")

    def log_message(self, format, *args):  # silencia el log por defecto
        pass


if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Agente de escritorio escuchando en el puerto {PORT}. Ctrl+C para salir.")
    server.serve_forever()
