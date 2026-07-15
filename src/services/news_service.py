import html
import io
import re
import xml.etree.ElementTree as ET

import pygame
import requests

TIMEOUT = 10
# Varios sitios rechazan peticiones sin un User-Agent de navegador (400/403).
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MultiScreenPi/1.0)"}
ATOM_NS = "{http://www.w3.org/2005/Atom}"
MEDIA_NS = "{http://search.yahoo.com/mrss/}"
CONTENT_NS = "{http://purl.org/rss/1.0/modules/content/}"
IMG_SRC_RE = re.compile(r'<img[^>]+src="([^"]+)"')
TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


class NewsFetchError(Exception):
    pass


def fetch_items(feed_url, limit=12):
    if not feed_url:
        raise NewsFetchError("Este feed no tiene URL configurada")

    try:
        response = requests.get(feed_url, headers=HEADERS, timeout=TIMEOUT)
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
            desc_el = item.find("description")
        else:
            title_el = item.find(f"{ATOM_NS}title")
            desc_el = item.find(f"{ATOM_NS}summary")

        title = (title_el.text or "").strip() if title_el is not None else "(sin titulo)"

        # Solo el resumen corto (description/summary), no el cuerpo completo del articulo.
        desc_text = desc_el.text if desc_el is not None and desc_el.text else ""
        description = _clean_html(desc_text) if desc_text else ""

        results.append(
            {
                "title": title,
                "description": description,
                "image_url": _extract_image(item, tag),
            }
        )

    return results


def _clean_html(raw):
    text = TAG_RE.sub(" ", raw)
    text = html.unescape(text)
    return WHITESPACE_RE.sub(" ", text).strip()


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

    for tag_name in ("description", f"{CONTENT_NS}encoded"):
        el = item.find(tag_name)
        if el is not None and el.text:
            match = IMG_SRC_RE.search(el.text)
            if match:
                return match.group(1)

    return None


def load_image(url, max_width, max_height=None):
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        image = pygame.image.load(io.BytesIO(response.content)).convert()
    except (requests.RequestException, pygame.error, OSError):
        return None

    w, h = image.get_size()
    scale = max_width / w if w > max_width else 1
    if max_height is not None:
        scale = min(scale, max_height / h if h > max_height else 1)
    if scale < 1:
        image = pygame.transform.smoothscale(image, (max(1, int(w * scale)), max(1, int(h * scale))))
    return image
