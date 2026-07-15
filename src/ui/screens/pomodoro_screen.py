from core.screen_manager import Screen
from ui import theme
from ui.widgets.button import Button

FOCUS_STEP = 5
BREAK_STEP = 1


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
        self.buttons = [
            Button((24, 24, 130, 56), "< Volver", self._go_back),
            Button((24, 300, 56, 56), "-", self._dec_focus),
            Button((w - 24 - 56, 300, 56, 56), "+", self._inc_focus),
            Button((24, 380, 56, 56), "-", self._dec_break),
            Button((w - 24 - 56, 380, 56, 56), "+", self._inc_break),
            Button((24, 480, w - 48, 90), self._start_label(), self._toggle_running),
            Button((24, 590, w - 48, 70), "Reiniciar", self._reset),
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

        title_surf = theme.FONT_TITLE.render("Pomodoro", True, theme.TEXT)
        surface.blit(title_surf, (24, 100))

        phase_label = "Enfoque" if self.phase == "focus" else "Descanso"
        phase_surf = theme.FONT_BODY.render(phase_label, True, theme.PRIMARY)
        surface.blit(phase_surf, phase_surf.get_rect(center=(w // 2, 190)))

        minutes = max(0, int(self.remaining) // 60)
        seconds = max(0, int(self.remaining) % 60)
        time_surf = theme.FONT_TIMER.render(f"{minutes:02d}:{seconds:02d}", True, theme.TEXT)
        surface.blit(time_surf, time_surf.get_rect(center=(w // 2, 245)))

        focus_label = theme.FONT_BODY.render(f"Enfoque: {self.focus_minutes} min", True, theme.TEXT)
        surface.blit(focus_label, focus_label.get_rect(center=(w // 2, 328)))

        break_label = theme.FONT_BODY.render(f"Descanso: {self.break_minutes} min", True, theme.TEXT)
        surface.blit(break_label, break_label.get_rect(center=(w // 2, 408)))

        for button in self.buttons:
            button.draw(surface)
