from abc import ABC, abstractmethod

from src.njct import implements, provider

from .common import API

type Location = tuple[float, float]  # Latitude-longitude # Consider namedtuples


@provider()
class LocationProvider(ABC, API):
    @abstractmethod
    def query(self, name: str) -> Location: ...


@implements(LocationProvider)
class Nominatim(LocationProvider.inject):
    url = "https://nominatim.openstreetmap.org"

    def query(self, name: str) -> Location:  # TODO multiple?
        response = self.client.get("/search", params={"format": "jsonv2", "q": name}).content
        data = self.json.loads(response)[0]

        return data["lat"], data["lon"]
