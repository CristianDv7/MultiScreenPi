import pygame

from ui import theme

LETTER_ROWS = ["1234567890", "qwertyuiop", "asdfghjkl", "zxcvbnm"]
SYMBOL_ROWS = ["1234567890", "!@#$%^&*()", "-_=+:;\"'", ".,/\\[]{}"]

KEY_H = 54
KEY_GAP = 6
SIDE_MARGIN = 10


class Keyboard:
    """Teclado en pantalla simple: letras/numeros, simbolos, shift, espacio, borrar y listo."""

    def __init__(self, top):
        self.top = top
        self.shift = False
        self.symbols = False
        self._keys = []
        self.bottom = top
        self._layout()

    def _rows(self):
        return SYMBOL_ROWS if self.symbols else LETTER_ROWS

    def _layout(self):
        self._keys = []
        y = self.top
        width_available = 600 - SIDE_MARGIN * 2

        for row in self._rows():
            n = len(row)
            key_w = (width_available - KEY_GAP * (n - 1)) / n
            x = SIDE_MARGIN
            for ch in row:
                label = ch.upper() if (self.shift and ch.isalpha()) else ch
                rect = pygame.Rect(int(x), y, int(key_w), KEY_H)
                self._keys.append((rect, label, ch if not (self.shift and ch.isalpha()) else ch.upper()))
                x += key_w + KEY_GAP
            y += KEY_H + KEY_GAP

        specials = [("SHIFT", 90), ("SYM", 90), ("ESPACIO", 210), ("BORRAR", 90), ("LISTO", 90)]
        total_w = sum(w for _, w in specials) + KEY_GAP * (len(specials) - 1)
        x = SIDE_MARGIN + max(0, (width_available - total_w) // 2)
        for label, w in specials:
            rect = pygame.Rect(int(x), y, int(w), KEY_H)
            self._keys.append((rect, label, label))
            x += w + KEY_GAP

        self.bottom = y + KEY_H

    def handle_tap(self, pos):
        for rect, label, value in self._keys:
            if rect.collidepoint(pos):
                return self._press(label, value)
        return None

    def _press(self, label, value):
        if label == "SHIFT":
            self.shift = not self.shift
            self._layout()
            return None
        if label == "SYM":
            self.symbols = not self.symbols
            self.shift = False
            self._layout()
            return None
        if label == "ESPACIO":
            return " "
        if label == "BORRAR":
            return "BACKSPACE"
        if label == "LISTO":
            return "DONE"
        return value

    def draw(self, surface):
        for rect, label, _value in self._keys:
            pygame.draw.rect(surface, theme.SURFACE, rect, border_radius=8)
            text_surf = theme.FONT_SMALL.render(label, True, theme.TEXT)
            surface.blit(text_surf, text_surf.get_rect(center=rect.center))
