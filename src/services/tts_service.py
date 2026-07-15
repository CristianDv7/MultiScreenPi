import os
import subprocess
import tempfile

from gtts import gTTS

_process = None
_tmp_path = None


class TTSError(Exception):
    pass


def speak(text, lang="es"):
    """Genera el audio con gTTS (requiere internet) y lo reproduce con mpg123.

    Bloquea mientras genera/descarga el audio, por eso quien la llame desde
    la UI debe hacerlo en un hilo aparte para no congelar la pantalla.
    """
    stop()
    if not text:
        return

    global _process, _tmp_path
    try:
        fd, path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        gTTS(text=text, lang=lang).save(path)
        _tmp_path = path
    except Exception as exc:
        raise TTSError(f"No se pudo generar el audio: {exc}") from exc

    try:
        _process = subprocess.Popen(["mpg123", "-q", path])
    except FileNotFoundError as exc:
        raise TTSError("mpg123 no esta instalado (sudo apt install mpg123)") from exc


def stop():
    global _process, _tmp_path
    if _process is not None and _process.poll() is None:
        _process.terminate()
    _process = None

    if _tmp_path and os.path.exists(_tmp_path):
        try:
            os.remove(_tmp_path)
        except OSError:
            pass
    _tmp_path = None


def is_speaking():
    return _process is not None and _process.poll() is None
