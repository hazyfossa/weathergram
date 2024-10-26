from abc import ABC, abstractmethod
from enum import Enum, auto

from attrs import define
from loguru import logger

from src.njct import implements, provider

from .common import API
from .location import Location


class WeatherType(Enum):
    sunny = auto()
    cloudy = auto()
    raining = auto()
    snow = auto()


@define
class Weather:
    temperature: int
    type: WeatherType
    humidity: int
    wind_speed: int


@provider()
class WeatherProvider(ABC, API):
    @abstractmethod
    def query(self, location: Location) -> Weather: ...


@implements(WeatherProvider)
class OpenMeteo(WeatherProvider.inject):
    url = "https://api.open-meteo.com/"

    def query(self, location):
        params = {
            "latitude": location[0],
            "longitude": location[1],
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "weather_code",
                "wind_speed_10m",
            ],
        }
        response = self.client.get("/v1/forecast", params=params).content
        data = self.json.loads(response)["current"]

        weather_code = int(data["weather_code"])  # WMO Weather interpretation code (WW)

        if weather_code == 0:
            weather_type = WeatherType.sunny
        elif weather_code in [*range(1, 4), 45, 48]:
            weather_type = WeatherType.cloudy
        elif weather_code in [*range(51, 68), *range(80, 83), 95, 96, 99]:
            weather_type = WeatherType.raining
        elif weather_code in [*range(71, 78), 85, 86]:
            weather_type = WeatherType.snow
        else:
            logger.warning("Got unknown weather code from OpenMeteo API: {}", weather_code)
            weather_type = WeatherType.sunny

        return Weather(
            temperature=data["temperature_2m"],
            type=weather_type,
            humidity=data["relative_humidity_2m"],
            wind_speed=data["wind_speed_10m"],
        )
