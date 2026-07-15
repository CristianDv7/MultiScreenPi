import threading

import pygame

from core import config
from core.screen_manager import Screen
from services import news_service
from ui import theme
from ui.widgets.button import Button

CARD_GAP = 14
PADDING = 16
TITLE_LINE_HEIGHT = 32
DESC_LINE_HEIGHT = 26
CHEVRON_SPACE = 34
MAX_IMAGE_WIDTH = 600 - 48 - PADDING * 2
MAX_IMAGE_HEIGHT = 260


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
        self._item_rects = []

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

        self.items = [
            {
                "title": item["title"],
                "description": item.get("description", ""),
                "image_url": item.get("image_url"),
                "expanded": False,
                "image_surface": None,
                "image_loading": False,
            }
            for item in items
        ]
        self.loading = False

    def on_tap(self, pos):
        for button in self.buttons + self.feed_buttons:
            if button.handle_tap(pos):
                return
        for rect, index in self._item_rects:
            if rect.collidepoint(pos):
                self._toggle_item(index)
                return

    def _toggle_item(self, index):
        item = self.items[index]
        item["expanded"] = not item["expanded"]
        if item["expanded"] and item["image_url"] and item["image_surface"] is None and not item["image_loading"]:
            item["image_loading"] = True
            threading.Thread(target=self._load_image_worker, args=(item,), daemon=True).start()

    def _load_image_worker(self, item):
        item["image_surface"] = news_service.load_image(item["image_url"], MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT)
        item["image_loading"] = False

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

        card_width = w - 48
        y = self.list_top - int(self.scroll)
        self._item_rects = []

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
            for index, item in enumerate(self.items):
                y = self._draw_card(surface, item, index, 24, y, card_width)
                y += CARD_GAP

        self.content_height = y + int(self.scroll) - self.list_top
        surface.set_clip(None)

    def _draw_card(self, surface, item, index, x, y, width):
        title_lines = _wrap_text(item["title"], theme.FONT_BODY, width - PADDING * 2 - CHEVRON_SPACE)
        card_top = y
        content_y = y + PADDING

        card_height = PADDING * 2 + len(title_lines) * TITLE_LINE_HEIGHT

        desc_lines = []
        if item["expanded"]:
            if item["image_loading"]:
                card_height += 30
            elif item["image_surface"] is not None:
                card_height += item["image_surface"].get_height() + 12
            if item["description"]:
                desc_lines = _wrap_text(item["description"], theme.FONT_SMALL, width - PADDING * 2)
                card_height += len(desc_lines) * DESC_LINE_HEIGHT + 8

        rect = pygame.Rect(x, card_top, width, card_height)
        pygame.draw.rect(surface, theme.SURFACE, rect, border_radius=14)
        self._item_rects.append((rect, index))

        line_y = content_y
        for line in title_lines:
            surface.blit(theme.FONT_BODY.render(line, True, theme.TEXT), (x + PADDING, line_y))
            line_y += TITLE_LINE_HEIGHT

        chevron = "-" if item["expanded"] else "+"
        chevron_surf = theme.FONT_BODY.render(chevron, True, theme.PRIMARY)
        surface.blit(chevron_surf, (x + width - PADDING - chevron_surf.get_width(), content_y))

        if item["expanded"]:
            if item["image_loading"]:
                surface.blit(
                    theme.FONT_SMALL.render("Cargando imagen...", True, theme.TEXT_MUTED), (x + PADDING, line_y)
                )
                line_y += 30
            elif item["image_surface"] is not None:
                surface.blit(item["image_surface"], (x + PADDING, line_y))
                line_y += item["image_surface"].get_height() + 12

            for line in desc_lines:
                surface.blit(theme.FONT_SMALL.render(line, True, theme.TEXT_MUTED), (x + PADDING, line_y))
                line_y += DESC_LINE_HEIGHT

        return card_top + card_height


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
