import requests

from core import config

TIMEOUT = 8


class WeatherError(Exception):
    pass


def _api_key():
    return config.get("weather", "api_key", default="")


def _location():
    return config.get("weather", "location", default="")


def _check_config():
    if not _api_key() or "REEMPLAZA" in _api_key():
        raise WeatherError("Configura weather.api_key en config.yaml")
    if not _location():
        raise WeatherError("Configura weather.location en config.yaml")


def fetch_current():
    _check_config()

    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": _location(), "appid": _api_key(), "units": "metric", "lang": "es"},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise WeatherError(str(exc)) from exc

    weather = (data.get("weather") or [{}])[0]
    main = data.get("main", {})

    return {
        "city": data.get("name", _location()),
        "temp": round(main.get("temp", 0)),
        "feels_like": round(main.get("feels_like", 0)),
        "humidity": main.get("humidity"),
        "description": weather.get("description", "").capitalize(),
    }


def fetch_hourly_forecast(limit=8):
    """Pronostico en bloques de 3 horas (endpoint gratuito /forecast de OpenWeatherMap)."""
    _check_config()

    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={"q": _location(), "appid": _api_key(), "units": "metric", "lang": "es"},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise WeatherError(str(exc)) from exc

    # Ordenamos explicitamente por timestamp: la API deberia devolverlo ya
    # ordenado, pero as segura que nunca salga desordenado en pantalla.
    items = sorted(data.get("list", []), key=lambda item: item.get("dt", 0))

    entries = []
    for item in items[:limit]:
        dt_txt = item.get("dt_txt", "")  # "2026-07-15 18:00:00"
        if " " in dt_txt:
            date_part, time_part = dt_txt.split(" ")
            year, month, day = date_part.split("-")
            time_label = f"{day}/{month} {time_part[:5]}"
        else:
            time_label = dt_txt
        weather = (item.get("weather") or [{}])[0]
        entries.append(
            {
                "time": time_label,
                "temp": round(item.get("main", {}).get("temp", 0)),
                "description": weather.get("description", "").capitalize(),
            }
        )

    return entries
