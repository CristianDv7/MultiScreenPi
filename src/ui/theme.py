import pygame

pygame.font.init()

BG = (255, 255, 255)
SURFACE = (238, 240, 253)  # tinte lavanda muy suave para tarjetas sobre blanco

# Paleta de UbicateAPP
INDIGO = (63, 81, 181)
LAVENDER = (172, 180, 251)
GOLD = (255, 179, 0)
GREEN = (76, 175, 80)
WHATSAPP_GREEN = (37, 211, 102)
FACEBOOK_BLUE = (24, 119, 242)
INSTAGRAM_PINK = (225, 48, 108)
GRAY_NEUTRAL = (184, 181, 181)
DANGER = (211, 47, 47)

BLUE = INDIGO  # alias usado ya en varias pantallas

PRIMARY = INDIGO
SECONDARY = LAVENDER

TEXT = (28, 28, 32)
TEXT_MUTED = (110, 110, 120)
TEXT_ON_ACCENT = (12, 12, 12)

FONT_PATH = None  # usa la fuente por defecto de pygame hasta que agreguemos una custom en assets/fonts

FONT_TIMER_XL = pygame.font.Font(FONT_PATH, 118)
FONT_TIMER = pygame.font.Font(FONT_PATH, 64)
FONT_TITLE = pygame.font.Font(FONT_PATH, 36)
FONT_BODY = pygame.font.Font(FONT_PATH, 26)
FONT_SMALL = pygame.font.Font(FONT_PATH, 20)
