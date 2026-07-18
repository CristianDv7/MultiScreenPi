import pygame

from core import config
from core.screen_manager import Screen
from services import camera_service
from ui import theme
from ui.widgets.button import Button, back_button

LABEL_Y = 96
TABS_TOP = 140
TAP_MOVE_THRESHOLD = 12
MIN_ZOOM = 1.0
MAX_ZOOM = 4.0


class CamerasScreen(Screen):
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.cameras = config.get("cameras", default=[]) or []
        self.active_index = 0
        self.source = None
        self.buttons = []
        self.tab_buttons = []
        self.image_top = 200
        self.zoomed = False
        self._image_rect = None

        # cache del escalado "ajustado a pantalla" (sin zoom del usuario)
        self._fit_cache_key = None
        self._fit_cache_surface = None

        # estado del gesto de pellizcar/panoramica mientras esta en zoom
        self.zoom_scale = 1.0
        self.pan_offset = [0.0, 0.0]
        self._touches = {}
        self._pinch_distance = None
        self._pinch_scale_start = None
        self._pinch_mid = None
        self._pinch_pan_start = None
        self._single_start_pos = None
        self._single_moved = 0.0

    def on_enter(self):
        self.buttons = [back_button(24, 24, self._go_back)]
        self._reset_zoom()
        self._build_tabs()
        self._select(0)

    def on_exit(self):
        if self.source:
            self.source.stop()

    def _go_back(self):
        if self.source:
            self.source.stop()
        self.screen_manager.pop()

    def _reset_zoom(self):
        self.zoomed = False
        self.zoom_scale = 1.0
        self.pan_offset = [0.0, 0.0]
        self._touches = {}
        self._pinch_distance = None

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
            self._reset_zoom()
            self._select(index)

        return select

    def _select(self, index):
        if not self.cameras:
            return
        if self.source:
            self.source.stop()
        self.active_index = index
        self._fit_cache_key = None
        self._build_tabs()
        try:
            self.source = camera_service.create_source(self.cameras[index])
            self.source.start()
        except ValueError as exc:
            self.source = None
            self._error = str(exc)

    def on_tap(self, pos):
        if self.zoomed:
            return  # mientras esta en zoom, todo lo maneja on_touch_event

        for button in self.buttons + self.tab_buttons:
            if button.handle_tap(pos):
                return

        if self._image_rect and self._image_rect.collidepoint(pos) and self.source and self.source.surface:
            self.zoomed = True
            self.zoom_scale = 1.0
            self.pan_offset = [0.0, 0.0]

    def on_touch_event(self, kind, finger_id, pos):
        if not self.zoomed:
            return

        if kind == "down":
            self._touches[finger_id] = pos
            if len(self._touches) == 1:
                self._single_start_pos = pos
                self._single_moved = 0.0
            elif len(self._touches) == 2:
                points = list(self._touches.values())
                self._pinch_distance = _distance(points[0], points[1])
                self._pinch_scale_start = self.zoom_scale
                self._pinch_mid = _midpoint(points[0], points[1])
                self._pinch_pan_start = tuple(self.pan_offset)

        elif kind == "move":
            if finger_id not in self._touches:
                return
            prev = self._touches[finger_id]
            self._touches[finger_id] = pos

            if len(self._touches) >= 2:
                points = list(self._touches.values())[:2]
                distance = _distance(points[0], points[1])
                if self._pinch_distance:
                    factor = distance / self._pinch_distance
                    self.zoom_scale = max(MIN_ZOOM, min(MAX_ZOOM, self._pinch_scale_start * factor))
                mid = _midpoint(points[0], points[1])
                if self._pinch_mid:
                    dx = mid[0] - self._pinch_mid[0]
                    dy = mid[1] - self._pinch_mid[1]
                    self.pan_offset = [self._pinch_pan_start[0] + dx, self._pinch_pan_start[1] + dy]
            elif len(self._touches) == 1:
                dx = pos[0] - prev[0]
                dy = pos[1] - prev[1]
                self.pan_offset[0] += dx
                self.pan_offset[1] += dy
                self._single_moved += (dx**2 + dy**2) ** 0.5

        elif kind == "up":
            was_lone_tap = (
                len(self._touches) == 1 and finger_id in self._touches and self._single_moved < TAP_MOVE_THRESHOLD
            )
            self._touches.pop(finger_id, None)
            if len(self._touches) < 2:
                self._pinch_distance = None
            if was_lone_tap:
                self._reset_zoom()

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

        if self.zoomed and self.source and self.source.surface:
            self._draw_zoomed(surface, w, h)
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
        self._image_rect = image_area

        if self.source and self.source.error:
            text = f"Error: {self.source.error}"
            surface.blit(
                theme.FONT_SMALL.render(text, True, theme.TEXT_MUTED),
                (image_area.left + 20, image_area.top + 20),
            )
        elif self.source and self.source.surface:
            img = self._fitted_surface(image_area.size)
            surface.blit(img, img.get_rect(center=image_area.center))

            badge_text = "EN VIVO" if current.get("type") == "mjpeg" else "FOTO"
            badge_color = theme.DANGER if current.get("type") == "mjpeg" else theme.GRAY_NEUTRAL
            badge_surf = theme.FONT_SMALL.render(badge_text, True, (255, 255, 255))
            badge_rect = badge_surf.get_rect()
            badge_rect.topleft = (image_area.left + 16, image_area.top + 16)
            pygame.draw.rect(surface, badge_color, badge_rect.inflate(20, 12), border_radius=10)
            surface.blit(badge_surf, badge_rect)

            hint_surf = theme.FONT_SMALL.render("Toca la imagen para ampliar", True, theme.TEXT_MUTED)
            surface.blit(hint_surf, (image_area.left, image_area.bottom + 6))
        else:
            surface.blit(
                theme.FONT_BODY.render("Conectando...", True, theme.TEXT_MUTED),
                (image_area.left + 20, image_area.top + 20),
            )

    def _fitted_surface(self, size):
        """Escala el frame actual para que quepa en `size`, cacheado por version
        del frame para no recalcular el escalado en cada cuadro (30 veces/seg).
        """
        cache_key = (self.source.version, size)
        if self._fit_cache_key != cache_key:
            src = self.source.surface
            sw, sh = src.get_size()
            max_w, max_h = size
            scale = min(max_w / sw, max_h / sh)
            new_size = (max(1, int(sw * scale)), max(1, int(sh * scale)))
            self._fit_cache_surface = pygame.transform.smoothscale(src, new_size)
            self._fit_cache_key = cache_key
        return self._fit_cache_surface

    def _draw_zoomed(self, surface, w, h):
        base = self._fitted_surface((w, h))
        bw, bh = base.get_size()
        zw, zh = max(1, int(bw * self.zoom_scale)), max(1, int(bh * self.zoom_scale))

        if self.zoom_scale != 1.0:
            img = pygame.transform.smoothscale(base, (zw, zh))
        else:
            img = base

        # limita la panoramica para que la imagen no se aleje del todo de la pantalla
        max_pan_x = max(0, (zw - w) / 2 + w / 3)
        max_pan_y = max(0, (zh - h) / 2 + h / 3)
        self.pan_offset[0] = max(-max_pan_x, min(max_pan_x, self.pan_offset[0]))
        self.pan_offset[1] = max(-max_pan_y, min(max_pan_y, self.pan_offset[1]))

        center = (w // 2 + self.pan_offset[0], h // 2 + self.pan_offset[1])
        surface.blit(img, img.get_rect(center=center))

        hint_surf = theme.FONT_SMALL.render("Pellizca para zoom, arrastra para mover, toca para volver", True, (255, 255, 255))
        hint_rect = hint_surf.get_rect()
        hint_rect.bottomleft = (16, h - 16)
        pygame.draw.rect(surface, (0, 0, 0), hint_rect.inflate(20, 12), border_radius=10)
        surface.blit(hint_surf, hint_rect)


def _distance(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def _midpoint(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
