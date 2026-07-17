import pygame

from core import config
from core.screen_manager import Screen
from services import system_service, wifi_service
from ui import theme
from ui.widgets.button import Button, back_button
from ui.widgets.keyboard import Keyboard

FIELD_HEIGHT = 50
TITLE_Y = 100
CONTENT_TOP = 155
KEYBOARD_TOP = 720  # deja el teclado pegado al fondo real de la pantalla (1024)
VIEWPORT_HEIGHT = KEYBOARD_TOP - CONTENT_TOP - 10


class SettingsScreen(Screen):
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.values = {}
        self.field_meta = {}
        self.feeds = []
        self.active_field = None
        self.touched_fields = set()
        self.show_password = False
        self.status = None
        self.ip_address = None
        self.buttons = []
        self._dynamic_buttons = []
        self.field_rects = {}
        self.scroll = 0.0
        self.content_height = 0
        self.keyboard = Keyboard(top=KEYBOARD_TOP)

    def on_enter(self):
        self._load_values()
        self.buttons = [
            back_button(24, 24, self.screen_manager.pop),
            Button(
                (600 - 24 - 130, 24, 130, 56),
                "Ocultar" if self.show_password else "Ver",
                self._toggle_show,
            ),
        ]

    def _load_values(self):
        self.feeds = config.get("news", "feeds", default=[]) or []

        self.values = {
            "ssid": "",
            "password": "",
            "timeout": str(config.get("display", "screen_timeout_seconds", default=60)),
            "ha_base_url": config.get("home_assistant", "base_url", default="") or "",
        }
        self.field_meta = {
            "ssid": {"label": "SSID", "mask": False},
            "password": {"label": "Contrasena", "mask": True},
            "timeout": {"label": "60", "mask": False, "numeric": True},
            "ha_base_url": {"label": "http://homeassistant.local:8123", "mask": False},
        }

        for i, feed in enumerate(self.feeds):
            key = f"feed_{i}_url"
            self.values[key] = feed.get("url", "")
            self.field_meta[key] = {"label": feed.get("name", f"Feed {i + 1}"), "mask": False}

        current_ssid = wifi_service.get_current_ssid()
        self.status = f"Conectado a: {current_ssid}" if current_ssid else "Sin conexion WiFi detectada"
        self.ip_address = system_service.get_local_ip()
        self.active_field = None
        self.touched_fields = set()

    def _toggle_show(self):
        self.show_password = not self.show_password

    def _save_wifi(self):
        self.status = "Guardando..."
        try:
            wifi_service.set_wifi(self.values.get("ssid", ""), self.values.get("password", ""))
            self.status = "WiFi guardado. La Pi intentara conectarse a la nueva red."
        except wifi_service.WifiError as exc:
            self.status = f"Error: {exc}"

    def _save_timeout(self):
        value = self.values.get("timeout", "")
        if not value.isdigit():
            self.status = "El tiempo de pantalla debe ser un numero (segundos)"
            return
        seconds = int(value)
        config.set_value("display", "screen_timeout_seconds", value=seconds)
        self.status = f"Tiempo de pantalla guardado: {seconds}s (0 = nunca)"

    def _save_ha(self):
        url = self.values.get("ha_base_url", "").strip()
        if not url:
            self.status = "La URL de Home Assistant no puede estar vacia"
            return
        config.set_value("home_assistant", "base_url", value=url)
        self.status = "URL de Home Assistant guardada"

    def _save_feeds(self):
        feeds = []
        for i, feed in enumerate(self.feeds):
            key = f"feed_{i}_url"
            feeds.append({"name": feed.get("name", f"Feed {i + 1}"), "url": self.values.get(key, "").strip()})
        config.set_value("news", "feeds", value=feeds)
        self.status = "URLs de noticias guardadas"

    def _layout_rows(self):
        ip_text = f"IP: {self.ip_address}" if self.ip_address else "IP: no disponible"
        rows = [
            ("text", ip_text),
            ("label", "WiFi"),
            ("field", "ssid"),
            ("field", "password"),
            ("button", "Guardar WiFi", self._save_wifi),
            ("text", self.status),
            ("gap",),
            ("label", "Tiempo de pantalla (segundos, 0 = nunca)"),
            ("field", "timeout"),
            ("button", "Guardar tiempo de pantalla", self._save_timeout),
            ("gap",),
            ("label", "Home Assistant (URL)"),
            ("field", "ha_base_url"),
            ("button", "Guardar Home Assistant", self._save_ha),
            ("gap",),
            ("label", "Noticias (URL de cada feed)"),
        ]
        for i in range(len(self.feeds)):
            rows.append(("field", f"feed_{i}_url"))
        if self.feeds:
            rows.append(("button", "Guardar noticias", self._save_feeds))
        return rows

    def on_tap(self, pos):
        for button in self.buttons:
            if button.handle_tap(pos):
                return

        for key, rect in self.field_rects.items():
            if rect.collidepoint(pos):
                self.active_field = key
                if key not in self.touched_fields:
                    self.values[key] = ""
                    self.touched_fields.add(key)
                return

        for button in self._dynamic_buttons:
            if button.handle_tap(pos):
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
        if not self.active_field:
            return
        meta = self.field_meta.get(self.active_field, {})
        if meta.get("numeric") and not char.isdigit():
            return
        self.values[self.active_field] = self.values.get(self.active_field, "") + char

    def _backspace(self):
        if not self.active_field:
            return
        self.values[self.active_field] = self.values.get(self.active_field, "")[:-1]

    def on_scroll(self, dy):
        max_scroll = max(0, self.content_height - VIEWPORT_HEIGHT)
        self.scroll = min(max_scroll, max(0, self.scroll - dy))

    def draw(self, surface):
        surface.fill(theme.BG)
        w, h = surface.get_size()

        title_surf = theme.FONT_TITLE.render("Configuracion", True, theme.TEXT)
        surface.blit(title_surf, (24, TITLE_Y))

        for button in self.buttons:
            button.draw(surface)

        clip_rect = pygame.Rect(0, CONTENT_TOP, w, VIEWPORT_HEIGHT)
        surface.set_clip(clip_rect)

        y = CONTENT_TOP - int(self.scroll)
        self.field_rects = {}
        self._dynamic_buttons = []

        for row in self._layout_rows():
            kind = row[0]
            if kind == "text":
                text = row[1]
                if text:
                    for line in _wrap(text, theme.FONT_SMALL, w - 48):
                        surface.blit(theme.FONT_SMALL.render(line, True, theme.TEXT_MUTED), (24, y))
                        y += 24
                y += 6
            elif kind == "label":
                surface.blit(theme.FONT_SMALL.render(row[1], True, theme.TEXT_MUTED), (24, y))
                y += 30
            elif kind == "field":
                key = row[1]
                rect = pygame.Rect(24, y, w - 48, FIELD_HEIGHT)
                self.field_rects[key] = rect
                meta = self.field_meta.get(key, {})
                mask = bool(meta.get("mask")) and not self.show_password
                self._draw_field(
                    surface, rect, meta.get("label", ""), self.values.get(key, ""), self.active_field == key, mask
                )
                y += FIELD_HEIGHT + 10
            elif kind == "button":
                _, label, callback = row
                rect = (24, y, w - 48, 56)
                btn = Button(rect, label, callback)
                btn.draw(surface)
                self._dynamic_buttons.append(btn)
                y += 56 + 10
            elif kind == "gap":
                y += 16

        self.content_height = y + int(self.scroll) - CONTENT_TOP
        surface.set_clip(None)

        self.keyboard.draw(surface)

    def _draw_field(self, surface, rect, placeholder, value, active, mask):
        pygame.draw.rect(surface, theme.SURFACE, rect, border_radius=10)
        border_color = theme.PRIMARY if active else theme.TEXT_MUTED
        pygame.draw.rect(surface, border_color, rect, width=2, border_radius=10)

        shown = ("*" * len(value)) if mask else value
        text = shown if shown else placeholder
        text_color = theme.TEXT if shown else theme.TEXT_MUTED
        text_surf = theme.FONT_SMALL.render(text, True, text_color)
        clip = surface.get_clip()
        surface.set_clip(rect.inflate(-8, 0))
        surface.blit(text_surf, text_surf.get_rect(midleft=(rect.left + 16, rect.centery)))
        surface.set_clip(clip)


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
