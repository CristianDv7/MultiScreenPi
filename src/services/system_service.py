import socket


def get_local_ip():
    """IP de salida de la Pi en la red local. No envia datos, solo abre un socket UDP."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        finally:
            s.close()
    except OSError:
        return None
