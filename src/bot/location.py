from attrs import define
from telethon import Button
from telethon.custom import Conversation
from telethon.types import GeoPointEmpty, Message, MessageMediaGeo

from src.bot.framework import User, command
from src.components.location import Location, LocationProvider

from .interval import IntervalComponent


@define
class LocationComponent(IntervalComponent):
    location_provider: LocationProvider.inject

    @command
    async def set_location(self, user: User):
        location = await self.set_location_ui(user.id)

        if location is None:
            return

        lat, long = location

        user.latitude = lat
        user.longitude = long

        await self.client.send_message(user.id, "Местоположение обновлено.", buttons=Button.clear())

    async def set_location_ui(self, user_id: int) -> Location | None:
        async with self.client.conversation(user_id) as menu:
            await menu.send_message(
                "[⚙] Введите местоположение: ",
                buttons=[
                    Button.request_location("Автоматически", single_use=True, resize=True),
                    Button.text("Вручную", single_use=True, resize=True),
                ],
            )

            try:
                reply = await menu.get_response()
            except TimeoutError:
                await menu.send_message("Время ожидания истекло.")
                return

            if isinstance(reply.media, MessageMediaGeo):
                geo_point = reply.media.geo

                if isinstance(geo_point, GeoPointEmpty):
                    await menu.send_message(
                        "При автоматической настройке местоположения произошла ошибка, попробуйте ручной способ."
                    )
                    return await self.manual_location_input(menu)

                return geo_point.lat, geo_point.long

            else:
                return await self.manual_location_input(menu)

    async def manual_location_input(self, menu: Conversation) -> Location:
        await menu.send_message("Введите ваше местоположение, с удобной для вас точностью: ")

        while True:
            reply = await menu.get_response()

            location = self.location_provider.query(reply.text)

            if location is not None:
                return location
            else:
                await menu.send_message("Невозможо найти указанное метоположение.\nПопробуйте ещё раз.")
