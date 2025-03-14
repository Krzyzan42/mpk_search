from datetime import datetime
from os import remove
from typing import Optional, Tuple
from dataclasses import dataclass


class Node:
    def __init__(self, name) -> None:
        self._connections = {}
        self.name = name

    def get_arrival_time(self, end: "Node", start_time: datetime) -> Optional[datetime]:
        connections = self._connections[end]
        for c in connections:
            if c.departs_at > start_time:
                return c.arrives_at
        return None

    def remove_neighbour(self, neighbor: "Node"):
        # print(f'{self.name} neighbours-----')
        # for k, i in self._connections.items():
        #     print(k.name)
        # print('neighbours-----')
        if neighbor in self._connections:
            self._connections.pop(neighbor)

    def get_neighbours(self) -> set["Node"]:
        return set(self._connections.keys())

    def add_connection(
        self, to: "Node", start_t: datetime, end_t: datetime, bus_n: str
    ):
        conn = Connection(start_t, end_t, bus_n)
        if not to in self._connections:
            self._connections[to] = []
        self._connections[to].append(conn)


@dataclass
class RowEntry:
    start: str
    end: str
    departs_at: datetime
    arrives_at: datetime
    bus_n: str


# For a bus going from A->B->C three times a day, there should be entries like this:
# A->B 9:00 9:10
# B->C 9:10 9:20
# A->B 11:00 11:10
# B->C 11:10 11:20
# A->B 15:00 15:10
# B->C 15:10 15:20


class Graph:
    def __init__(self, entries: list[RowEntry]) -> None:
        pass

    def get_bus_stops(self) -> list[str]:
        pass

    def get_earliest_arrival_time(self, start: str, end: str, departure_time: datetime):
        pass

    def get_neighbouring_bus_stops(self, bus_stop: str) -> list[str]:
        pass

    def remove_bus_stop(self, bus_stop: str):
        pass
