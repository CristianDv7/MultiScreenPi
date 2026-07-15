import subprocess

_process = None


class TTSError(Exception):
    pass


def speak(text, lang="es"):
    stop()
    if not text:
        return

    global _process
    # "..." al inicio absorbe el recorte de los primeros milisegundos que hace
    # espeak-ng/ALSA en esta placa mientras el dispositivo de audio despierta,
    # asi no se pierde la primera palabra real del texto.
    padded = f"... {text}"
    try:
        _process = subprocess.Popen(["espeak-ng", "-v", lang, "-s", "155", padded])
    except FileNotFoundError as exc:
        raise TTSError("espeak-ng no esta instalado") from exc


def stop():
    global _process
    if _process is not None and _process.poll() is None:
        _process.terminate()
    _process = None


def is_speaking():
    return _process is not None and _process.poll() is None
