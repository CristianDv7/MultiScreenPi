import threading

from core.screen_manager import Screen
from services import news_service
from ui import theme
from ui.widgets.button import Button


class NewsScreen(Screen):
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.headlines = []
        self.error = None
        self.loading = False
        self.buttons = []

    def on_enter(self):
        self._build_buttons()
        self._refresh()

    def _build_buttons(self):
        self.buttons = [
            Button((24, 24, 130, 56), "< Volver", self.screen_manager.pop),
            Button((600 - 24 - 150, 24, 150, 56), "Actualizar", self._refresh),
        ]

    def _refresh(self):
        if self.loading:
            return
        self.loading = True
        self.error = None
        threading.Thread(target=self._fetch_worker, daemon=True).start()

    def _fetch_worker(self):
        try:
            self.headlines = news_service.fetch_headlines(limit=12)
        except news_service.NewsFetchError as exc:
            self.error = str(exc)
        finally:
            self.loading = False

    def on_tap(self, pos):
        for button in self.buttons:
            if button.handle_tap(pos):
                return

    def draw(self, surface):
        surface.fill(theme.BG)
        w, h = surface.get_size()

        title_surf = theme.FONT_TITLE.render("Noticias", True, theme.TEXT)
        surface.blit(title_surf, (24, 100))

        y = 160
        if self.loading:
            status = theme.FONT_BODY.render("Cargando...", True, theme.TEXT_MUTED)
            surface.blit(status, (24, y))
        elif self.error:
            for line in _wrap_text(f"Error: {self.error}", theme.FONT_SMALL, w - 48):
                surface.blit(theme.FONT_SMALL.render(line, True, theme.TEXT_MUTED), (24, y))
                y += 22
        elif not self.headlines:
            status = theme.FONT_BODY.render("Sin titulares.", True, theme.TEXT_MUTED)
            surface.blit(status, (24, y))
        else:
            for headline in self.headlines:
                for line in _wrap_text(headline, theme.FONT_SMALL, w - 48):
                    if y > h - 24:
                        break
                    surface.blit(theme.FONT_SMALL.render(line, True, theme.TEXT), (24, y))
                    y += 24
                y += 14

        for button in self.buttons:
            button.draw(surface)


def _wrap_text(text, font, max_width):
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
