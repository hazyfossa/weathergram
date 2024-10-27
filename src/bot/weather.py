from attrs import define

from src.bot.framework import Component, User, command
from src.components.location import Location
from src.components.weather import Weather, WeatherProvider, WeatherType


def type_line(type: WeatherType):
    match type:
        case WeatherType.sunny:
            return "[☀] Солнечно"
        case WeatherType.cloudy:
            return "[☁] Облачно"
        case WeatherType.raining:
            return "[🌧] Дождь"
        case WeatherType.snow:
            return "[🌨] Снег"


def weather_ui(weather: Weather) -> str:
    return f"""{type_line(weather.type)}
[🌡] Температура: {weather.temperature} C°
[💧] Влажность: {weather.humidity}%
[💨] Скорость ветра: {weather.wind_speed} м/с"""


@define
class WeatherComponent(Component):
    weather_provider: WeatherProvider.inject

    @command
    async def weather(self, user: User):
        await self.send_weather(user.id, (user.latitude, user.longitude))

    async def send_weather(
        self, user_id: int, location: Location
    ):  # This is a separate function to allow being passed as a scheduler task.
        weather = self.weather_provider.query(location)
        await self.client.send_message(user_id, weather_ui(weather))
