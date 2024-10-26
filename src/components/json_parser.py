from typing import Any

from src.njct import Protocol, implements, import_implementation, provider


@provider()
class Json(Protocol):
    def loads(self, data: bytes) -> Any: ...

    def dumps(self, object: Any) -> bytes: ...


@implements(Json, name="stdlib", priority=1)
class StdlibJsonAdapter:
    def __init__(self) -> None:
        import json

        self.json = json

    def dumps(self, object: Any) -> bytes:
        return self.json.dumps(object).encode()

    def loads(self, data: bytes) -> Any:
        return self.json.loads(data)


import_implementation(Json, "ujson", priority=2)
import_implementation(Json, "orjson", priority=3)
