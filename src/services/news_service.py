import io
import re
import xml.etree.ElementTree as ET

import pygame
import requests

TIMEOUT = 10
ATOM_NS = "{http://www.w3.org/2005/Atom}"
MEDIA_NS = "{http://search.yahoo.com/mrss/}"
IMG_SRC_RE = re.compile(r'<img[^>]+src="([^"]+)"')


class NewsFetchError(Exception):
    pass


def fetch_items(feed_url, limit=12):
    if not feed_url:
        raise NewsFetchError("Este feed no tiene URL configurada")

    try:
        response = requests.get(feed_url, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise NewsFetchError(str(exc)) from exc

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as exc:
        raise NewsFetchError(f"Feed invalido: {exc}") from exc

    items = root.findall(".//item")
    tag = "item"
    if not items:
        items = root.findall(f".//{ATOM_NS}entry")
        tag = "atom"

    results = []
    for item in items[:limit]:
        if tag == "item":
            title_el = item.find("title")
        else:
            title_el = item.find(f"{ATOM_NS}title")
        title = (title_el.text or "").strip() if title_el is not None else "(sin titulo)"
        results.append({"title": title, "image_url": _extract_image(item, tag)})

    return results


def _extract_image(item, tag):
    if tag != "item":
        return None

    enclosure = item.find("enclosure")
    if enclosure is not None and "image" in (enclosure.get("type") or ""):
        return enclosure.get("url")

    media_content = item.find(f"{MEDIA_NS}content")
    if media_content is not None and media_content.get("url"):
        return media_content.get("url")

    media_thumb = item.find(f"{MEDIA_NS}thumbnail")
    if media_thumb is not None and media_thumb.get("url"):
        return media_thumb.get("url")

    description = item.find("description")
    if description is not None and description.text:
        match = IMG_SRC_RE.search(description.text)
        if match:
            return match.group(1)

    return None


def load_thumbnail(url, size):
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        image = pygame.image.load(io.BytesIO(response.content))
        image = image.convert()
        return pygame.transform.smoothscale(image, size)
    except (requests.RequestException, pygame.error, OSError):
        return None
