import requests

from core import config

TIMEOUT = 5


class PCControlError(Exception):
    pass


def _base_url():
    return (config.get("pc_control", "base_url", default="") or "").rstrip("/")


def _token():
    return config.get("pc_control", "token", default="") or ""


def get_shortcuts():
    return config.get("pc_control", "shortcuts", default=[]) or []


def _headers():
    return {"Authorization": f"Bearer {_token()}"}


def trigger(shortcut):
    base_url = _base_url()
    if not base_url:
        raise PCControlError("Configura pc_control.base_url en config.yaml")

    is_url = shortcut.get("type") == "url"
    endpoint = "/open-url" if is_url else "/launch"
    payload = {"url": shortcut.get("target")} if is_url else {"app": shortcut.get("target")}

    try:
        response = requests.post(f"{base_url}{endpoint}", json=payload, headers=_headers(), timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise PCControlError(str(exc)) from exc


def get_audio_devices():
    base_url = _base_url()
    if not base_url:
        raise PCControlError("Configura pc_control.base_url en config.yaml")

    try:
        response = requests.get(f"{base_url}/audio-devices", headers=_headers(), timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise PCControlError(str(exc)) from exc


def set_audio_device(name):
    base_url = _base_url()
    if not base_url:
        raise PCControlError("Configura pc_control.base_url en config.yaml")

    try:
        response = requests.post(
            f"{base_url}/set-audio-device", json={"name": name}, headers=_headers(), timeout=TIMEOUT
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise PCControlError(str(exc)) from exc


def switch_desktop(direction):
    base_url = _base_url()
    if not base_url:
        raise PCControlError("Configura pc_control.base_url en config.yaml")

    try:
        response = requests.post(
            f"{base_url}/switch-desktop", json={"direction": direction}, headers=_headers(), timeout=TIMEOUT
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise PCControlError(str(exc)) from exc
