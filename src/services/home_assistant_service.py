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
    """Lee home_assistant.entities: lista de {entity_id, enabled}, agregada a
    mano desde el panel web. Si esta vacia/no configurada, muestra todas las
    light.* automaticamente. Las marcadas enabled=false no se muestran.
    """
    base_url = _base_url()
    if not base_url or not _token() or "REEMPLAZA" in _token():
        raise HomeAssistantError("Configura home_assistant.base_url y token en config.yaml")

    try:
        response = requests.get(f"{base_url}/api/states", headers=_headers(), timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HomeAssistantError(str(exc)) from exc

    configured = config.get("home_assistant", "entities", default=None)
    allowed_ids = None
    if configured:
        # Soporta el formato viejo (lista simple de entity_id como texto) y
        # el nuevo (lista de {entity_id, enabled}) agregado desde el panel web.
        allowed_ids = [
            item if isinstance(item, str) else item.get("entity_id")
            for item in configured
            if isinstance(item, str) or item.get("enabled", True)
        ]

    lights_by_id = {}
    for entity in response.json():
        entity_id = entity.get("entity_id", "")
        if allowed_ids is not None:
            if entity_id not in allowed_ids:
                continue
        elif not entity_id.startswith("light."):
            continue
        name = entity.get("attributes", {}).get("friendly_name", entity_id)
        lights_by_id[entity_id] = {"entity_id": entity_id, "name": name, "state": entity.get("state")}

    if allowed_ids is not None:
        return [lights_by_id[eid] for eid in allowed_ids if eid in lights_by_id]
    return list(lights_by_id.values())


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


def get_camera_snapshot(entity_id):
    base_url = _base_url()
    if not base_url or not _token() or "REEMPLAZA" in _token():
        raise HomeAssistantError("Configura home_assistant.base_url y token en config.yaml")

    try:
        response = requests.get(
            f"{base_url}/api/camera_proxy/{entity_id}",
            headers={"Authorization": f"Bearer {_token()}"},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        return response.content
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
