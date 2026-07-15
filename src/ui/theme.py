import pygame

pygame.font.init()

BG = (8, 8, 10)
SURFACE = (26, 26, 30)

# Acentos tomados de la paleta de UbicateAPP (dorado, verde, azul), sobre fondo negro.
GOLD = (255, 179, 0)
GREEN = (76, 175, 80)
BLUE = (63, 81, 181)

PRIMARY = GOLD
SECONDARY = GREEN
INFO = BLUE

TEXT = (245, 245, 247)
TEXT_MUTED = (160, 160, 168)
TEXT_ON_ACCENT = (12, 12, 12)

FONT_PATH = None  # usa la fuente por defecto de pygame hasta que agreguemos una custom en assets/fonts

FONT_TIMER_XL = pygame.font.Font(FONT_PATH, 118)
FONT_TIMER = pygame.font.Font(FONT_PATH, 64)
FONT_TITLE = pygame.font.Font(FONT_PATH, 36)
FONT_BODY = pygame.font.Font(FONT_PATH, 26)
FONT_SMALL = pygame.font.Font(FONT_PATH, 20)
