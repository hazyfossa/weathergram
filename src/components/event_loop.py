from asyncio import AbstractEventLoop

from src.njct import Protocol, import_implementation, provider


@provider()
class EventLoop(Protocol):
    def new_event_loop(self) -> AbstractEventLoop: ...


import_implementation(EventLoop, "asyncio")
import_implementation(EventLoop, "uvloop", priority=10)
