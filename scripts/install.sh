#!/usr/bin/env bash
# Instalador para MultiScreenPi en una Raspberry Pi (DietPi) nueva.
#
# Uso (parado dentro de la carpeta del repo ya clonado):
#   bash scripts/install.sh
#
# Es seguro correrlo varias veces (no duplica lineas de config ni pisa
# tu config.yaml si ya existe).
#
# Antes de esto: flashea DietPi con Raspberry Pi Imager (SSH + WiFi
# configurados), entra por SSH, y clona el repo:
#   git clone git@github.com:CristianDv7/MultiScreenPi.git
#   cd MultiScreenPi

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -f /boot/firmware/config.txt ]; then
    BOOT_CONFIG=/boot/firmware/config.txt
else
    BOOT_CONFIG=/boot/config.txt
fi

echo "=== MultiScreenPi: instalacion ==="
echo "Repo: $REPO_DIR"
echo "Config de arranque: $BOOT_CONFIG"
echo

echo "--- 1/5: Paquetes del sistema ---"
sudo apt update
sudo apt install -y \
    git python3-pygame python3-venv python3-full \
    libgl1-mesa-dri libegl1 libgles2 libgbm1 mesa-utils \
    espeak-ng mpg123 curl iw alsa-utils

echo
echo "--- 2/5: Pantalla (KMS), GPU y audio ---"

if grep -q "^#dtoverlay=vc4-kms-v3d" "$BOOT_CONFIG"; then
    sudo sed -i 's/^#dtoverlay=vc4-kms-v3d.*/dtoverlay=vc4-kms-v3d/' "$BOOT_CONFIG"
    echo "KMS habilitado (linea existente descomentada)."
elif ! grep -q "^dtoverlay=vc4-kms-v3d" "$BOOT_CONFIG"; then
    echo "dtoverlay=vc4-kms-v3d" | sudo tee -a "$BOOT_CONFIG" > /dev/null
    echo "KMS habilitado (linea agregada)."
else
    echo "KMS ya estaba habilitado."
fi

if grep -q "^gpu_mem_512=16" "$BOOT_CONFIG"; then
    sudo sed -i 's/^gpu_mem_512=16/gpu_mem_512=64/' "$BOOT_CONFIG"
    echo "gpu_mem_512 ajustado a 64."
elif ! grep -q "^gpu_mem" "$BOOT_CONFIG"; then
    echo "gpu_mem=64" | sudo tee -a "$BOOT_CONFIG" > /dev/null
    echo "gpu_mem agregado (64)."
else
    echo "gpu_mem ya estaba configurado, no se toca."
fi

if ! grep -q "^dtparam=audio=on" "$BOOT_CONFIG"; then
    echo "dtparam=audio=on" | sudo tee -a "$BOOT_CONFIG" > /dev/null
    echo "Audio habilitado."
else
    echo "Audio ya estaba habilitado."
fi

echo
echo "--- 3/5: Entorno Python ---"
if [ ! -d "$HOME/venv" ]; then
    python3 -m venv --system-site-packages "$HOME/venv"
    echo "Entorno virtual creado en $HOME/venv"
else
    echo "Entorno virtual ya existe en $HOME/venv"
fi

# shellcheck disable=SC1091
source "$HOME/venv/bin/activate"
pip install --upgrade pip
pip install -r "$REPO_DIR/requirements.txt"
deactivate

echo
echo "--- 4/5: Archivo de configuracion ---"
if [ ! -f "$REPO_DIR/config/config.yaml" ]; then
    cp "$REPO_DIR/config/config.example.yaml" "$REPO_DIR/config/config.yaml"
    echo "Se creo config/config.yaml a partir del ejemplo."
    echo "IMPORTANTE: editalo con tus datos reales antes de usar la app:"
    echo "  nano $REPO_DIR/config/config.yaml"
else
    echo "config/config.yaml ya existe, no se toca."
fi

echo
echo "--- 5/5: Servicio systemd ---"
sudo cp "$REPO_DIR/scripts/multiscreenpi.service" /etc/systemd/system/
sudo systemctl daemon-reload
echo "Servicio instalado (todavia no activado)."

echo
echo "=== Listo. Proximos pasos ==="
echo "1. Reinicia para que los cambios de pantalla/audio tomen efecto:"
echo "     sudo reboot"
echo "2. Edita config/config.yaml con tus claves/tokens reales."
echo "3. Prueba la app a mano antes de dejarla en automatico:"
echo "     cd $REPO_DIR/src"
echo "     source ~/venv/bin/activate"
echo "     export SDL_VIDEODRIVER=kmsdrm SDL_AUDIODRIVER=dummy"
echo "     python3 main.py"
echo "4. Cuando funcione bien, activa el arranque automatico:"
echo "     sudo systemctl enable --now multiscreenpi.service"
