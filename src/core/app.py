import pygame

from core import config
from core.input import TAP, normalize_event
from core.screen_manager import ScreenManager


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
                if kind == TAP:
                    self.screens.handle_tap(pos)
                self.screens.handle_event(event)

            self.screens.update(dt)
            self.screens.draw(self.logical_surface)
            self._present()
            pygame.display.flip()

        pygame.quit()
