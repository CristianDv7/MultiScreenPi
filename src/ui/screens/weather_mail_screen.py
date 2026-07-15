import threading

import pygame

from core.screen_manager import Screen
from services import mail_service, weather_service
from ui import theme
from ui.widgets.button import Button

WEATHER_CARD = pygame.Rect(24, 100, 600 - 48, 260)
MAIL_CARD = pygame.Rect(24, 380, 600 - 48, 560)


class WeatherMailScreen(Screen):
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.weather = None
        self.weather_error = None
        self.mail = None
        self.mail_error = None
        self.loading = False
        self.buttons = []

    def on_enter(self):
        self.buttons = [
            Button((24, 24, 100, 56), "< Volver", self.screen_manager.pop),
            Button((600 - 24 - 150, 24, 150, 56), "Actualizar", self._load),
        ]
        self._load()

    def _load(self):
        if self.loading:
            return
        self.loading = True
        self.weather = None
        self.weather_error = None
        self.mail = None
        self.mail_error = None
        threading.Thread(target=self._load_weather, daemon=True).start()
        threading.Thread(target=self._load_mail, daemon=True).start()

    def _load_weather(self):
        try:
            self.weather = weather_service.fetch_current()
        except weather_service.WeatherError as exc:
            self.weather_error = str(exc)
        finally:
            self._maybe_done()

    def _load_mail(self):
        try:
            self.mail = mail_service.fetch_unread(limit=5)
        except mail_service.MailError as exc:
            self.mail_error = str(exc)
        finally:
            self._maybe_done()

    def _maybe_done(self):
        weather_ready = self.weather is not None or self.weather_error
        mail_ready = self.mail is not None or self.mail_error
        if weather_ready and mail_ready:
            self.loading = False

    def on_tap(self, pos):
        for button in self.buttons:
            if button.handle_tap(pos):
                return

    def draw(self, surface):
        surface.fill(theme.BG)

        for button in self.buttons:
            button.draw(surface)

        self._draw_weather_card(surface)
        self._draw_mail_card(surface)

    def _draw_weather_card(self, surface):
        pygame.draw.rect(surface, theme.SURFACE, WEATHER_CARD, border_radius=24)
        pygame.draw.rect(surface, theme.INDIGO, WEATHER_CARD, width=3, border_radius=24)

        x = WEATHER_CARD.left + 24
        y = WEATHER_CARD.top + 20

        if self.loading and self.weather is None and not self.weather_error:
            surface.blit(theme.FONT_BODY.render("Cargando clima...", True, theme.TEXT_MUTED), (x, y))
            return

        if self.weather_error:
            for line in _wrap(f"Error: {self.weather_error}", theme.FONT_SMALL, WEATHER_CARD.width - 48):
                surface.blit(theme.FONT_SMALL.render(line, True, theme.TEXT_MUTED), (x, y))
                y += 24
            return

        data = self.weather
        surface.blit(theme.FONT_BODY.render(data["city"], True, theme.TEXT), (x, y))
        y += 44

        surface.blit(theme.FONT_TIMER.render(f"{data['temp']}°C", True, theme.TEXT), (x, y))
        y += 76

        surface.blit(theme.FONT_BODY.render(data["description"], True, theme.TEXT_MUTED), (x, y))
        y += 38

        extra = f"Sensacion: {data['feels_like']}°C   Humedad: {data['humidity']}%"
        surface.blit(theme.FONT_SMALL.render(extra, True, theme.TEXT_MUTED), (x, y))

    def _draw_mail_card(self, surface):
        pygame.draw.rect(surface, theme.SURFACE, MAIL_CARD, border_radius=24)
        pygame.draw.rect(surface, theme.GOLD, MAIL_CARD, width=3, border_radius=24)

        x = MAIL_CARD.left + 24
        y = MAIL_CARD.top + 20

        if self.loading and self.mail is None and not self.mail_error:
            surface.blit(theme.FONT_BODY.render("Cargando correos...", True, theme.TEXT_MUTED), (x, y))
            return

        if self.mail_error:
            for line in _wrap(f"Error: {self.mail_error}", theme.FONT_SMALL, MAIL_CARD.width - 48):
                surface.blit(theme.FONT_SMALL.render(line, True, theme.TEXT_MUTED), (x, y))
                y += 24
            return

        count = self.mail["unread_count"]
        surface.blit(theme.FONT_TITLE.render(f"{count} correos nuevos", True, theme.TEXT), (x, y))
        y += 54

        for msg in self.mail["messages"]:
            subject = msg["subject"] or "(sin asunto)"
            for line in _wrap(subject, theme.FONT_SMALL, MAIL_CARD.width - 48)[:2]:
                if y > MAIL_CARD.bottom - 30:
                    return
                surface.blit(theme.FONT_SMALL.render(line, True, theme.TEXT), (x, y))
                y += 24

            sender = (msg["from"] or "")[:60]
            if y > MAIL_CARD.bottom - 30:
                return
            surface.blit(theme.FONT_SMALL.render(sender, True, theme.TEXT_MUTED), (x, y))
            y += 32


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
