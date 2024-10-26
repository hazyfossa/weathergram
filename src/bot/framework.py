from inspect import getmembers, ismethod
from typing import Any, Awaitable, Callable

from attrs import define
from telethon import TelegramClient
from telethon.events import NewMessage

from src.database.schema import User as User

type Message = NewMessage.Event


@define
class Component:
    client: TelegramClient


def command[T: Callable](handler: T) -> T:
    setattr(handler, "__command_flag", True)
    return handler


def init_client(
    bot: object,
    client: TelegramClient,
    with_user: Callable,
) -> TelegramClient:
    handlers = getmembers(bot, predicate=lambda i: ismethod(i) and hasattr(i, "__command_flag"))

    for name, handler in handlers:
        client.on(NewMessage(pattern=f"/{name}"))(with_user(handler))

    return client
