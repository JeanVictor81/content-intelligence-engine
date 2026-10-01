"""Shared contract for source connectors."""

from dataclasses import dataclass
from typing import Protocol, TypeVar

ItemT = TypeVar("ItemT")


@dataclass(frozen=True, slots=True)
class SearchOptions:
    """Common limits for a connector search."""

    max_results: int = 20

    def __post_init__(self) -> None:
        if self.max_results < 1:
            raise ValueError("max_results must be greater than zero.")


class Connector(Protocol[ItemT]):
    """Contract implemented by connectors for an individual source platform."""

    name: str

    def search(self, query: str, options: SearchOptions | None = None) -> list[ItemT]:
        """Search configured sources and return connector-native items."""
        ...

    def fetch(self, item: ItemT) -> ItemT:
        """Return full details for an item when the source separates search and fetch."""
        ...
