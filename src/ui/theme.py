import pygame

pygame.font.init()

BG = (18, 18, 20)
SURFACE = (30, 30, 34)
PRIMARY = (78, 168, 222)
TEXT = (235, 235, 240)
TEXT_MUTED = (150, 150, 158)

FONT_PATH = None  # usa la fuente por defecto de pygame hasta que agreguemos una custom en assets/fonts

FONT_TIMER = pygame.font.Font(FONT_PATH, 64)
FONT_TITLE = pygame.font.Font(FONT_PATH, 36)
FONT_BODY = pygame.font.Font(FONT_PATH, 26)
FONT_SMALL = pygame.font.Font(FONT_PATH, 20)
