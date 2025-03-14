from datetime import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class RowEntry:
    start: str
    end: str
    departs_at: datetime
    arrives_at: datetime
    bus_n: str


@dataclass
class Connection:
    departs_at: datetime
    arrives_at: datetime
    bus_n: str


def to_datetime(entry: str) -> datetime:
    hour, minute, second = entry.split(":")
    day = 1
    hour = int(hour)
    minute = int(minute)
    second = int(second)
    if hour >= 24:
        day += 1
        hour -= 24

    return datetime(2000, 1, day, hour, minute, second)


def parse_data(rows: list[str]) -> list[RowEntry]:
    connections: list[RowEntry] = []
    for r in rows:
        r = r.split(",")
        connections.append(
            RowEntry(r[5], r[6], to_datetime(r[3]), to_datetime(r[4]), r[2])
        )
    return connections


class Node:
    _connections: dict["Node", list[Connection]]
    name: str

    def __init__(self, name) -> None:
        self._connections = {}
        self.name = name

    def get_arrival_time(self, end: "Node", start_time: datetime) -> Optional[datetime]:
        if not end in self._connections:
            return None

        connections = self._connections[end]
        for c in connections:
            if c.departs_at >= start_time:
                return c.arrives_at
        return None

    def get_transfer_weight(self, end: "Node", bus_n: str) -> Optional[int]:
        if not end in self._connections:
            return None
        connections = self._connections[end]
        for c in connections:
            if c.bus_n == bus_n:
                return 0
        return 1

    def remove_neighbour(self, neighbor: "Node"):
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

    def sort_connections(self):
        for key, connections in self._connections.items():
            connections.sort(key=lambda x: x.arrives_at)


class Graph:
    _nodes: dict[str, Node]

    def __init__(self, entries: list[RowEntry]) -> None:
        self._nodes = self._get_nodes_from_connections(entries)
        self._add_connections(entries)

    def get_nodes(self) -> list[str]:
        return list(self._nodes.keys())

    def get_arrival_time(self, start: str, end: str, departure_time: datetime):
        start_n = self._nodes[start]
        end_n = self._nodes[end]
        return start_n.get_arrival_time(end_n, departure_time)

    def get_transfer_weight(self, start: str, end: str, bus_n: str):
        start_n = self._nodes[start]
        end_n = self._nodes[end]
        return start_n.get_transfer_weight(end_n, bus_n)

    def get_neighbouring_nodes(self, node: str) -> list[str]:
        neighbour_nodes = self._nodes[node].get_neighbours()
        result = []
        for n in neighbour_nodes:
            result.append(n.name)
        return result

    def remove_node(self, node: str):
        remove_n = self._nodes.pop(node)
        for n in self._nodes.values():
            n.remove_neighbour(remove_n)

    def _get_nodes_from_connections(
        self, connections: list[RowEntry]
    ) -> dict[str, Node]:
        nodes: dict[str, Node] = {}
        for c in connections:
            if not c.start in nodes:
                nodes[c.start] = Node(c.start)
            if not c.end in nodes:
                nodes[c.end] = Node(c.end)
        return nodes

    def _add_connections(self, connections: list[RowEntry]):
        for c in connections:
            if c.start == c.end:
                continue
            start_n = self._nodes[c.start]
            end_n = self._nodes[c.end]

            start_n.add_connection(end_n, c.departs_at, c.arrives_at, c.bus_n)
        for n in self._nodes.values():
            n.sort_connections()


def graph_from_data(rows: list[str]) -> Graph:
    return Graph(parse_data(rows))
