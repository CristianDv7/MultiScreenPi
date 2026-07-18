"""Diagnostico: confirma si la pantalla entrega multitouch real (varios
finger_id distintos al mismo tiempo) o si solo maneja un toque a la vez.

Uso en la Pi:
    cd MultiScreenPi/src
    export SDL_VIDEODRIVER=kmsdrm SDL_AUDIODRIVER=dummy
    python3 multitouch_test.py

Toca la pantalla con UN dedo, mira la terminal. Despues toca con DOS
dedos AL MISMO TIEMPO (como para pellizcar) y mira si aparecen dos
finger_id distintos o solo uno. Ctrl+C para salir.
"""

import pygame

pygame.init()
pygame.display.set_mode((600, 1024), pygame.FULLSCREEN)
pygame.mouse.set_visible(False)

print("Escuchando eventos tactiles. Toca con 1 dedo, luego con 2 al mismo tiempo.", flush=True)

active_fingers = set()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
        elif event.type == pygame.FINGERDOWN:
            active_fingers.add(event.finger_id)
            print(f"FINGERDOWN finger_id={event.finger_id} x={event.x:.2f} y={event.y:.2f} "
                  f"-- dedos activos ahora: {len(active_fingers)}", flush=True)
        elif event.type == pygame.FINGERUP:
            active_fingers.discard(event.finger_id)
            print(f"FINGERUP   finger_id={event.finger_id} -- dedos activos ahora: {len(active_fingers)}", flush=True)
        elif event.type == pygame.FINGERMOTION:
            pass  # silenciado para no inundar la terminal
        elif event.type == pygame.MOUSEBUTTONDOWN:
            print(f"MOUSEBUTTONDOWN pos={event.pos} (la pantalla esta mandando eventos de mouse, no de touch)", flush=True)
        elif event.type == pygame.MOUSEBUTTONUP:
            print("MOUSEBUTTONUP", flush=True)

pygame.quit()
