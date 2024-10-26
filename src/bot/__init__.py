from attrs import define
from loguru import logger
from telethon import TelegramClient

from .framework import command, init_client, Message
from .interval import IntervalComponent
from .location import LocationComponent
from .user_flow import UserFlowComponent, User
from .weather import WeatherComponent


async def notify(client: TelegramClient):
    bot_user = await client.get_me()
    logger.info("Running as bot [{}]", bot_user.id)  # type: ignore # typing bug in telethon


@define
class Bot(UserFlowComponent, LocationComponent, IntervalComponent, WeatherComponent):
    def __attrs_post_init__(self):
        self.client = init_client(self, self.client, self.with_user)
        self.client.loop.create_task(notify(self.client))

    @command
    async def start(self, user: User):
        await self.client.send_message(
            user.id,
            """Вы уже зарегистрированы :)                             
Изменить местоположение - /set_location
Изменить интервал - /set_interval
Удалить аккаунт - /unregister""",
        )


__all__ = ["Bot"]
