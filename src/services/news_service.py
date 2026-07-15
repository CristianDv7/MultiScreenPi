import xml.etree.ElementTree as ET

import requests

from core import config

TIMEOUT = 10
ATOM_NS = "{http://www.w3.org/2005/Atom}"


class NewsFetchError(Exception):
    pass


def fetch_headlines(limit=10):
    feed_url = config.get("news", "feed_url")
    if not feed_url or feed_url.startswith("https://example.com"):
        raise NewsFetchError("Configura 'news.feed_url' en config.yaml")

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
    title_tag = "title"
    if not items:
        items = root.findall(f".//{ATOM_NS}entry")
        title_tag = f"{ATOM_NS}title"

    headlines = []
    for item in items[:limit]:
        title_el = item.find(title_tag)
        title = (title_el.text or "").strip() if title_el is not None else "(sin titulo)"
        headlines.append(title)

    return headlines
