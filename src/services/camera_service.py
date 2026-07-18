import io
import threading
import time

import pygame
import requests

from services import home_assistant_service

# Tope de resolucion que se guarda en memoria (no el tamano en pantalla):
# mas grande que el area visible normal a proposito, para que el zoom
# muestre detalle real en vez de solo agrandar un recorte pequeno.
MAX_SIZE = (1280, 960)
HA_POLL_INTERVAL = 1.5
MJPEG_TIMEOUT = 8
BUFFER_SAFETY_LIMIT = 3_000_000


class CameraSource:
    """Interfaz comun: corre en un hilo aparte, expone .surface con el ultimo frame decodificado.

    .version sube cada vez que llega un frame nuevo, para que quien dibuje
    pueda cachear el escalado y no recalcularlo en cada cuadro.
    """

    def __init__(self):
        self.surface = None
        self.version = 0
        self.error = None
        self.running = False
        self._thread = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.error = None
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False

    def _run(self):
        raise NotImplementedError

    def _decode(self, jpg_bytes):
        try:
            image = pygame.image.load(io.BytesIO(jpg_bytes)).convert()
            w, h = image.get_size()
            max_w, max_h = MAX_SIZE
            scale = min(max_w / w, max_h / h, 1)
            if scale < 1:
                image = pygame.transform.smoothscale(image, (int(w * scale), int(h * scale)))
            self.surface = image
            self.version += 1
        except (pygame.error, OSError):
            pass


class MjpegSource(CameraSource):
    """Lee un stream MJPEG (multipart, tipo mjpg-streamer) buscando marcadores JPEG."""

    def __init__(self, url):
        super().__init__()
        self.url = url

    def _run(self):
        buffer = b""
        try:
            response = requests.get(self.url, stream=True, timeout=MJPEG_TIMEOUT)
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=4096):
                if not self.running:
                    break
                buffer += chunk

                start = buffer.find(b"\xff\xd8")
                if start == -1:
                    continue
                end = buffer.find(b"\xff\xd9", start + 2)
                if end == -1:
                    if len(buffer) > BUFFER_SAFETY_LIMIT:
                        buffer = b""
                    continue

                self._decode(buffer[start : end + 2])
                buffer = buffer[end + 2 :]
        except requests.RequestException as exc:
            self.error = str(exc)
        finally:
            self.running = False


class HaSnapshotSource(CameraSource):
    """Pide una foto a Home Assistant (funciona con cualquier camara que HA soporte, incl. ONVIF)."""

    def __init__(self, entity_id):
        super().__init__()
        self.entity_id = entity_id

    def _run(self):
        while self.running:
            try:
                jpg_bytes = home_assistant_service.get_camera_snapshot(self.entity_id)
                self._decode(jpg_bytes)
                self.error = None
            except home_assistant_service.HomeAssistantError as exc:
                self.error = str(exc)
            time.sleep(HA_POLL_INTERVAL)


def create_source(camera_config):
    cam_type = camera_config.get("type")
    if cam_type == "mjpeg":
        return MjpegSource(camera_config.get("url", ""))
    if cam_type == "ha_snapshot":
        return HaSnapshotSource(camera_config.get("entity_id", ""))
    raise ValueError(f"Tipo de camara desconocido: {cam_type}")
