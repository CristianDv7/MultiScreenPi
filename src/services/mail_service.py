import email
import imaplib
from email.header import decode_header

from core import config


class MailError(Exception):
    pass


def _decode(value):
    if not value:
        return ""
    parts = decode_header(value)
    decoded = ""
    for text, encoding in parts:
        if isinstance(text, bytes):
            decoded += text.decode(encoding or "utf-8", errors="ignore")
        else:
            decoded += text
    return decoded


def fetch_unread(limit=5):
    host = config.get("mail", "imap_host", default="imap.gmail.com")
    port = config.get("mail", "imap_port", default=993)
    username = config.get("mail", "username", default="")
    password = config.get("mail", "app_password", default="")

    if not username or not password or "REEMPLAZA" in password:
        raise MailError("Configura mail.username y mail.app_password en config.yaml")

    try:
        conn = imaplib.IMAP4_SSL(host, port)
    except OSError as exc:
        raise MailError(f"No se pudo conectar a {host}: {exc}") from exc

    try:
        conn.login(username, password)
        conn.select("INBOX")

        status, data = conn.search(None, "UNSEEN")
        if status != "OK":
            raise MailError("No se pudo buscar correos no leidos")

        ids = data[0].split()
        unread_count = len(ids)
        recent_ids = list(reversed(ids[-limit:]))

        messages = []
        for msg_id in recent_ids:
            status, msg_data = conn.fetch(msg_id, "(RFC822.HEADER)")
            if status != "OK" or not msg_data or not msg_data[0]:
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            messages.append({"subject": _decode(msg.get("Subject")), "from": _decode(msg.get("From"))})

        return {"unread_count": unread_count, "messages": messages}
    except imaplib.IMAP4.error as exc:
        raise MailError(str(exc)) from exc
    finally:
        try:
            conn.logout()
        except OSError:
            pass
