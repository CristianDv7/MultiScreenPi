import threading

import pygame

from core.screen_manager import Screen
from services import social_service
from ui import theme
from ui.widgets.button import Button

CARD_HEIGHT = 140
CARD_GAP = 20
LIST_TOP = 110

PLATFORMS = [
    ("YouTube", theme.YOUTUBE_RED, social_service.fetch_youtube_subscribers),
    ("Facebook", theme.FACEBOOK_BLUE, social_service.fetch_facebook_followers),
    ("Instagram", theme.INSTAGRAM_PINK, social_service.fetch_instagram_followers),
]


class SocialScreen(Screen):
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.counts = {}
        self.errors = {}
        self.loading = False
        self.buttons = []

    def on_enter(self):
        self.buttons = [
            Button((24, 24, 100, 56), "< Volver", self.screen_manager.pop),
            Button((600 - 24 - 150, 24, 150, 56), "Actualizar", self._load),
        ]
        self._load()

    def _load(self):
        if self.loading:
            return
        self.loading = True
        self.counts = {}
        self.errors = {}
        for name, _color, fetch_fn in PLATFORMS:
            threading.Thread(target=self._load_one, args=(name, fetch_fn), daemon=True).start()

    def _load_one(self, name, fetch_fn):
        try:
            self.counts[name] = fetch_fn()
        except social_service.SocialError as exc:
            self.errors[name] = str(exc)
        finally:
            if len(self.counts) + len(self.errors) >= len(PLATFORMS):
                self.loading = False

    def on_tap(self, pos):
        for button in self.buttons:
            if button.handle_tap(pos):
                return

    def draw(self, surface):
        surface.fill(theme.BG)
        w = surface.get_width()

        for button in self.buttons:
            button.draw(surface)

        y = LIST_TOP
        for name, color, _fetch_fn in PLATFORMS:
            rect = pygame.Rect(24, y, w - 48, CARD_HEIGHT)
            pygame.draw.rect(surface, theme.SURFACE, rect, border_radius=24)
            pygame.draw.rect(surface, color, rect, width=4, border_radius=24)

            name_surf = theme.FONT_BODY.render(name, True, theme.TEXT)
            surface.blit(name_surf, (rect.left + 24, rect.top + 20))

            if name in self.errors:
                for i, line in enumerate(_wrap(f"Error: {self.errors[name]}", theme.FONT_SMALL, rect.width - 48)):
                    surface.blit(
                        theme.FONT_SMALL.render(line, True, theme.TEXT_MUTED),
                        (rect.left + 24, rect.top + 60 + i * 22),
                    )
            elif name in self.counts:
                count_surf = theme.FONT_TIMER.render(_format_count(self.counts[name]), True, color)
                surface.blit(count_surf, (rect.left + 24, rect.top + 55))
            else:
                surface.blit(
                    theme.FONT_BODY.render("Cargando...", True, theme.TEXT_MUTED), (rect.left + 24, rect.top + 60)
                )

            y += CARD_HEIGHT + CARD_GAP


def _format_count(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M".replace(".0M", "M")
    if n >= 1000:
        return f"{n / 1000:.1f}k".replace(".0k", "k")
    return str(n)


def _wrap(text, font, max_width):
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
