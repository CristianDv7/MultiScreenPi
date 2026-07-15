import subprocess

from core import config

WPA_CONF = "/etc/wpa_supplicant/wpa_supplicant.conf"


class WifiError(Exception):
    pass


def _interface():
    return config.get("wifi", "interface", default="wlan0")


def get_current_ssid():
    # iwgetid (wireless-tools) puede no estar instalado en DietPi por defecto.
    try:
        result = subprocess.run(
            ["iwgetid", "-r"], capture_output=True, text=True, timeout=5, check=False
        )
        ssid = result.stdout.strip()
        if ssid:
            return ssid
    except FileNotFoundError:
        pass

    # Alternativa con "iw" (mas moderno, suele venir instalado).
    try:
        result = subprocess.run(
            ["iw", "dev", _interface(), "link"], capture_output=True, text=True, timeout=5, check=False
        )
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("SSID:"):
                return line.split("SSID:", 1)[1].strip()
    except FileNotFoundError:
        pass

    return None


def set_wifi(ssid, password):
    """Agrega una red WiFi nueva sin borrar las que ya existen en wpa_supplicant.conf.

    Se agrega en vez de reemplazar el archivo a proposito: si la red nueva no
    conecta (typo, contrasena mala, etc.) las redes anteriores que si
    funcionaban siguen disponibles y el dispositivo no se queda sin poder
    reconectar solo.
    """
    ssid = (ssid or "").strip()
    if not ssid:
        raise WifiError("El SSID no puede estar vacio")
    if not password:
        raise WifiError("La contrasena no puede estar vacia")

    try:
        result = subprocess.run(
            ["wpa_passphrase", ssid, password],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except FileNotFoundError as exc:
        raise WifiError("wpa_passphrase no esta instalado") from exc

    if result.returncode != 0:
        raise WifiError(result.stderr.strip() or "wpa_passphrase fallo")

    # wpa_passphrase agrega un comentario con la contrasena en texto plano, lo quitamos.
    lines = [line for line in result.stdout.splitlines() if not line.strip().startswith("#psk=")]
    network_block = "\n".join(lines) + "\n"

    try:
        with open(WPA_CONF, "a", encoding="utf-8") as f:
            f.write("\n" + network_block)
    except OSError as exc:
        raise WifiError(f"No se pudo escribir {WPA_CONF}: {exc}") from exc

    try:
        subprocess.run(
            ["wpa_cli", "-i", _interface(), "reconfigure"],
            check=True,
            timeout=10,
            capture_output=True,
            text=True,
        )
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        raise WifiError(f"Red guardada pero no se pudo reconfigurar: {exc}") from exc
