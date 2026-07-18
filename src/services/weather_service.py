import datetime
import time

import requests

from core import config
from core.spanish_dates import weekday_name

TIMEOUT = 8
DEFAULT_CACHE_MINUTES = 15

_cache = {"current": None, "current_at": 0.0, "forecast": None, "forecast_at": 0.0}


def _cache_ttl():
    minutes = config.get("weather", "cache_minutes", default=DEFAULT_CACHE_MINUTES)
    return max(0, minutes) * 60


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


def fetch_current(force=False):
    now = time.monotonic()
    if not force and _cache["current"] and now - _cache["current_at"] < _cache_ttl():
        return _cache["current"]

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

    result = {
        "city": data.get("name", _location()),
        "temp": round(main.get("temp", 0)),
        "feels_like": round(main.get("feels_like", 0)),
        "humidity": main.get("humidity"),
        "description": weather.get("description", "").capitalize(),
    }
    _cache["current"] = result
    _cache["current_at"] = now
    return result


def fetch_hourly_forecast(limit=8, force=False):
    """Pronostico en bloques de 3 horas (endpoint gratuito /forecast de OpenWeatherMap)."""
    now = time.monotonic()
    if not force and _cache["forecast"] and now - _cache["forecast_at"] < _cache_ttl():
        return _cache["forecast"][:limit]

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
    # ordenado, pero asi nos aseguramos que nunca salga desordenado en pantalla.
    items = sorted(data.get("list", []), key=lambda item: item.get("dt", 0))

    # dt/dt_txt vienen en UTC; hay que corregir con el offset de la ciudad
    # (en segundos) para mostrar la hora local real, si no los horarios salen
    # desfasados varias horas segun la zona horaria del usuario.
    tz_offset = data.get("city", {}).get("timezone", 0)

    entries = []
    for item in items:
        dt = item.get("dt", 0)
        local_dt = datetime.datetime.utcfromtimestamp(dt + tz_offset)
        time_label = f"{weekday_name(local_dt)} {local_dt.day}/{local_dt.month} {local_dt.strftime('%H:%M')}"

        weather = (item.get("weather") or [{}])[0]
        entries.append(
            {
                "time": time_label,
                "temp": round(item.get("main", {}).get("temp", 0)),
                "description": weather.get("description", "").capitalize(),
            }
        )

    _cache["forecast"] = entries
    _cache["forecast_at"] = now
    return entries[:limit]
