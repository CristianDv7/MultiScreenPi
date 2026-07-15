import datetime
import threading
from pathlib import Path

import pygame

from core import config
from core.screen_manager import Screen
from core.spanish_dates import today_label
from services import weather_service
from ui import theme
from ui.screens.home_assistant_screen import HomeAssistantScreen
from ui.screens.pc_control_screen import PCControlScreen
from ui.screens.placeholder_screen import PlaceholderScreen
from ui.screens.news_screen import NewsScreen
from ui.screens.pomodoro_screen import PomodoroScreen
from ui.screens.settings_screen import SettingsScreen
from ui.screens.system_screen import SystemScreen
from ui.screens.weather_screen import WeatherScreen
from ui.widgets.button import Button

WEATHER_REFRESH_SECONDS = 600  # 10 minutos
SLIDESHOW_INTERVAL_SECONDS = 10
SLIDESHOW_DIR = Path(__file__).resolve().parents[3] / "assets" / "slideshow"
SLIDESHOW_MAX_SIZE = (520, 520)

MENU_ITEMS = [
    ("Pomodoro", "Temporizador personalizable", PomodoroScreen, theme.GOLD),
    ("Noticias", "Titulares desde un feed", NewsScreen, theme.BLUE),
    ("Home Assistant", "Controla tus luces", HomeAssistantScreen, theme.GREEN),
    ("Metricas Ubicate", "Dashboard desde Supabase", None, theme.GOLD),
    ("Clima", "Pronostico por horas", WeatherScreen, theme.BLUE),
    ("Mi PC", "Abrir apps y sitios en tu PC", PCControlScreen, theme.LAVENDER),
    ("Sistema", "Salud de la Pi, apagar y reiniciar", SystemScreen, theme.GRAY_NEUTRAL),
]


class MainMenuScreen(Screen):
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.buttons = []
        self.settings_button = None
        self.idle_elapsed = 0.0
        self.blanked = False

        self._weather_cache = None
        self._weather_loading = False
        self._weather_elapsed = WEATHER_REFRESH_SECONDS  # fuerza una carga inicial

        self._slideshow_paths = []
        self._slideshow_scanned = False
        self._slideshow_index = 0
        self._slideshow_elapsed = 0.0
        self._slideshow_surface = None
        self._slideshow_loading = False

    def on_enter(self):
        self.buttons = []
        top = 140
        spacing = 14
        button_height = 108
        width = 600 - 48

        for i, (title, subtitle, screen_cls, accent) in enumerate(MENU_ITEMS):
            rect = (24, top + i * (button_height + spacing), width, button_height)
            self.buttons.append(
                Button(rect, title, self._make_opener(title, screen_cls), subtitle=subtitle, accent=accent)
            )

        self.settings_button = Button(
            (600 - 24 - 140, 24, 140, 56),
            "Ajustes",
            self._make_opener("Configuracion", SettingsScreen),
            accent=theme.GOLD,
        )

        self.idle_elapsed = 0.0
        self.blanked = False

    def _make_opener(self, title, screen_cls):
        def opener():
            if screen_cls is not None:
                self.screen_manager.push(screen_cls(self.screen_manager))
            else:
                self.screen_manager.push(PlaceholderScreen(self.screen_manager, title))

        return opener

    def _timeout_seconds(self):
        return config.get("display", "screen_timeout_seconds", default=60)

    def update(self, dt):
        timeout = self._timeout_seconds()
        if timeout and timeout > 0:
            self.idle_elapsed += dt
            if self.idle_elapsed >= timeout:
                self.blanked = True
        else:
            self.blanked = False

        self._weather_elapsed += dt
        if self._weather_elapsed >= WEATHER_REFRESH_SECONDS and not self._weather_loading:
            self._weather_elapsed = 0.0
            self._weather_loading = True
            threading.Thread(target=self._fetch_weather, daemon=True).start()

        if self.blanked:
            self._update_slideshow(dt)

    def _fetch_weather(self):
        try:
            self._weather_cache = weather_service.fetch_current()
        except weather_service.WeatherError:
            pass
        finally:
            self._weather_loading = False

    def _update_slideshow(self, dt):
        if not self._slideshow_scanned:
            self._slideshow_scanned = True
            self._slideshow_paths = self._scan_slideshow_images()
            if self._slideshow_paths:
                self._load_slideshow_image()
            return

        if not self._slideshow_paths:
            return

        self._slideshow_elapsed += dt
        if self._slideshow_elapsed >= SLIDESHOW_INTERVAL_SECONDS and not self._slideshow_loading:
            self._slideshow_elapsed = 0.0
            self._slideshow_index = (self._slideshow_index + 1) % len(self._slideshow_paths)
            self._load_slideshow_image()

    def _scan_slideshow_images(self):
        if not SLIDESHOW_DIR.exists():
            return []
        exts = (".jpg", ".jpeg", ".png")
        return sorted(str(p) for p in SLIDESHOW_DIR.iterdir() if p.suffix.lower() in exts)

    def _load_slideshow_image(self):
        self._slideshow_loading = True
        threading.Thread(target=self._load_slideshow_worker, daemon=True).start()

    def _load_slideshow_worker(self):
        path = self._slideshow_paths[self._slideshow_index]
        try:
            image = pygame.image.load(path).convert()
            w, h = image.get_size()
            max_w, max_h = SLIDESHOW_MAX_SIZE
            scale = min(max_w / w, max_h / h, 1)
            if scale < 1:
                image = pygame.transform.smoothscale(image, (int(w * scale), int(h * scale)))
            self._slideshow_surface = image
        except (pygame.error, OSError):
            self._slideshow_surface = None
        finally:
            self._slideshow_loading = False

    def on_tap(self, pos):
        self.idle_elapsed = 0.0
        if self.blanked:
            self.blanked = False
            return

        for button in self.buttons:
            if button.handle_tap(pos):
                return
        if self.settings_button:
            self.settings_button.handle_tap(pos)

    def on_scroll(self, dy):
        self.idle_elapsed = 0.0
        self.blanked = False

    def draw(self, surface):
        if self.blanked:
            self._draw_clock(surface)
            return

        surface.fill(theme.BG)

        header = theme.FONT_TITLE.render("MultiScreenPi", True, theme.TEXT)
        surface.blit(header, (24, 50))

        for button in self.buttons:
            button.draw(surface)

        if self.settings_button:
            self.settings_button.draw(surface)

    def _draw_clock(self, surface):
        surface.fill((0, 0, 0))
        w, _h = surface.get_size()

        time_surf = theme.FONT_TIMER_XL.render(
            datetime.datetime.now().strftime("%H:%M:%S"), True, theme.LAVENDER
        )
        surface.blit(time_surf, time_surf.get_rect(center=(w // 2, 150)))

        date_surf = theme.FONT_BODY.render(today_label(), True, (150, 150, 160))
        surface.blit(date_surf, date_surf.get_rect(center=(w // 2, 250)))

        if self._weather_cache:
            data = self._weather_cache
            weather_text = f"{data['city']} - {data['temp']}°C - {data['description']}"
            weather_surf = theme.FONT_BODY.render(weather_text, True, theme.GOLD)
            surface.blit(weather_surf, weather_surf.get_rect(center=(w // 2, 290)))

        if self._slideshow_surface:
            top = 340
            img_rect = self._slideshow_surface.get_rect(
                center=(w // 2, top + self._slideshow_surface.get_height() // 2)
            )
            surface.blit(self._slideshow_surface, img_rect)
