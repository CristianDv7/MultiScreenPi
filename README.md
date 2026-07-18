# MultiScreenPi

Panel multimedia para Raspberry Pi Zero 2W con pantalla táctil Waveshare
Zero-DISP-7A: Pomodoro, noticias, control de Home Assistant, clima, cámaras,
control remoto de PC y más, con anuncios por voz vía Alexa.

## Instalar en una Pi nueva

1. Flashea DietPi con Raspberry Pi Imager (configura SSH y WiFi en las
   opciones avanzadas antes de grabar).
2. Entra por SSH y completa el asistente de primer arranque de DietPi
   (elige **OpenSSH** como servidor SSH, deja Desktop en `None`).
3. Clona el repo:
   ```bash
   git clone git@github.com:CristianDv7/MultiScreenPi.git
   cd MultiScreenPi
   ```
4. Corre el instalador (paquetes, KMS/GPU, audio, entorno Python, servicio systemd):
   ```bash
   bash scripts/install.sh
   ```
5. Reinicia para que los cambios de pantalla/audio tomen efecto:
   ```bash
   sudo reboot
   ```
6. Edita `config/config.yaml` (se creó a partir de `config.example.yaml`)
   con tus claves y tokens reales — este archivo nunca se sube a git.
7. Prueba la app a mano antes de dejarla en automático:
   ```bash
   cd src
   source ~/venv/bin/activate
   export SDL_VIDEODRIVER=kmsdrm SDL_AUDIODRIVER=dummy
   python3 main.py
   ```
8. Cuando funcione bien, activa el arranque automático:
   ```bash
   sudo systemctl enable --now multiscreenpi.service
   ```

## Estructura

- `src/` — código de la app (Python + pygame)
- `config/config.example.yaml` — plantilla de configuración sin secretos
- `scripts/` — instalador y unit de systemd
- `desktop-agent/` — agente que corre en tu PC de escritorio para la sección "Mi PC" (abrir apps/sitios, cambiar audio, escritorios virtuales)
- `assets/slideshow/` — pon aquí fotos para el slideshow del reloj de reposo
