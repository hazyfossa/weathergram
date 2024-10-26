import asyncio
import sys

from loguru import logger
from telethon import TelegramClient

from src.config import settings
from src.bot import Bot

from .components.event_loop import EventLoop
from .components.json_parser import Json
from .components.location import LocationProvider
from .components.scheduler import Scheduler
from .components.weather import WeatherProvider
from .database.interface import Database

if __name__ != "__main__":
    raise RuntimeError("This should be the entrypoint for the app.")


loop = EventLoop().new_event_loop()
asyncio.set_event_loop(loop)


database = Database(settings.database)

client = TelegramClient(
    database.session_store,
    settings.api_id,
    settings.api_hash,
).start(bot_token=settings.bot_token)

json = Json()
scheduler = Scheduler()

loop.create_task(scheduler.run())

bot = Bot(
    client,
    WeatherProvider(json),
    scheduler,
    LocationProvider(json),
    database.user_store,
)

try:
    bot.client.run_until_disconnected()
except KeyboardInterrupt:
    bot.client.disconnect()
