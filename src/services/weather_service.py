import requests

from core import config

TIMEOUT = 8


class WeatherError(Exception):
    pass


def fetch_current():
    api_key = config.get("weather", "api_key", default="")
    location = config.get("weather", "location", default="")

    if not api_key or "REEMPLAZA" in api_key:
        raise WeatherError("Configura weather.api_key en config.yaml")
    if not location:
        raise WeatherError("Configura weather.location en config.yaml")

    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": location, "appid": api_key, "units": "metric", "lang": "es"},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise WeatherError(str(exc)) from exc

    weather = (data.get("weather") or [{}])[0]
    main = data.get("main", {})

    return {
        "city": data.get("name", location),
        "temp": round(main.get("temp", 0)),
        "feels_like": round(main.get("feels_like", 0)),
        "humidity": main.get("humidity"),
        "description": weather.get("description", "").capitalize(),
    }
