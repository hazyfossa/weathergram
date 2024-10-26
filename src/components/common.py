from abc import ABC, abstractmethod
from typing import Protocol

from httpx import Client

from .json_parser import Json


class ApiProtocol(Protocol):
    url: str
    key: str | None


class API(ApiProtocol):
    def __init__(self, json: Json.inject) -> None:
        self.client = Client(base_url=self.url)
        self.json = json
