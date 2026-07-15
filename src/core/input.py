import pygame

TAP = "tap"


def normalize_event(event, transform_pos):
    """Convierte un evento crudo de pygame (mouse o touch) en (TAP, pos_logico) o (None, None).

    El Zero-DISP-7A expone el touch por USB; segun la version de SDL puede llegar
    como MOUSEBUTTONDOWN (mas probable bajo el driver KMSDRM) o como FINGERDOWN.
    Soportamos ambos para no depender de cual use tu build de pygame.
    """
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        return TAP, transform_pos(event.pos)

    if event.type == pygame.FINGERDOWN:
        surface = pygame.display.get_surface()
        phys_w, phys_h = surface.get_size()
        pos = (event.x * phys_w, event.y * phys_h)
        return TAP, transform_pos(pos)

    return None, None
