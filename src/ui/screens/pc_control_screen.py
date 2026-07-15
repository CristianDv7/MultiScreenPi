import threading

import pygame

from core.screen_manager import Screen
from services import pc_control_service, voice_service
from ui import theme
from ui.widgets.button import Button

CARD_HEIGHT = 76
CARD_GAP = 14
LIST_TOP = 100


class PCControlScreen(Screen):
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.shortcuts = []
        self.status = None
        self.scroll = 0.0
        self.content_height = 0
        self.buttons = []
        self._item_rects = []

    def on_enter(self):
        self.shortcuts = pc_control_service.get_shortcuts()
        self.status = None
        self.scroll = 0.0
        self.buttons = [Button((24, 24, 100, 56), "< Volver", self.screen_manager.pop)]

    def _trigger(self, index):
        shortcut = self.shortcuts[index]
        self.status = f"Abriendo {shortcut.get('name')}..."
        threading.Thread(target=self._trigger_worker, args=(shortcut,), daemon=True).start()

    def _trigger_worker(self, shortcut):
        name = shortcut.get("name", "?")
        try:
            voice_service.speak(f"Abriendo {name}")
        except voice_service.VoiceError:
            pass

        try:
            pc_control_service.trigger(shortcut)
            self.status = f"{name}: abierto"
        except pc_control_service.PCControlError as exc:
            self.status = f"Error: {exc}"

    def on_tap(self, pos):
        for button in self.buttons:
            if button.handle_tap(pos):
                return
        for rect, index in self._item_rects:
            if rect.collidepoint(pos):
                self._trigger(index)
                return

    def on_scroll(self, dy):
        viewport = 1024 - LIST_TOP - 20
        max_scroll = max(0, self.content_height - viewport)
        self.scroll = min(max_scroll, max(0, self.scroll - dy))

    def draw(self, surface):
        surface.fill(theme.BG)
        w, h = surface.get_size()

        for button in self.buttons:
            button.draw(surface)

        viewport_height = h - LIST_TOP - 20
        clip_rect = pygame.Rect(0, LIST_TOP, w, viewport_height)
        surface.set_clip(clip_rect)

        y = LIST_TOP - int(self.scroll)
        self._item_rects = []
        card_width = w - 48

        if not self.shortcuts:
            surface.blit(
                theme.FONT_BODY.render("Configura pc_control.shortcuts en config.yaml", True, theme.TEXT_MUTED),
                (24, y),
            )
        else:
            for index, shortcut in enumerate(self.shortcuts):
                rect = pygame.Rect(24, y, card_width, CARD_HEIGHT)
                pygame.draw.rect(surface, theme.SURFACE, rect, border_radius=16)
                bar_rect = pygame.Rect(rect.left, rect.top, 6, rect.height)
                pygame.draw.rect(
                    surface, theme.LAVENDER, bar_rect, border_top_left_radius=16, border_bottom_left_radius=16
                )

                name_surf = theme.FONT_BODY.render(shortcut.get("name", "?"), True, theme.TEXT)
                surface.blit(name_surf, name_surf.get_rect(midleft=(rect.left + 30, rect.centery)))

                kind_surf = theme.FONT_SMALL.render(
                    "Sitio web" if shortcut.get("type") == "url" else "App", True, theme.TEXT_MUTED
                )
                surface.blit(kind_surf, kind_surf.get_rect(midright=(rect.right - 24, rect.centery)))

                self._item_rects.append((rect, index))
                y += CARD_HEIGHT + CARD_GAP

            if self.status:
                for line in _wrap(self.status, theme.FONT_SMALL, w - 48):
                    surface.blit(theme.FONT_SMALL.render(line, True, theme.TEXT_MUTED), (24, y))
                    y += 24

        self.content_height = y + int(self.scroll) - LIST_TOP
        surface.set_clip(None)


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
