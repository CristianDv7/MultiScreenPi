import pygame

from core.screen_manager import Screen
from services import wifi_service
from ui import theme
from ui.widgets.button import Button
from ui.widgets.keyboard import Keyboard

FIELD_HEIGHT = 56
SSID_RECT = pygame.Rect(24, 140, 600 - 48, FIELD_HEIGHT)
PASSWORD_RECT = pygame.Rect(24, 212, 600 - 48, FIELD_HEIGHT)
SAVE_RECT = (24, 480, 600 - 48, 60)


class SettingsScreen(Screen):
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.ssid = ""
        self.password = ""
        self.active_field = "ssid"
        self.show_password = False
        self.status = None
        self.saving = False
        self.buttons = []
        self.keyboard = Keyboard(top=560)

    def on_enter(self):
        current = wifi_service.get_current_ssid()
        self.status = f"Conectado a: {current}" if current else "Sin conexion WiFi detectada"
        self._build_buttons()

    def _build_buttons(self):
        self.buttons = [
            Button((24, 24, 130, 56), "< Volver", self.screen_manager.pop),
            Button(
                (600 - 24 - 130, 24, 130, 56),
                "Ocultar" if self.show_password else "Ver",
                self._toggle_show,
            ),
            Button(SAVE_RECT, "Guardar WiFi", self._save),
        ]

    def _toggle_show(self):
        self.show_password = not self.show_password
        self._build_buttons()

    def _save(self):
        if self.saving:
            return
        self.saving = True
        self.status = "Guardando..."
        try:
            wifi_service.set_wifi(self.ssid, self.password)
            self.status = "Guardado. La Pi intentara conectarse a la nueva red."
        except wifi_service.WifiError as exc:
            self.status = f"Error: {exc}"
        finally:
            self.saving = False

    def on_tap(self, pos):
        for button in self.buttons:
            if button.handle_tap(pos):
                return

        if SSID_RECT.collidepoint(pos):
            self.active_field = "ssid"
            return
        if PASSWORD_RECT.collidepoint(pos):
            self.active_field = "password"
            return

        result = self.keyboard.handle_tap(pos)
        if result is None:
            return
        if result == "BACKSPACE":
            self._backspace()
        elif result == "DONE":
            self.active_field = None
        else:
            self._append(result)

    def _append(self, char):
        if self.active_field == "ssid":
            self.ssid += char
        elif self.active_field == "password":
            self.password += char

    def _backspace(self):
        if self.active_field == "ssid":
            self.ssid = self.ssid[:-1]
        elif self.active_field == "password":
            self.password = self.password[:-1]

    def draw(self, surface):
        surface.fill(theme.BG)
        w = surface.get_width()

        title_surf = theme.FONT_TITLE.render("Configuracion", True, theme.TEXT)
        surface.blit(title_surf, (24, 90))

        self._draw_field(surface, SSID_RECT, "SSID", self.ssid, self.active_field == "ssid", mask=False)
        self._draw_field(
            surface,
            PASSWORD_RECT,
            "Contrasena",
            self.password,
            self.active_field == "password",
            mask=not self.show_password,
        )

        if self.status:
            y = 300
            for line in _wrap(self.status, theme.FONT_SMALL, w - 48):
                surface.blit(theme.FONT_SMALL.render(line, True, theme.TEXT_MUTED), (24, y))
                y += 26

        for button in self.buttons:
            button.draw(surface)

        self.keyboard.draw(surface)

    def _draw_field(self, surface, rect, placeholder, value, active, mask):
        pygame.draw.rect(surface, theme.SURFACE, rect, border_radius=10)
        border_color = theme.PRIMARY if active else theme.TEXT_MUTED
        pygame.draw.rect(surface, border_color, rect, width=2, border_radius=10)

        shown = ("*" * len(value)) if mask else value
        text = shown if shown else placeholder
        text_color = theme.TEXT if shown else theme.TEXT_MUTED
        text_surf = theme.FONT_BODY.render(text, True, text_color)
        surface.blit(text_surf, text_surf.get_rect(midleft=(rect.left + 16, rect.centery)))


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
