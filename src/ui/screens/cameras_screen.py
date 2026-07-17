import pygame

from core import config
from core.screen_manager import Screen
from services import camera_service
from ui import theme
from ui.widgets.button import Button, back_button

LABEL_Y = 96
TABS_TOP = 140


class CamerasScreen(Screen):
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.cameras = config.get("cameras", default=[]) or []
        self.active_index = 0
        self.source = None
        self.buttons = []
        self.tab_buttons = []
        self.image_top = 200

    def on_enter(self):
        self.buttons = [back_button(24, 24, self._go_back)]
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
        x, y = 24, TABS_TOP
        row_height = 46
        max_right = 600 - 24

        for i, cam in enumerate(self.cameras):
            label = cam.get("name", f"Camara {i + 1}")
            width = min(220, max(90, len(label) * 12 + 28))
            if x + width > max_right and x > 24:
                x = 24
                y += row_height + 10
            is_active = i == self.active_index
            self.tab_buttons.append(
                Button(
                    (x, y, width, row_height),
                    label,
                    self._make_selector(i),
                    bg=theme.INDIGO if is_active else theme.SURFACE,
                    text_color=(255, 255, 255) if is_active else theme.TEXT,
                    font=theme.FONT_SMALL,
                    centered=True,
                )
            )
            x += width + 10

        self.image_top = y + row_height + 24

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
        self._build_tabs()
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

        if not self.cameras:
            for button in self.buttons:
                button.draw(surface)
            surface.blit(
                theme.FONT_BODY.render("Configura 'cameras' en config.yaml", True, theme.TEXT_MUTED), (24, 160)
            )
            return

        current = self.cameras[self.active_index]
        name = current.get("name", f"Camara {self.active_index + 1}")

        label_surf = theme.FONT_TITLE.render(f"Viendo: {name}", True, theme.TEXT)
        surface.blit(label_surf, (24, LABEL_Y))

        for button in self.buttons:
            button.draw(surface)
        for button in self.tab_buttons:
            button.draw(surface)

        image_area = pygame.Rect(24, self.image_top, w - 48, h - self.image_top - 20)
        pygame.draw.rect(surface, theme.SURFACE, image_area, border_radius=20)
        pygame.draw.rect(surface, theme.GOLD, image_area, width=3, border_radius=20)

        if self.source and self.source.error:
            text = f"Error: {self.source.error}"
            surface.blit(
                theme.FONT_SMALL.render(text, True, theme.TEXT_MUTED),
                (image_area.left + 20, image_area.top + 20),
            )
        elif self.source and self.source.surface:
            img = self.source.surface
            surface.blit(img, img.get_rect(center=image_area.center))

            badge_text = "EN VIVO" if current.get("type") == "mjpeg" else "FOTO"
            badge_color = theme.DANGER if current.get("type") == "mjpeg" else theme.GRAY_NEUTRAL
            badge_surf = theme.FONT_SMALL.render(badge_text, True, (255, 255, 255))
            badge_rect = badge_surf.get_rect()
            badge_rect.topleft = (image_area.left + 16, image_area.top + 16)
            pygame.draw.rect(surface, badge_color, badge_rect.inflate(20, 12), border_radius=10)
            surface.blit(badge_surf, badge_rect)
        else:
            surface.blit(
                theme.FONT_BODY.render("Conectando...", True, theme.TEXT_MUTED),
                (image_area.left + 20, image_area.top + 20),
            )
