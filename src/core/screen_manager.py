class Screen:
    def on_enter(self):
        pass

    def on_exit(self):
        pass

    def handle_event(self, event):
        pass

    def on_tap(self, pos):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass


class ScreenManager:
    def __init__(self):
        self._stack = []

    @property
    def current(self):
        return self._stack[-1] if self._stack else None

    def push(self, screen: Screen):
        if self.current:
            self.current.on_exit()
        self._stack.append(screen)
        screen.on_enter()

    def pop(self):
        if not self._stack:
            return
        self._stack.pop().on_exit()
        if self.current:
            self.current.on_enter()

    def replace(self, screen: Screen):
        if self._stack:
            self._stack.pop().on_exit()
        self._stack.append(screen)
        screen.on_enter()

    def handle_event(self, event):
        if self.current:
            self.current.handle_event(event)

    def handle_tap(self, pos):
        if self.current:
            self.current.on_tap(pos)

    def update(self, dt):
        if self.current:
            self.current.update(dt)

    def draw(self, surface):
        if self.current:
            self.current.draw(surface)
