import pygame

DOWN = "down"
MOVE = "move"
UP = "up"

MOUSE_ID = "mouse"


def normalize_event(event, transform_pos):
    """Convierte un evento crudo de pygame (mouse o touch) en (DOWN/MOVE/UP, pos_logico, id_de_dedo).

    El Zero-DISP-7A expone el touch por USB; segun la version de SDL puede llegar
    como eventos de mouse (mas probable bajo el driver KMSDRM) o como FINGER*.
    Soportamos ambos para no depender de cual use tu build de pygame. El id de
    dedo (finger_id, o "mouse" para eventos de mouse) permite distinguir varios
    toques simultaneos para gestos tipo pellizcar-para-zoom.
    """
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        return DOWN, transform_pos(event.pos), MOUSE_ID
    if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        return UP, transform_pos(event.pos), MOUSE_ID
    if event.type == pygame.MOUSEMOTION and event.buttons[0]:
        return MOVE, transform_pos(event.pos), MOUSE_ID

    if event.type == pygame.FINGERDOWN:
        return DOWN, transform_pos(_finger_pos(event)), event.finger_id
    if event.type == pygame.FINGERUP:
        return UP, transform_pos(_finger_pos(event)), event.finger_id
    if event.type == pygame.FINGERMOTION:
        return MOVE, transform_pos(_finger_pos(event)), event.finger_id

    return None, None, None


def _finger_pos(event):
    surface = pygame.display.get_surface()
    w, h = surface.get_size()
    return (event.x * w, event.y * h)
