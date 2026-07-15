import requests

from core import config

TIMEOUT = 8


class HomeAssistantError(Exception):
    pass


def _base_url():
    return (config.get("home_assistant", "base_url", default="") or "").rstrip("/")


def _token():
    return config.get("home_assistant", "token", default="") or ""


def _headers():
    return {"Authorization": f"Bearer {_token()}", "Content-Type": "application/json"}


def list_lights():
    base_url = _base_url()
    if not base_url or not _token() or "REEMPLAZA" in _token():
        raise HomeAssistantError("Configura home_assistant.base_url y token en config.yaml")

    try:
        response = requests.get(f"{base_url}/api/states", headers=_headers(), timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HomeAssistantError(str(exc)) from exc

    lights = []
    for entity in response.json():
        entity_id = entity.get("entity_id", "")
        if not entity_id.startswith("light."):
            continue
        name = entity.get("attributes", {}).get("friendly_name", entity_id)
        lights.append({"entity_id": entity_id, "name": name, "state": entity.get("state")})

    return lights


def set_light(entity_id, turn_on):
    base_url = _base_url()
    service = "turn_on" if turn_on else "turn_off"
    try:
        response = requests.post(
            f"{base_url}/api/services/light/{service}",
            headers=_headers(),
            json={"entity_id": entity_id},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HomeAssistantError(str(exc)) from exc


def call_service(domain, service, payload):
    base_url = _base_url()
    if not base_url or not _token() or "REEMPLAZA" in _token():
        raise HomeAssistantError("Configura home_assistant.base_url y token en config.yaml")

    try:
        response = requests.post(
            f"{base_url}/api/services/{domain}/{service}",
            headers=_headers(),
            json=payload,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HomeAssistantError(str(exc)) from exc


def speak_on_alexa(text):
    """Hace que un Echo hable via la integracion Alexa Media Player.

    Requiere alexa.notify_service en config.yaml, ej: "notify.alexa_media_estudio".
    Encuentra el nombre exacto en HA: Herramientas de desarrollo > Acciones,
    busca "alexa_media".
    """
    notify_service = config.get("alexa", "notify_service", default="")
    if not notify_service or not notify_service.startswith("notify."):
        raise HomeAssistantError(
            "Configura alexa.notify_service en config.yaml (ej: notify.alexa_media_estudio)"
        )
    _, service = notify_service.split(".", 1)
    call_service("notify", service, {"message": text})
