"""Diagnostico rapido: confirma que la pantalla enciende en la orientacion
correcta y que los toques se registran en la posicion esperada, antes de
construir el resto de la app.

Uso en la Pi:
    cd MultiScreenPi/src
    python3 hw_test.py

Toca distintas zonas de la pantalla: cada toque dibuja un circulo en la
posicion logica (post-rotacion) y lo imprime en la terminal. Si el circulo
no aparece donde tocaste, o el texto sale rotado/al reves, avisa para
ajustar el valor de "rotate" en config/config.yaml (prueba 90 <-> 270).

Ctrl+C en la terminal para salir.
"""

import pygame

from core.app import App
from core.screen_manager import Screen


class DiagnosticScreen(Screen):
    def __init__(self):
        self.taps = []
        self.font = pygame.font.Font(None, 28)

    def on_tap(self, pos):
        print(f"TAP en {pos}", flush=True)
        self.taps.append(pos)

    def draw(self, surface):
        surface.fill((20, 20, 24))
        for pos in self.taps[-30:]:
            pygame.draw.circle(surface, (78, 168, 222), pos, 14)

        w, h = surface.get_size()
        lines = [
            f"Canvas logico: {w}x{h}",
            "Toca la pantalla para probar.",
            "Este texto debe leerse normal, sin rotar.",
        ]
        for i, line in enumerate(lines):
            text = self.font.render(line, True, (235, 235, 240))
            surface.blit(text, (10, 10 + i * 30))


def main():
    app = App()
    app.screens.push(DiagnosticScreen())
    app.run()


if __name__ == "__main__":
    main()
