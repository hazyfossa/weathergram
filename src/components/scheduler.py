import asyncio
from typing import Awaitable, Callable

from loguru import logger

from src.njct import Protocol, implements, provider

type TaskID = int


@provider()
class Scheduler(Protocol):
    def add_task(self, id: TaskID, task: Callable[..., Awaitable], interval: int) -> None: ...

    def remove_task(self, id: TaskID) -> None: ...

    async def run(self) -> None: ...


@implements(Scheduler, priority=1)
class AsyncScheduler:
    def __init__(self) -> None:
        self.tasks: dict[TaskID, asyncio.Task] = {}

    def add_task(self, id: TaskID, task: Callable[..., Awaitable], interval: int, override: bool = True) -> None:
        if id in self.tasks:
            if override:
                self.remove_task(id)
            else:
                raise KeyError

        async def worker():
            try:
                while True:
                    await asyncio.sleep(interval)
                    await task()
            except asyncio.CancelledError:
                return

        worker_unit = self.loop.create_task(worker())
        self.tasks[id] = worker_unit

        def callback(_):
            logger.debug("Task {} cancelled successfully", id)
            del self.tasks[id]

        worker_unit.add_done_callback(callback)

    def remove_task(self, id: TaskID) -> None:
        self.tasks[id].cancel()

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None:
            raise RuntimeError("Attemting to manage tasks before scheduler has started.")

        return self._loop

    async def run(self) -> None:
        self._loop = asyncio.get_running_loop()


# @implements(Scheduler, priority=2)
# class APScheduler:
#     def __init__(self):
#         with require_module():
#             from apscheduler.schedulers.asyncio import AsyncIOScheduler
