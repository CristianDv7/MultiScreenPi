import pygame

from core import config
from core.screen_manager import Screen
from services import camera_service
from ui import theme
from ui.widgets.button import Button


class CamerasScreen(Screen):
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.cameras = config.get("cameras", default=[]) or []
        self.active_index = 0
        self.source = None
        self.buttons = []
        self.tab_buttons = []
        self.image_top = 160

    def on_enter(self):
        self.buttons = [Button((24, 24, 100, 56), "< Volver", self._go_back)]
        self._build_tabs()
        self._select(0)

    def on_exit(self):
        if self.source:
            self.source.stop()

    def _go_back(self):
        if self.source:
            self.source.stop()
        self.screen_manager.pop()

    def _build_tabs(self):
        self.tab_buttons = []
        x, y = 24, 96
        row_height = 44
        max_right = 600 - 24

        for i, cam in enumerate(self.cameras):
            label = cam.get("name", f"Camara {i + 1}")
            width = min(220, max(90, len(label) * 11 + 24))
            if x + width > max_right and x > 24:
                x = 24
                y += row_height + 8
            self.tab_buttons.append(Button((x, y, width, row_height), label, self._make_selector(i)))
            x += width + 8

        self.image_top = y + row_height + 20

    def _make_selector(self, index):
        def select():
            self._select(index)

        return select

    def _select(self, index):
        if not self.cameras:
            return
        if self.source:
            self.source.stop()
        self.active_index = index
        try:
            self.source = camera_service.create_source(self.cameras[index])
            self.source.start()
        except ValueError as exc:
            self.source = None
            self._error = str(exc)

    def on_tap(self, pos):
        for button in self.buttons + self.tab_buttons:
            if button.handle_tap(pos):
                return

    def draw(self, surface):
        surface.fill(theme.BG)
        w, h = surface.get_size()

        for button in self.buttons:
            button.draw(surface)
        for button in self.tab_buttons:
            button.draw(surface)

        if not self.cameras:
            surface.blit(
                theme.FONT_BODY.render("Configura 'cameras' en config.yaml", True, theme.TEXT_MUTED), (24, 160)
            )
            return

        image_area = pygame.Rect(24, self.image_top, w - 48, h - self.image_top - 20)
        pygame.draw.rect(surface, theme.SURFACE, image_area, border_radius=16)

        if self.source and self.source.error:
            text = f"Error: {self.source.error}"
            surface.blit(
                theme.FONT_SMALL.render(text, True, theme.TEXT_MUTED),
                (image_area.left + 16, image_area.top + 16),
            )
        elif self.source and self.source.surface:
            img = self.source.surface
            surface.blit(img, img.get_rect(center=image_area.center))
        else:
            surface.blit(
                theme.FONT_BODY.render("Conectando...", True, theme.TEXT_MUTED),
                (image_area.left + 16, image_area.top + 16),
            )
