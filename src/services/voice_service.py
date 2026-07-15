from core import config
from services import home_assistant_service, tts_service


class VoiceError(Exception):
    pass


def _output():
    return config.get("voice", "output", default="pi")


def speak(text):
    if _output() == "alexa":
        try:
            home_assistant_service.speak_on_alexa(text)
        except home_assistant_service.HomeAssistantError as exc:
            raise VoiceError(str(exc)) from exc
    else:
        try:
            tts_service.speak(text)
        except tts_service.TTSError as exc:
            raise VoiceError(str(exc)) from exc


def stop():
    # No hay forma sencilla de cortar a Alexa a mitad de frase via esta integracion.
    if _output() != "alexa":
        tts_service.stop()
