from core import config
from core.screen_manager import Screen
from ui import theme
from ui.screens.home_assistant_screen import HomeAssistantScreen
from ui.screens.placeholder_screen import PlaceholderScreen
from ui.screens.news_screen import NewsScreen
from ui.screens.pomodoro_screen import PomodoroScreen
from ui.screens.settings_screen import SettingsScreen
from ui.screens.weather_mail_screen import WeatherMailScreen
from ui.widgets.button import Button

MENU_ITEMS = [
    ("Pomodoro", "Temporizador personalizable", PomodoroScreen, theme.GOLD),
    ("Noticias", "Titulares desde un feed", NewsScreen, theme.BLUE),
    ("Home Assistant", "Controla tus luces", HomeAssistantScreen, theme.GREEN),
    ("Metricas Ubicate", "Dashboard desde Supabase", None, theme.GOLD),
    ("Clima y Correos", "Vistazo rapido del dia", WeatherMailScreen, theme.BLUE),
]


class MainMenuScreen(Screen):
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.buttons = []
        self.settings_button = None
        self.idle_elapsed = 0.0
        self.blanked = False

    def on_enter(self):
        self.buttons = []
        top = 140
        spacing = 16
        button_height = 130
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
            surface.fill((0, 0, 0))
            return

        surface.fill(theme.BG)

        header = theme.FONT_TITLE.render("MultiScreenPi", True, theme.TEXT)
        surface.blit(header, (24, 50))

        for button in self.buttons:
            button.draw(surface)

        if self.settings_button:
            self.settings_button.draw(surface)
