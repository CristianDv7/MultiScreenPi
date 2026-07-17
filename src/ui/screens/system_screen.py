import threading

import pygame

from core.screen_manager import Screen
from services import system_service
from ui import theme
from ui.widgets.button import Button, back_button

STATS_CARD = pygame.Rect(24, 100, 600 - 48, 220)
CONFIRM_TIMEOUT = 5.0


class SystemScreen(Screen):
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.ip_address = None
        self.cpu_temp = None
        self.memory = None
        self.uptime = None
        self.loading = False
        self.confirm_action = None
        self.confirm_elapsed = 0.0

    def on_enter(self):
        self.confirm_action = None
        self._load()

    def _load(self):
        if self.loading:
            return
        self.loading = True
        threading.Thread(target=self._load_worker, daemon=True).start()

    def _load_worker(self):
        self.ip_address = system_service.get_local_ip()
        self.cpu_temp = system_service.get_cpu_temp_c()
        self.memory = system_service.get_memory_usage()
        self.uptime = system_service.get_uptime()
        self.loading = False

    def update(self, dt):
        if self.confirm_action:
            self.confirm_elapsed += dt
            if self.confirm_elapsed > CONFIRM_TIMEOUT:
                self.confirm_action = None

    def _reboot_tap(self):
        if self.confirm_action == "reboot":
            self.confirm_action = None
            system_service.reboot()
        else:
            self.confirm_action = "reboot"
            self.confirm_elapsed = 0.0

    def _shutdown_tap(self):
        if self.confirm_action == "shutdown":
            self.confirm_action = None
            system_service.shutdown()
        else:
            self.confirm_action = "shutdown"
            self.confirm_elapsed = 0.0

    def _buttons(self):
        reboot_label = "Toca de nuevo para reiniciar" if self.confirm_action == "reboot" else "Reiniciar"
        shutdown_label = "Toca de nuevo para apagar" if self.confirm_action == "shutdown" else "Apagar"
        return [
            back_button(24, 24, self.screen_manager.pop),
            Button((600 - 24 - 150, 24, 150, 56), "Actualizar", self._load),
            Button((24, 370, 600 - 48, 70), reboot_label, self._reboot_tap, accent=theme.GOLD),
            Button(
                (24, 450, 600 - 48, 70),
                shutdown_label,
                self._shutdown_tap,
                bg=theme.DANGER,
                text_color=(255, 255, 255),
            ),
        ]

    def on_tap(self, pos):
        for button in self._buttons():
            if button.handle_tap(pos):
                return

    def draw(self, surface):
        surface.fill(theme.BG)

        for button in self._buttons():
            button.draw(surface)

        pygame.draw.rect(surface, theme.SURFACE, STATS_CARD, border_radius=24)
        pygame.draw.rect(surface, theme.INDIGO, STATS_CARD, width=3, border_radius=24)

        x = STATS_CARD.left + 24
        y = STATS_CARD.top + 20

        temp_text = f"{self.cpu_temp}°C" if self.cpu_temp is not None else "no disponible"
        lines = [f"IP: {self.ip_address or 'no disponible'}", f"Temperatura CPU: {temp_text}"]

        if self.memory:
            lines.append(
                f"RAM: {self.memory['used_mb']} / {self.memory['total_mb']} MB ({self.memory['percent']}%)"
            )
        else:
            lines.append("RAM: no disponible")

        lines.append(f"Encendida hace: {self.uptime or 'no disponible'}")

        for line in lines:
            surface.blit(theme.FONT_BODY.render(line, True, theme.TEXT), (x, y))
            y += 44

        if self.confirm_action:
            warn = theme.FONT_SMALL.render(
                "Toca de nuevo el mismo boton en 5s para confirmar, o espera para cancelar", True, theme.DANGER
            )
            surface.blit(warn, (24, 340))
