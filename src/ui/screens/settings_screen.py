import pygame

from core import config
from core.screen_manager import Screen
from services import system_service, wifi_service
from ui import theme
from ui.widgets.button import Button
from ui.widgets.keyboard import Keyboard

FIELD_HEIGHT = 50
SSID_RECT = pygame.Rect(24, 156, 600 - 48, FIELD_HEIGHT)
PASSWORD_RECT = pygame.Rect(24, 214, 600 - 48, FIELD_HEIGHT)
WIFI_SAVE_RECT = (24, 272, 600 - 48, FIELD_HEIGHT)
STATUS_Y = 332
TIMEOUT_RECT = pygame.Rect(24, 418, 600 - 48, FIELD_HEIGHT)
TIMEOUT_SAVE_RECT = (24, 476, 600 - 48, FIELD_HEIGHT)


class SettingsScreen(Screen):
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.ssid = ""
        self.password = ""
        self.timeout_value = ""
        self.active_field = "ssid"
        self.show_password = False
        self.status = None
        self.saving = False
        self.buttons = []
        self.keyboard = Keyboard(top=545)
        self._timeout_touched = False
        self.ip_address = None

    def on_enter(self):
        current = wifi_service.get_current_ssid()
        self.status = f"Conectado a: {current}" if current else "Sin conexion WiFi detectada"
        self.ip_address = system_service.get_local_ip()
        self.timeout_value = str(config.get("display", "screen_timeout_seconds", default=60))
        self._timeout_touched = False
        self._build_buttons()

    def _build_buttons(self):
        self.buttons = [
            Button((24, 24, 130, 56), "< Volver", self.screen_manager.pop),
            Button(
                (600 - 24 - 130, 24, 130, 56),
                "Ocultar" if self.show_password else "Ver",
                self._toggle_show,
            ),
            Button(WIFI_SAVE_RECT, "Guardar WiFi", self._save_wifi),
            Button(TIMEOUT_SAVE_RECT, "Guardar tiempo de pantalla", self._save_timeout),
        ]

    def _toggle_show(self):
        self.show_password = not self.show_password
        self._build_buttons()

    def _save_wifi(self):
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

    def _save_timeout(self):
        if not self.timeout_value.isdigit():
            self.status = "El tiempo de pantalla debe ser un numero (segundos)"
            return
        seconds = int(self.timeout_value)
        config.set_value(seconds, "display", "screen_timeout_seconds")
        self.status = f"Tiempo de pantalla guardado: {seconds}s (0 = nunca)"

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
        if TIMEOUT_RECT.collidepoint(pos):
            self.active_field = "timeout"
            if not self._timeout_touched:
                self.timeout_value = ""
                self._timeout_touched = True
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
        elif self.active_field == "timeout" and char.isdigit():
            self.timeout_value += char

    def _backspace(self):
        if self.active_field == "ssid":
            self.ssid = self.ssid[:-1]
        elif self.active_field == "password":
            self.password = self.password[:-1]
        elif self.active_field == "timeout":
            self.timeout_value = self.timeout_value[:-1]

    def draw(self, surface):
        surface.fill(theme.BG)
        w = surface.get_width()

        title_surf = theme.FONT_TITLE.render("Configuracion", True, theme.TEXT)
        surface.blit(title_surf, (24, 64))

        ip_text = f"IP: {self.ip_address}" if self.ip_address else "IP: no disponible"
        ip_surf = theme.FONT_SMALL.render(ip_text, True, theme.TEXT_MUTED)
        surface.blit(ip_surf, (24, 100))

        wifi_label = theme.FONT_SMALL.render("WiFi", True, theme.TEXT_MUTED)
        surface.blit(wifi_label, (24, 130))

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
            y = STATUS_Y
            for line in _wrap(self.status, theme.FONT_SMALL, w - 48):
                surface.blit(theme.FONT_SMALL.render(line, True, theme.TEXT_MUTED), (24, y))
                y += 24

        timeout_label = theme.FONT_SMALL.render(
            "Tiempo de pantalla (segundos, 0 = nunca)", True, theme.TEXT_MUTED
        )
        surface.blit(timeout_label, (24, 392))
        self._draw_field(
            surface, TIMEOUT_RECT, "60", self.timeout_value, self.active_field == "timeout", mask=False
        )

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
