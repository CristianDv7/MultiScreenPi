from core.screen_manager import Screen
from ui import theme
from ui.screens.placeholder_screen import PlaceholderScreen
from ui.widgets.button import Button

MENU_ITEMS = [
    ("Pomodoro", "Temporizador personalizable"),
    ("Noticias", "Titulares desde un feed"),
    ("Home Assistant", "Controla tus luces"),
    ("Metricas Ubicate", "Dashboard desde Supabase"),
    ("Clima y Correos", "Vistazo rapido del dia"),
]


class MainMenuScreen(Screen):
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.buttons = []
        self.settings_button = None

    def on_enter(self):
        self.buttons = []
        top = 140
        spacing = 16
        button_height = 130
        width = 600 - 48

        for i, (title, subtitle) in enumerate(MENU_ITEMS):
            rect = (24, top + i * (button_height + spacing), width, button_height)
            self.buttons.append(Button(rect, title, self._make_opener(title), subtitle=subtitle))

        self.settings_button = Button(
            (600 - 24 - 56, 24, 56, 56), "*", self._make_opener("Configuracion")
        )

    def _make_opener(self, title):
        def opener():
            self.screen_manager.push(PlaceholderScreen(self.screen_manager, title))

        return opener

    def on_tap(self, pos):
        for button in self.buttons:
            if button.handle_tap(pos):
                return
        if self.settings_button:
            self.settings_button.handle_tap(pos)

    def draw(self, surface):
        surface.fill(theme.BG)

        header = theme.FONT_TITLE.render("MultiScreenPi", True, theme.TEXT)
        surface.blit(header, (24, 50))

        for button in self.buttons:
            button.draw(surface)

        if self.settings_button:
            self.settings_button.draw(surface)
