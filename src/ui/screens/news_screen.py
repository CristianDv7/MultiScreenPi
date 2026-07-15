import threading

import pygame

from core import config
from core.screen_manager import Screen
from services import news_service
from ui import theme
from ui.widgets.button import Button

THUMB_SIZE = (100, 70)
MAX_IMAGES = 6
CARD_GAP = 20


class NewsScreen(Screen):
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.feeds = config.get("news", "feeds", default=[]) or []
        self.active_index = 0
        self.items = []
        self.error = None
        self.loading = False
        self.scroll = 0.0
        self.content_height = 0
        self.list_top = 160
        self.buttons = []
        self.feed_buttons = []

    def on_enter(self):
        self.buttons = [
            Button((24, 24, 130, 56), "< Volver", self.screen_manager.pop),
            Button((600 - 24 - 150, 24, 150, 56), "Actualizar", self._load_active_feed),
        ]
        self._build_feed_buttons()
        self._load_active_feed()

    def _build_feed_buttons(self):
        self.feed_buttons = []
        x, y = 24, 96
        row_height = 44
        max_right = 600 - 24

        for i, feed in enumerate(self.feeds):
            label = feed.get("name", f"Feed {i + 1}")
            width = min(220, max(90, len(label) * 11 + 24))
            if x + width > max_right and x > 24:
                x = 24
                y += row_height + 8
            self.feed_buttons.append(Button((x, y, width, row_height), label, self._make_selector(i)))
            x += width + 8

        self.list_top = y + row_height + 20

    def _make_selector(self, index):
        def select():
            if index != self.active_index and not self.loading:
                self.active_index = index
                self.scroll = 0.0
                self._load_active_feed()

        return select

    def _load_active_feed(self):
        if self.loading or not self.feeds:
            return
        self.loading = True
        self.error = None
        self.items = []
        feed_url = self.feeds[self.active_index].get("url")
        threading.Thread(target=self._fetch_worker, args=(feed_url,), daemon=True).start()

    def _fetch_worker(self, feed_url):
        try:
            items = news_service.fetch_items(feed_url, limit=12)
        except news_service.NewsFetchError as exc:
            self.error = str(exc)
            self.loading = False
            return

        self.items = [dict(item, image_surface=None) for item in items]
        self.loading = False

        for entry in self.items[:MAX_IMAGES]:
            url = entry.get("image_url")
            if url:
                entry["image_surface"] = news_service.load_thumbnail(url, THUMB_SIZE)

    def on_tap(self, pos):
        for button in self.buttons + self.feed_buttons:
            if button.handle_tap(pos):
                return

    def on_scroll(self, dy):
        viewport = 1024 - self.list_top - 20
        max_scroll = max(0, self.content_height - viewport)
        self.scroll = min(max_scroll, max(0, self.scroll - dy))

    def draw(self, surface):
        surface.fill(theme.BG)
        w, h = surface.get_size()

        for button in self.buttons:
            button.draw(surface)
        for button in self.feed_buttons:
            button.draw(surface)

        viewport_height = h - self.list_top - 20
        clip_rect = pygame.Rect(0, self.list_top, w, viewport_height)
        surface.set_clip(clip_rect)

        y = self.list_top - int(self.scroll)

        if not self.feeds:
            surface.blit(theme.FONT_BODY.render("Configura news.feeds", True, theme.TEXT_MUTED), (24, y))
        elif self.loading and not self.items:
            surface.blit(theme.FONT_BODY.render("Cargando...", True, theme.TEXT_MUTED), (24, y))
        elif self.error:
            for line in _wrap_text(f"Error: {self.error}", theme.FONT_SMALL, w - 48):
                surface.blit(theme.FONT_SMALL.render(line, True, theme.TEXT_MUTED), (24, y))
                y += 22
        elif not self.items:
            surface.blit(theme.FONT_BODY.render("Sin titulares.", True, theme.TEXT_MUTED), (24, y))
        else:
            for item in self.items:
                thumb = item.get("image_surface")
                text_x = 24
                if thumb:
                    surface.blit(thumb, (24, y))
                    text_x = 24 + THUMB_SIZE[0] + 12

                line_y = y
                for line in _wrap_text(item["title"], theme.FONT_SMALL, w - text_x - 24):
                    surface.blit(theme.FONT_SMALL.render(line, True, theme.TEXT), (text_x, line_y))
                    line_y += 22

                card_height = max(THUMB_SIZE[1] if thumb else 0, line_y - y)
                y += card_height + CARD_GAP

        self.content_height = y + int(self.scroll) - self.list_top
        surface.set_clip(None)


def _wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines
