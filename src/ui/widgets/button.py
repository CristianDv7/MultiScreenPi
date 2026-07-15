import pygame

from ui import theme


class Button:
    def __init__(self, rect, label, on_tap, subtitle=None):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.subtitle = subtitle
        self.on_tap = on_tap

    def contains(self, pos):
        return self.rect.collidepoint(pos)

    def handle_tap(self, pos):
        if self.contains(pos) and self.on_tap:
            self.on_tap()
            return True
        return False

    def draw(self, surface):
        pygame.draw.rect(surface, theme.SURFACE, self.rect, border_radius=16)

        label_y = self.rect.centery - (12 if self.subtitle else 0)
        label_surf = theme.FONT_BODY.render(self.label, True, theme.TEXT)
        label_rect = label_surf.get_rect(midleft=(self.rect.left + 24, label_y))
        surface.blit(label_surf, label_rect)

        if self.subtitle:
            sub_surf = theme.FONT_SMALL.render(self.subtitle, True, theme.TEXT_MUTED)
            sub_rect = sub_surf.get_rect(midleft=(self.rect.left + 24, self.rect.centery + 16))
            surface.blit(sub_surf, sub_rect)
