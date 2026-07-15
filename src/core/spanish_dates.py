import datetime

DIAS = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def weekday_name(dt):
    return DIAS[dt.weekday()]


def month_name(dt):
    return MESES[dt.month - 1]


def today_label():
    now = datetime.datetime.now()
    return f"{weekday_name(now)} {now.day} de {month_name(now)} de {now.year}"


def time_phrase(dt=None):
    """Frase natural para anunciar la hora por voz, ej. 'Son las 3 y 20 de la tarde'."""
    dt = dt or datetime.datetime.now()
    hour12 = dt.hour % 12
    if hour12 == 0:
        hour12 = 12

    if dt.hour < 12:
        periodo = "de la manana"
    elif dt.hour < 19:
        periodo = "de la tarde"
    else:
        periodo = "de la noche"

    if dt.minute == 0:
        return f"Son las {hour12} {periodo}"
    return f"Son las {hour12} y {dt.minute} {periodo}"
