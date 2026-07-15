"""Cambiar de escritorio virtual de Windows simulando Ctrl+Win+Flecha.

Windows no tiene una API oficial para "ir al escritorio N" directamente,
asi que simulamos el atajo de teclado nativo. Con exactamente 2 escritorios
esto funciona como un salto directo: "izquierda" no hace nada si ya estas
en el primero, y "derecha" no hace nada si ya estas en el segundo.
"""

import time
from ctypes import windll

VK_LWIN = 0x5B
VK_CONTROL = 0x11
VK_LEFT = 0x25
VK_RIGHT = 0x27
KEYEVENTF_KEYUP = 0x0002

user32 = windll.user32


def _press(vk):
    user32.keybd_event(vk, 0, 0, 0)


def _release(vk):
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)


def switch_desktop(direction):
    arrow = VK_RIGHT if direction == "right" else VK_LEFT
    _press(VK_CONTROL)
    _press(VK_LWIN)
    _press(arrow)
    time.sleep(0.05)
    _release(arrow)
    _release(VK_LWIN)
    _release(VK_CONTROL)
