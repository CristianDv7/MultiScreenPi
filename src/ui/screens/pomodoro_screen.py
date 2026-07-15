import pygame

from core.screen_manager import Screen
from ui import theme
from ui.widgets.button import Button

FOCUS_STEP = 5
BREAK_STEP = 1

CARD_RECT = pygame.Rect(24, 100, 600 - 48, 430)
STEP_BTN_SIZE = 70


class PomodoroScreen(Screen):
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.focus_minutes = 25
        self.break_minutes = 5
        self.phase = "focus"
        self.remaining = self.focus_minutes * 60
        self.running = False
        self.buttons = []

    def on_enter(self):
        self._build_buttons()

    def _build_buttons(self):
        w = 600
        start_bg = theme.GOLD if self.running else theme.GREEN
        self.buttons = [
            Button((24, 24, 100, 56), "< Volver", self._go_back),
            Button((24, 560, STEP_BTN_SIZE, STEP_BTN_SIZE), "-", self._dec_focus, bg=theme.SURFACE),
            Button(
                (w - 24 - STEP_BTN_SIZE, 560, STEP_BTN_SIZE, STEP_BTN_SIZE), "+", self._inc_focus, bg=theme.SURFACE
            ),
            Button((24, 650, STEP_BTN_SIZE, STEP_BTN_SIZE), "-", self._dec_break, bg=theme.SURFACE),
            Button(
                (w - 24 - STEP_BTN_SIZE, 650, STEP_BTN_SIZE, STEP_BTN_SIZE), "+", self._inc_break, bg=theme.SURFACE
            ),
            Button(
                (24, 750, w - 48, 100),
                self._start_label(),
                self._toggle_running,
                bg=start_bg,
                text_color=theme.TEXT_ON_ACCENT,
            ),
            Button((24, 870, w - 48, 70), "Reiniciar", self._reset, accent=theme.BLUE),
        ]

    def _go_back(self):
        self.screen_manager.pop()

    def _start_label(self):
        return "Pausar" if self.running else "Iniciar"

    def _inc_focus(self):
        if self.running:
            return
        self.focus_minutes = min(90, self.focus_minutes + FOCUS_STEP)
        if self.phase == "focus":
            self.remaining = self.focus_minutes * 60
        self._build_buttons()

    def _dec_focus(self):
        if self.running:
            return
        self.focus_minutes = max(5, self.focus_minutes - FOCUS_STEP)
        if self.phase == "focus":
            self.remaining = self.focus_minutes * 60
        self._build_buttons()

    def _inc_break(self):
        if self.running:
            return
        self.break_minutes = min(30, self.break_minutes + BREAK_STEP)
        if self.phase == "break":
            self.remaining = self.break_minutes * 60
        self._build_buttons()

    def _dec_break(self):
        if self.running:
            return
        self.break_minutes = max(1, self.break_minutes - BREAK_STEP)
        if self.phase == "break":
            self.remaining = self.break_minutes * 60
        self._build_buttons()

    def _toggle_running(self):
        self.running = not self.running
        self._build_buttons()

    def _reset(self):
        self.running = False
        self.phase = "focus"
        self.remaining = self.focus_minutes * 60
        self._build_buttons()

    def on_tap(self, pos):
        for button in self.buttons:
            if button.handle_tap(pos):
                return

    def update(self, dt):
        if not self.running:
            return
        self.remaining -= dt
        if self.remaining <= 0:
            self._switch_phase()

    def _switch_phase(self):
        self.phase = "break" if self.phase == "focus" else "focus"
        minutes = self.break_minutes if self.phase == "break" else self.focus_minutes
        self.remaining = minutes * 60

    def draw(self, surface):
        surface.fill(theme.BG)
        w = surface.get_width()
        accent = theme.GOLD if self.phase == "focus" else theme.GREEN

        pygame.draw.rect(surface, theme.SURFACE, CARD_RECT, border_radius=28)
        pygame.draw.rect(surface, accent, CARD_RECT, width=4, border_radius=28)

        phase_label = "ENFOQUE" if self.phase == "focus" else "DESCANSO"
        phase_surf = theme.FONT_TITLE.render(phase_label, True, accent)
        surface.blit(phase_surf, phase_surf.get_rect(center=(w // 2, CARD_RECT.top + 60)))

        minutes = max(0, int(self.remaining) // 60)
        seconds = max(0, int(self.remaining) % 60)
        time_surf = theme.FONT_TIMER_XL.render(f"{minutes:02d}:{seconds:02d}", True, theme.TEXT)
        surface.blit(time_surf, time_surf.get_rect(center=(w // 2, CARD_RECT.centery + 30)))

        focus_label = theme.FONT_BODY.render(f"Enfoque: {self.focus_minutes} min", True, theme.TEXT)
        surface.blit(focus_label, focus_label.get_rect(center=(w // 2, 595)))

        break_label = theme.FONT_BODY.render(f"Descanso: {self.break_minutes} min", True, theme.TEXT)
        surface.blit(break_label, break_label.get_rect(center=(w // 2, 685)))

        for button in self.buttons:
            button.draw(surface)
