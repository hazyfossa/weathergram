from typing import Awaitable, Callable, Self

from attrs import define
from telethon import Button

from src.bot.framework import Message, command
from src.bot.interval import IntervalComponent
from src.bot.location import LocationComponent
from src.database.interface import UserStore
from src.database.schema import User


@define
class UserFlowComponent(LocationComponent, IntervalComponent):
    user_store: UserStore

    async def new_user(self, event: Message) -> User | None:
        user_id = event.chat_id
        assert isinstance(user_id, int)

        await self.client.send_message(user_id, "Добро пожаловать!")  # TODO

        location = await self.set_location_ui(user_id)

        if location is None:
            return

        lat, long = location

        interval = await self.set_interval_ui(user_id, (lat, long))

        user = User(id=user_id, latitude=lat, longitude=long, interval=interval)
        self.user_store.add(user)

        await self.client.send_message(
            user_id,
            "Настройка завершена. \nЧтобы изменить настройки используйте команды /set_location и /set_interval.",
            buttons=Button.clear(),
        )

        return user

    @command
    async def unregister(self, user: User) -> None:
        self.user_store.remove(user.id)
        self.scheduler.remove_task(user.id)

    def with_user[O](self, command: Callable[[Self, User], O]) -> Callable[[Message], Awaitable[O | None]]:
        async def wrapper(message: Message) -> O | None:
            user_id = message.chat_id
            assert isinstance(user_id, int)

            user = self.user_store.get(user_id)

            if user is None:
                await self.new_user(message)
                return

            result = await command(user)  # type: ignore
            return result

        return wrapper

    async def new_user_prompt(self, message: Message):
        assert message.chat_id is not None

        async with self.client.conversation(message.chat_id) as chat:
            await chat.send_message("Для использования бота, пройдите короткую регистрацию", buttons=Button.text("Регистрация"))
