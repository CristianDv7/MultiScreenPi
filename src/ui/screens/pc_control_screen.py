import threading

import pygame

from core.screen_manager import Screen
from services import pc_control_service, voice_service
from ui import theme
from ui.widgets.button import Button

CARD_HEIGHT = 76
CARD_GAP = 14
COLUMN_GAP = 16
LIST_TOP = 100

DESKTOPS = [
    {"name": "Escritorio 1", "direction": "left"},
    {"name": "Escritorio 2", "direction": "right"},
]


class PCControlScreen(Screen):
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.shortcuts = []
        self.status = None
        self.scroll = 0.0
        self.content_height = 0
        self.buttons = []
        self._item_rects = []

        self.audio_devices = []
        self.audio_current = None
        self.audio_loading = False
        self.audio_error = None

    def on_enter(self):
        self.shortcuts = pc_control_service.get_shortcuts()
        self.status = None
        self.scroll = 0.0
        self.buttons = [Button((24, 24, 100, 56), "< Volver", self.screen_manager.pop)]
        self._load_audio_devices()

    def _load_audio_devices(self):
        if self.audio_loading:
            return
        self.audio_loading = True
        self.audio_error = None
        threading.Thread(target=self._load_audio_worker, daemon=True).start()

    def _load_audio_worker(self):
        try:
            data = pc_control_service.get_audio_devices()
            self.audio_devices = data.get("devices", [])
            self.audio_current = data.get("current")
        except pc_control_service.PCControlError as exc:
            self.audio_error = str(exc)
        finally:
            self.audio_loading = False

    def _switch_audio(self, name):
        threading.Thread(target=self._switch_audio_worker, args=(name,), daemon=True).start()

    def _switch_audio_worker(self, name):
        try:
            pc_control_service.set_audio_device(name)
            self.audio_current = name
            self.status = f"Audio: {name}"
        except pc_control_service.PCControlError as exc:
            self.status = f"Error: {exc}"

    def _switch_desktop(self, desktop):
        threading.Thread(target=self._switch_desktop_worker, args=(desktop,), daemon=True).start()

    def _switch_desktop_worker(self, desktop):
        try:
            pc_control_service.switch_desktop(desktop["direction"])
            self.status = f"{desktop['name']}: activado"
        except pc_control_service.PCControlError as exc:
            self.status = f"Error: {exc}"

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
        for rect, kind, value in self._item_rects:
            if rect.collidepoint(pos):
                if kind == "shortcut":
                    self._trigger(value)
                elif kind == "audio":
                    self._switch_audio(value)
                elif kind == "desktop":
                    self._switch_desktop(value)
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

        y = self._draw_section_label(surface, "Escritorios", y)
        y = self._draw_grid(
            surface,
            card_width,
            y,
            DESKTOPS,
            lambda rect, item: self._draw_desktop_card(surface, rect, item),
        )
        y += 20

        y = self._draw_section_label(surface, "Salida de audio", y)
        y = self._draw_audio_section(surface, y, card_width)
        y += 20

        y = self._draw_section_label(surface, "Atajos", y)
        y = self._draw_shortcuts_section(surface, y, card_width)

        if self.status:
            for line in _wrap(self.status, theme.FONT_SMALL, card_width):
                surface.blit(theme.FONT_SMALL.render(line, True, theme.TEXT_MUTED), (24, y))
                y += 24

        self.content_height = y + int(self.scroll) - LIST_TOP
        surface.set_clip(None)

    def _draw_section_label(self, surface, text, y):
        surface.blit(theme.FONT_BODY.render(text, True, theme.TEXT), (24, y))
        return y + 40

    def _draw_grid(self, surface, card_width, top, items, render_fn):
        column_width = (card_width - COLUMN_GAP) / 2
        for i, item in enumerate(items):
            col = i % 2
            row = i // 2
            x = 24 + col * (column_width + COLUMN_GAP)
            y = top + row * (CARD_HEIGHT + CARD_GAP)
            rect = pygame.Rect(int(x), int(y), int(column_width), CARD_HEIGHT)
            render_fn(rect, item)

        rows = (len(items) + 1) // 2
        return top + rows * (CARD_HEIGHT + CARD_GAP)

    def _draw_desktop_card(self, surface, rect, desktop):
        pygame.draw.rect(surface, theme.SURFACE, rect, border_radius=16)
        bar_rect = pygame.Rect(rect.left, rect.top, 6, rect.height)
        pygame.draw.rect(surface, theme.GOLD, bar_rect, border_top_left_radius=16, border_bottom_left_radius=16)

        name_surf = theme.FONT_BODY.render(desktop["name"], True, theme.TEXT)
        surface.blit(name_surf, name_surf.get_rect(center=rect.center))

        self._item_rects.append((rect, "desktop", desktop))

    def _draw_audio_section(self, surface, y, card_width):
        if self.audio_loading and not self.audio_devices:
            surface.blit(theme.FONT_SMALL.render("Cargando dispositivos...", True, theme.TEXT_MUTED), (24, y))
            return y + 34

        if self.audio_error:
            for line in _wrap(f"Error: {self.audio_error}", theme.FONT_SMALL, card_width):
                surface.blit(theme.FONT_SMALL.render(line, True, theme.TEXT_MUTED), (24, y))
                y += 24
            return y

        def render(rect, device):
            is_current = device == self.audio_current
            pygame.draw.rect(surface, theme.SURFACE, rect, border_radius=16)
            bar_color = theme.GREEN if is_current else theme.TEXT_MUTED
            bar_rect = pygame.Rect(rect.left, rect.top, 6, rect.height)
            pygame.draw.rect(surface, bar_color, bar_rect, border_top_left_radius=16, border_bottom_left_radius=16)

            name_surf = theme.FONT_SMALL.render(device, True, theme.TEXT)
            clip = surface.get_clip()
            surface.set_clip(rect.inflate(-16, 0))
            surface.blit(name_surf, name_surf.get_rect(midleft=(rect.left + 16, rect.centery)))
            surface.set_clip(clip)

            self._item_rects.append((rect, "audio", device))

        return self._draw_grid(surface, card_width, y, self.audio_devices, render)

    def _draw_shortcuts_section(self, surface, y, card_width):
        if not self.shortcuts:
            surface.blit(
                theme.FONT_SMALL.render("Configura pc_control.shortcuts en config.yaml", True, theme.TEXT_MUTED),
                (24, y),
            )
            return y + 34

        def render(rect, entry):
            index, shortcut = entry
            pygame.draw.rect(surface, theme.SURFACE, rect, border_radius=16)
            bar_rect = pygame.Rect(rect.left, rect.top, 6, rect.height)
            pygame.draw.rect(
                surface, theme.LAVENDER, bar_rect, border_top_left_radius=16, border_bottom_left_radius=16
            )

            name_surf = theme.FONT_SMALL.render(shortcut.get("name", "?"), True, theme.TEXT)
            clip = surface.get_clip()
            surface.set_clip(rect.inflate(-16, 0))
            surface.blit(name_surf, name_surf.get_rect(midleft=(rect.left + 16, rect.centery)))
            surface.set_clip(clip)

            self._item_rects.append((rect, "shortcut", index))

        return self._draw_grid(surface, card_width, y, list(enumerate(self.shortcuts)), render)


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
