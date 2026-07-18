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

## Panel web de administración

Además de la pantalla táctil, hay un panel web (`http://IP_DE_LA_PI:8080`)
para administrar noticias, cámaras, atajos de PC, qué luces de Home
Assistant se muestran, y las fotos del slideshow — más cómodo que editar
`config.yaml` a mano por SSH cuando es una lista larga o subir imágenes.

Para activarlo, pon una contraseña en `config.yaml`:
```yaml
web:
  password: "tu_contrasena"
  port: 8080
```
Arranca solo (en un hilo dentro de la misma app) la próxima vez que
reinicies el servicio. Usuario `admin`, la contraseña que hayas puesto.
Los cambios se reflejan de inmediato en el panel, sin reiniciar nada.

## Agente de escritorio (para la sección "Mi PC")

Corre en tu PC de escritorio (Windows) para que el panel pueda abrir sitios
web/apps, cambiar el audio, y moverte entre escritorios virtuales.

1. En `desktop-agent/`, corre el instalador:
   ```powershell
   powershell -ExecutionPolicy Bypass -File install.ps1
   ```
   Instala las dependencias (`pycaw`, `comtypes`), crea `agent_config.json`
   a partir del ejemplo, y configura el autoarranque con Windows.
2. Edita `agent_config.json` con un token secreto y las rutas de tus apps
   (`.exe` o `.lnk`) — este archivo nunca se sube a git.
3. Copia esa URL (`http://IP_DE_TU_PC:5566`) y el token al panel web de la
   Pi, sección **Secretos > Mi PC**.

## Estructura

- `src/` — código de la app (Python + pygame)
- `src/web/` — panel web de administración (Flask)
- `config/config.example.yaml` — plantilla de configuración sin secretos
- `scripts/` — instalador y unit de systemd
- `desktop-agent/` — agente que corre en tu PC de escritorio para la sección "Mi PC" (abrir apps/sitios, cambiar audio, escritorios virtuales)
- `assets/slideshow/` — pon aquí fotos para el slideshow del reloj de reposo (o súbelas desde el panel web)
