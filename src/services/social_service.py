import requests

from core import config

TIMEOUT = 8
GRAPH_API = "https://graph.facebook.com/v19.0"


class SocialError(Exception):
    pass


def fetch_youtube_subscribers():
    api_key = config.get("social", "youtube", "api_key", default="")
    channel_id = config.get("social", "youtube", "channel_id", default="")

    if not api_key or "REEMPLAZA" in api_key:
        raise SocialError("Configura social.youtube.api_key en config.yaml")
    if not channel_id:
        raise SocialError("Configura social.youtube.channel_id en config.yaml")

    try:
        response = requests.get(
            "https://www.googleapis.com/youtube/v3/channels",
            params={"part": "statistics", "id": channel_id, "key": api_key},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise SocialError(str(exc)) from exc

    items = data.get("items", [])
    if not items:
        raise SocialError("No se encontro el canal (revisa channel_id)")
    return int(items[0]["statistics"]["subscriberCount"])


def fetch_facebook_followers():
    page_id = config.get("social", "facebook", "page_id", default="")
    token = config.get("social", "facebook", "access_token", default="")

    if not page_id or not token or "REEMPLAZA" in token:
        raise SocialError("Configura social.facebook.page_id y access_token en config.yaml")

    try:
        response = requests.get(
            f"{GRAPH_API}/{page_id}",
            params={"fields": "followers_count", "access_token": token},
            timeout=TIMEOUT,
        )
        data = response.json()
    except requests.RequestException as exc:
        raise SocialError(str(exc)) from exc

    if "followers_count" not in data:
        raise SocialError(data.get("error", {}).get("message", "Respuesta inesperada de Facebook"))
    return data["followers_count"]


def fetch_instagram_followers():
    ig_id = config.get("social", "instagram", "business_account_id", default="")
    # Reutiliza el token de Facebook si no se configura uno especifico: es el
    # mismo Page Access Token el que se usa para consultar Instagram Graph API.
    token = config.get("social", "instagram", "access_token", default="") or config.get(
        "social", "facebook", "access_token", default=""
    )

    if not ig_id or not token or "REEMPLAZA" in token:
        raise SocialError("Configura social.instagram.business_account_id (y access_token) en config.yaml")

    try:
        response = requests.get(
            f"{GRAPH_API}/{ig_id}",
            params={"fields": "followers_count", "access_token": token},
            timeout=TIMEOUT,
        )
        data = response.json()
    except requests.RequestException as exc:
        raise SocialError(str(exc)) from exc

    if "followers_count" not in data:
        raise SocialError(data.get("error", {}).get("message", "Respuesta inesperada de Instagram"))
    return data["followers_count"]
