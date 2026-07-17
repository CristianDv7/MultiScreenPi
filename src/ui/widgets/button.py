import pygame

from ui import theme


class Button:
    def __init__(
        self,
        rect,
        label,
        on_tap,
        subtitle=None,
        accent=None,
        bg=None,
        text_color=None,
        font=None,
        centered=False,
    ):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.subtitle = subtitle
        self.on_tap = on_tap
        self.accent = accent  # color de franja lateral (para listas/menus)
        self.bg = bg  # color de fondo del boton completo (para acciones destacadas)
        self.text_color = text_color
        self.font = font or theme.FONT_BODY
        self.centered = centered

    def contains(self, pos):
        return self.rect.collidepoint(pos)

    def handle_tap(self, pos):
        if self.contains(pos) and self.on_tap:
            self.on_tap()
            return True
        return False

    def draw(self, surface):
        pygame.draw.rect(surface, self.bg or theme.SURFACE, self.rect, border_radius=16)

        text_x = self.rect.left + 24
        if self.accent:
            bar_rect = pygame.Rect(self.rect.left, self.rect.top, 6, self.rect.height)
            pygame.draw.rect(
                surface, self.accent, bar_rect, border_top_left_radius=16, border_bottom_left_radius=16
            )
            text_x += 10

        color = self.text_color or theme.TEXT
        label_surf = self.font.render(self.label, True, color)

        if self.centered:
            label_rect = label_surf.get_rect(center=self.rect.center)
        else:
            label_y = self.rect.centery - (12 if self.subtitle else 0)
            label_rect = label_surf.get_rect(midleft=(text_x, label_y))
        surface.blit(label_surf, label_rect)

        if self.subtitle:
            sub_surf = theme.FONT_SMALL.render(self.subtitle, True, theme.TEXT_MUTED)
            sub_rect = sub_surf.get_rect(midleft=(text_x, self.rect.centery + 16))
            surface.blit(sub_surf, sub_rect)


def back_button(x, y, on_tap, width=130, height=56):
    """Boton de 'volver' consistente para todas las pantallas."""
    return Button(
        (x, y, width, height),
        "< Volver",
        on_tap,
        bg=theme.INDIGO,
        text_color=(255, 255, 255),
        font=theme.FONT_SMALL,
        centered=True,
    )
