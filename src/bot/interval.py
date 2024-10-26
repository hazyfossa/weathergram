import re
from enum import IntEnum

from attrs import define
from telethon import Button
from telethon.custom import Conversation

from src.bot.framework import User, command
from src.bot.weather import WeatherComponent
from src.components.location import Location
from src.components.scheduler import Scheduler


class seconds_per(IntEnum):
    minute = 60
    hour = minute * 60
    day = hour * 24
    week = day * 7


intervals: dict[str, int] = {
    "Раз в минуту": seconds_per.minute,
    "Ежедневно": seconds_per.day,
    "Каждые три дня": seconds_per.day * 3,
    "Еженедельно": seconds_per.week,
}  #  Настраеваемый


class CustomInterval:
    group = lambda tag: rf"(\d+{tag})?"  # noqa: E731
    tags = {
        "w": seconds_per.week,
        "d": seconds_per.day,
        "h": seconds_per.hour,
        "m": seconds_per.minute,
        "s": 1,
    }

    regex = re.compile("".join(map(group, tags.keys())))

    @classmethod
    def parse(cls, string: str) -> int | None:
        match = cls.regex.match(string)

        if match is None:
            return None

        result = 0

        for group in match.groups():
            if group is None:
                continue

            value, tag = group[:-1], group[-1]
            value = int(value)

            result += cls.tags[tag] * value

        if result == 0:
            return None
        else:
            return result


@define
class IntervalComponent(WeatherComponent):
    scheduler: Scheduler.inject

    @command
    async def set_interval(self, user: User):
        interval = await self.set_interval_ui(user.id, (user.latitude, user.longitude))
        user.interval = interval

        await self.client.send_message(user.id, "Интервал обновлён.", buttons=Button.clear())

    async def set_interval_ui(self, user_id: int, location: Location):
        async with self.client.conversation(user_id) as menu:
            await menu.send_message(
                "Выберите интервал отправки погоды: ",
                buttons=[
                    Button.text(
                        value,
                        single_use=True,
                        resize=True,
                    )
                    for value in [*intervals.keys(), "Настраиваемый"]
                ],
            )

            try:
                reply = await menu.get_response()
            except TimeoutError:
                await menu.send_message("Время ожидания истекло.")
                return

            if reply.text == "Настраиваемый":
                interval = await self.manual_interval_input(menu)
            else:
                interval = intervals[reply.text]

        async def future():
            await self.send_weather(user_id, location)

        self.scheduler.add_task(user_id, future, interval)

        return interval

    async def manual_interval_input(self, menu: Conversation):
        await menu.send_message(
            """Введите необходимый интервал в формате [x]w[x]d[x]h[x]m[x]s.
w - неделя, d - день, h - час, m - минута, s - секунда.

Пример: 2h30m - каждые 2 часа 30 минут.
5d - каждые пять дней.
            """,
        )

        while True:
            reply = await menu.get_response()

            interval = CustomInterval.parse(reply.text)

            if interval is not None:
                return interval
            else:
                await menu.send_message("Неверный интервал, попробуйте ещё раз:")
