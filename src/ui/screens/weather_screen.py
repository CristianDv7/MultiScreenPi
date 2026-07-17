import threading

import pygame

from core.screen_manager import Screen
from core.spanish_dates import today_label
from services import voice_service, weather_service
from ui import theme
from ui.widgets.button import Button, back_button

DATE_Y = 92
CURRENT_CARD = pygame.Rect(24, 140, 600 - 48, 180)
FORECAST_TOP = 370
ROW_HEIGHT = 60
ROW_GAP = 8


class WeatherScreen(Screen):
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.current = None
        self.forecast = []
        self.error = None
        self.loading = False
        self.buttons = []

    def on_enter(self):
        self.buttons = [
            back_button(24, 24, self.screen_manager.pop),
            Button((166, 24, 150, 56), "Leer clima", self._read_weather),
            Button((600 - 24 - 150, 24, 150, 56), "Actualizar", self._force_load),
        ]
        self._load()

    def _force_load(self):
        self._load(force=True)

    def _read_weather(self):
        if not self.current:
            return
        data = self.current
        phrase = (
            f"El clima en {data['city']} es {data['temp']} grados, {data['description']}. "
            f"Sensacion termica {data['feels_like']} grados, humedad {data['humidity']} por ciento."
        )
        threading.Thread(target=self._speak_worker, args=(phrase,), daemon=True).start()

    def _speak_worker(self, text):
        try:
            voice_service.speak(text)
        except voice_service.VoiceError as exc:
            self.error = str(exc)

    def _load(self, force=False):
        if self.loading:
            return
        self.loading = True
        self.error = None
        self.current = None
        self.forecast = []
        threading.Thread(target=self._load_worker, args=(force,), daemon=True).start()

    def _load_worker(self, force):
        try:
            self.current = weather_service.fetch_current(force=force)
            self.forecast = weather_service.fetch_hourly_forecast(limit=8, force=force)
        except weather_service.WeatherError as exc:
            self.error = str(exc)
        finally:
            self.loading = False

    def on_tap(self, pos):
        for button in self.buttons:
            if button.handle_tap(pos):
                return

    def draw(self, surface):
        surface.fill(theme.BG)
        w = surface.get_width()

        for button in self.buttons:
            button.draw(surface)

        date_surf = theme.FONT_BODY.render(today_label(), True, theme.TEXT_MUTED)
        surface.blit(date_surf, (24, DATE_Y))

        pygame.draw.rect(surface, theme.SURFACE, CURRENT_CARD, border_radius=24)
        pygame.draw.rect(surface, theme.INDIGO, CURRENT_CARD, width=3, border_radius=24)

        x = CURRENT_CARD.left + 24
        y = CURRENT_CARD.top + 20

        if self.loading and self.current is None and not self.error:
            surface.blit(theme.FONT_BODY.render("Cargando clima...", True, theme.TEXT_MUTED), (x, y))
            return

        if self.error:
            for line in _wrap(f"Error: {self.error}", theme.FONT_SMALL, CURRENT_CARD.width - 48):
                surface.blit(theme.FONT_SMALL.render(line, True, theme.TEXT_MUTED), (x, y))
                y += 24
            return

        data = self.current
        surface.blit(theme.FONT_BODY.render(data["city"], True, theme.TEXT), (x, y))

        temp_surf = theme.FONT_TIMER.render(f"{data['temp']}°C", True, theme.TEXT)
        surface.blit(temp_surf, (CURRENT_CARD.right - 24 - temp_surf.get_width(), CURRENT_CARD.top + 30))

        y += 44
        surface.blit(theme.FONT_BODY.render(data["description"], True, theme.TEXT_MUTED), (x, y))
        y += 38
        extra = f"Sensacion: {data['feels_like']}°C   Humedad: {data['humidity']}%"
        surface.blit(theme.FONT_SMALL.render(extra, True, theme.TEXT_MUTED), (x, y))

        surface.blit(theme.FONT_BODY.render("Pronostico por horas", True, theme.TEXT), (24, FORECAST_TOP - 44))

        row_y = FORECAST_TOP
        for entry in self.forecast:
            row_rect = pygame.Rect(24, row_y, w - 48, ROW_HEIGHT)
            pygame.draw.rect(surface, theme.SURFACE, row_rect, border_radius=14)

            time_surf = theme.FONT_SMALL.render(entry["time"], True, theme.TEXT)
            surface.blit(time_surf, time_surf.get_rect(midleft=(row_rect.left + 20, row_rect.centery)))

            desc_surf = theme.FONT_SMALL.render(entry["description"], True, theme.TEXT_MUTED)
            surface.blit(desc_surf, desc_surf.get_rect(center=(row_rect.centerx, row_rect.centery)))

            temp_surf = theme.FONT_BODY.render(f"{entry['temp']}°C", True, theme.GOLD)
            surface.blit(temp_surf, temp_surf.get_rect(midright=(row_rect.right - 20, row_rect.centery)))

            row_y += ROW_HEIGHT + ROW_GAP


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
