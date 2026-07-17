import threading

import pygame

from core.screen_manager import Screen
from services import home_assistant_service as ha
from ui import theme
from ui.widgets.button import Button, back_button

CARD_HEIGHT = 84
CARD_GAP = 16
LIST_TOP = 100

TOGGLE_WIDTH = 64
TOGGLE_HEIGHT = 34
THUMB_MARGIN = 4


class HomeAssistantScreen(Screen):
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.lights = []
        self.error = None
        self.loading = False
        self.scroll = 0.0
        self.content_height = 0
        self.buttons = []
        self._item_rects = []

    def on_enter(self):
        self.buttons = [
            back_button(24, 24, self.screen_manager.pop),
            Button((600 - 24 - 150, 24, 150, 56), "Actualizar", self._load),
        ]
        self._load()

    def _load(self):
        if self.loading:
            return
        self.loading = True
        self.error = None
        threading.Thread(target=self._load_worker, daemon=True).start()

    def _load_worker(self):
        try:
            self.lights = ha.list_lights()
        except ha.HomeAssistantError as exc:
            self.error = str(exc)
        finally:
            self.loading = False

    def _toggle(self, index):
        light = self.lights[index]
        turn_on = light["state"] != "on"
        light["state"] = "on" if turn_on else "off"
        threading.Thread(
            target=self._toggle_worker, args=(light["entity_id"], turn_on, index), daemon=True
        ).start()

    def _toggle_worker(self, entity_id, turn_on, index):
        try:
            ha.set_light(entity_id, turn_on)
        except ha.HomeAssistantError as exc:
            self.error = str(exc)
            if index < len(self.lights):
                self.lights[index]["state"] = "off" if turn_on else "on"

    def on_tap(self, pos):
        for button in self.buttons:
            if button.handle_tap(pos):
                return
        for rect, index in self._item_rects:
            if rect.collidepoint(pos):
                self._toggle(index)
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

        if self.loading and not self.lights:
            surface.blit(theme.FONT_BODY.render("Cargando...", True, theme.TEXT_MUTED), (24, y))
        elif self.error:
            for line in _wrap(f"Error: {self.error}", theme.FONT_SMALL, w - 48):
                surface.blit(theme.FONT_SMALL.render(line, True, theme.TEXT_MUTED), (24, y))
                y += 24
        elif not self.lights:
            surface.blit(theme.FONT_BODY.render("No se encontraron luces.", True, theme.TEXT_MUTED), (24, y))
        else:
            for index, light in enumerate(self.lights):
                rect = pygame.Rect(24, y, card_width, CARD_HEIGHT)
                is_on = light["state"] == "on"

                pygame.draw.rect(surface, theme.SURFACE, rect, border_radius=20)
                bar_color = theme.GREEN if is_on else theme.TEXT_MUTED
                bar_rect = pygame.Rect(rect.left, rect.top, 6, rect.height)
                pygame.draw.rect(
                    surface, bar_color, bar_rect, border_top_left_radius=20, border_bottom_left_radius=20
                )

                name_surf = theme.FONT_BODY.render(light["name"], True, theme.TEXT)
                clip = surface.get_clip()
                text_clip = pygame.Rect(rect.left, rect.top, rect.width - 120, rect.height)
                surface.set_clip(text_clip)
                surface.blit(name_surf, name_surf.get_rect(midleft=(rect.left + 28, rect.centery)))
                surface.set_clip(clip)

                self._draw_toggle(surface, rect, is_on)

                self._item_rects.append((rect, index))
                y += CARD_HEIGHT + CARD_GAP

        self.content_height = y + int(self.scroll) - LIST_TOP
        surface.set_clip(None)

    def _draw_toggle(self, surface, card_rect, is_on):
        track = pygame.Rect(0, 0, TOGGLE_WIDTH, TOGGLE_HEIGHT)
        track.midright = (card_rect.right - 24, card_rect.centery)

        track_color = theme.GREEN if is_on else theme.GRAY_NEUTRAL
        pygame.draw.rect(surface, track_color, track, border_radius=TOGGLE_HEIGHT // 2)

        thumb_radius = TOGGLE_HEIGHT // 2 - THUMB_MARGIN
        thumb_x = track.right - thumb_radius - THUMB_MARGIN if is_on else track.left + thumb_radius + THUMB_MARGIN
        pygame.draw.circle(surface, theme.BG, (thumb_x, track.centery), thumb_radius)


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
