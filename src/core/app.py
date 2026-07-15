import threading

import pygame

from core import config
from core.input import DOWN, MOVE, UP, normalize_event
from core.screen_manager import ScreenManager
from core.spanish_dates import time_phrase
from services import voice_service

DRAG_THRESHOLD = 12


class App:
    def __init__(self):
        pygame.init()

        self.logical_size = (
            config.get("display", "width", default=600),
            config.get("display", "height", default=1024),
        )
        self.rotate = config.get("display", "rotate", default=0)
        fullscreen = config.get("display", "fullscreen", default=True)
        self.fps = config.get("display", "fps", default=30)

        flags = pygame.FULLSCREEN if fullscreen else 0
        self.display_surface = pygame.display.set_mode(self._physical_size(), flags)
        pygame.display.set_caption("MultiScreenPi")
        pygame.mouse.set_visible(False)

        self.logical_surface = pygame.Surface(self.logical_size)

        self.clock = pygame.time.Clock()
        self.screens = ScreenManager()
        self.running = True

        self._touch_start = None
        self._touch_last = None
        self._dragging = False

        self._announce_elapsed = 0.0

    def _physical_size(self):
        lw, lh = self.logical_size
        if self.rotate in (90, 270):
            return lh, lw
        return lw, lh

    def _transform_pos(self, pos):
        """Convierte una posicion en coordenadas fisicas de pantalla a coordenadas del canvas logico."""
        px, py = pos
        pw, ph = self.display_surface.get_size()
        if self.rotate == 90:
            return py, pw - px
        if self.rotate == 270:
            return ph - py, px
        if self.rotate == 180:
            return pw - px, ph - py
        return px, py

    def _handle_touch(self, kind, pos):
        if kind == DOWN:
            self._touch_start = pos
            self._touch_last = pos
            self._dragging = False
        elif kind == MOVE and self._touch_last is not None:
            dy = pos[1] - self._touch_last[1]
            if not self._dragging:
                total_dx = pos[0] - self._touch_start[0]
                total_dy = pos[1] - self._touch_start[1]
                if (total_dx**2 + total_dy**2) ** 0.5 > DRAG_THRESHOLD:
                    self._dragging = True
            if self._dragging:
                self.screens.handle_scroll(dy)
            self._touch_last = pos
        elif kind == UP:
            if not self._dragging and self._touch_start is not None:
                self.screens.handle_tap(self._touch_start)
            self._touch_start = None
            self._touch_last = None
            self._dragging = False

    def _maybe_announce_time(self, dt):
        if not config.get("voice", "hourly_announcement", default=True):
            return
        interval = config.get("voice", "interval_minutes", default=60) * 60
        if interval <= 0:
            return

        self._announce_elapsed += dt
        if self._announce_elapsed >= interval:
            self._announce_elapsed = 0.0
            threading.Thread(target=self._speak_time, daemon=True).start()

    def _speak_time(self):
        try:
            voice_service.speak(time_phrase())
        except voice_service.VoiceError:
            pass

    def _present(self):
        if self.rotate == 0:
            self.display_surface.blit(self.logical_surface, (0, 0))
        else:
            rotated = pygame.transform.rotate(self.logical_surface, -self.rotate)
            self.display_surface.blit(rotated, (0, 0))

    def run(self):
        while self.running:
            dt = self.clock.tick(self.fps) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                    continue

                kind, pos = normalize_event(event, self._transform_pos)
                self._handle_touch(kind, pos)
                self.screens.handle_event(event)

            self._maybe_announce_time(dt)

            self.screens.update(dt)
            self.screens.draw(self.logical_surface)
            self._present()
            pygame.display.flip()

        pygame.quit()
