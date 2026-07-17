from core.screen_manager import Screen
from ui import theme
from ui.widgets.button import Button, back_button


class PlaceholderScreen(Screen):
    """Pantalla temporal para las opciones del menu que aun no estan implementadas."""

    def __init__(self, screen_manager, title):
        self.screen_manager = screen_manager
        self.title = title
        self.back_button = None

    def on_enter(self):
        self.back_button = back_button(24, 24, self.screen_manager.pop)

    def on_tap(self, pos):
        if self.back_button:
            self.back_button.handle_tap(pos)

    def draw(self, surface):
        surface.fill(theme.BG)
        self.back_button.draw(surface)

        w, h = surface.get_size()
        title_surf = theme.FONT_TITLE.render(self.title, True, theme.TEXT)
        surface.blit(title_surf, title_surf.get_rect(center=(w // 2, h // 2 - 20)))

        note_surf = theme.FONT_SMALL.render("Proximamente", True, theme.TEXT_MUTED)
        surface.blit(note_surf, note_surf.get_rect(center=(w // 2, h // 2 + 20)))
