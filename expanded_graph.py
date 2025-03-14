from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from geopy.distance import geodesic
from typing import Callable, Optional, Tuple
import math

def to_datetime(time: str):
    hour, minute, second = time.split(":")
    day = 1
    hour = int(hour)
    minute = int(minute)
    second = int(second)
    if hour >= 24:
        day = 2
        hour -= 24
    return datetime(2000, 1, day, hour, minute, second)

def to_row_entry(row :str):
    r = row.split(',')
    return RowEntry(
        start=r[5],
        end=r[6],
        departs_at=to_datetime(r[3]),
        arrives_at=to_datetime(r[4]),
        bus_n=r[2],
        start_latitude=float(r[7]),
        start_longitude=float(r[8]),
        end_latitude=float(r[9]),
        end_longitude=float(r[10]),
    )

@dataclass
class RowEntry:
    start: str
    end: str
    departs_at: datetime
    arrives_at: datetime
    bus_n: str
    start_latitude: float
    start_longitude: float
    end_latitude: float
    end_longitude: float


@dataclass
class Connection:
    departs_at: datetime
    arrives_at: datetime
    bus_n: str


class Node:
    bus_stop_name: str
    bus_n: str
    latitude: float
    longitude: float
    removed: bool
    parent: Optional['Node']

    _connections: dict["Node", list[Connection]]
    _same_stop_nodes: list["Node"]

    def __init__(self, stop_name, bus_name, latitude=0.0, longitude=0.0) -> None:
        self._connections = {}
        self.bus_stop_name = stop_name
        self.bus_n = bus_name
        self.latitude = latitude
        self.longitude = longitude
        self.removed = False
        self.parent = None

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Node):
            raise ValueError()
        return value.bus_n == self.bus_n and value.bus_stop_name == self.bus_stop_name

    def __hash__(self) -> int:
        return hash(self.bus_stop_name + self.bus_n)

    def __repr__(self) -> str:
        s = f"{self.bus_stop_name}:{self.bus_n}"
        return s

    def add_connection(self, node: "Node", connection: Connection):
        if not node in self._connections:
            self._connections[node] = []
        self._connections[node].append(connection)

    def get_best_connection(self, end: "Node", departure_time) -> Optional[datetime]:
        if end not in self._connections or end.removed:
            raise ValueError("Connection doesnt exist")

        connections = self._connections[end]
        for c in connections:
            if c.departs_at >= departure_time:
                return c.arrives_at
        return None

    def set_same_stop_nodes(self, nodes: list["Node"]):
        self._same_stop_nodes = nodes

    def get_neighbours(self):
        all_nodes = list(self._connections.keys()) + self._same_stop_nodes
        active_nodes = [n for n in all_nodes if n.removed is False]
        return active_nodes

    def sort_connections(self):
        for key, value in self._connections.items():
            value.sort(key=lambda x: x.arrives_at)


def difference_in_minutes(a: datetime, b: datetime):
    c = b - a
    return math.floor(c.total_seconds() / 60)


def distance(a: Tuple[float, float], b: Tuple[float, float]):
    return geodesic(a, b).km
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


class ExpandedGraph:
    _nodes: list[Node]
    _time_weight_func: Callable
    _transfer_const: float
    _cost_per_km: float

    def __init__(
        self,
        connections: list[RowEntry],
        time_weight_func=difference_in_minutes,
        transfer_cost=10,
        cost_per_kilometer=10,
    ):
        self._nodes = self._create_nodes(connections)
        self._append_connections_to_nodes(connections)
        self._time_weight_func = time_weight_func
        self._cost_per_km = cost_per_kilometer
        self._transfer_const = transfer_cost

    def get_nodes(self) -> list[Node]:
        return [n for n in self._nodes if n.removed is False]

    def get_connection_weight(
        self,
        start: Node,
        end: Node,
        departure_time: datetime,
        heuristic_target: Optional[Tuple[float, float]] = None,
    ) -> Tuple[float, datetime]:
        if start.removed or end.removed:
            raise ValueError()
        if start.bus_stop_name == end.bus_stop_name:
            heuristic = 0
            if heuristic_target:
                heuristic = distance((end.latitude, end.longitude), heuristic_target) * self._cost_per_km
            return self._transfer_const + heuristic, departure_time
        else:
            arrival_time = start.get_best_connection(end, departure_time)
            if not arrival_time:
                return (None, None)
            heuristic = 0
            if heuristic_target:
                heuristic = distance(
                    (end.latitude, end.longitude), heuristic_target
                ) * self._cost_per_km
            time_weight = self._time_weight_func(departure_time, arrival_time)
            return heuristic + time_weight, arrival_time

    def get_neighbouring_nodes(self, node: Node) -> list[Node]:
        return node.get_neighbours()

    def remove_node(self, node: Node):
        node.removed = True

    def get_nodes_by_stop_name(self, stop_name: str) -> list[Node]:
        nodes = []
        for n in self._nodes:
            if n.bus_stop_name == stop_name:
                nodes.append(n)
        return nodes

    def get_node(self, stop_name, bus_name) -> Node:
        for n in self._nodes:
            if n.bus_stop_name == stop_name and n.bus_n == bus_name:
                return n
        raise ValueError("Tried to get a node that doesnt exist")

    def _create_nodes(self, connections: list[RowEntry]) -> list[Node]:
        nodes: dict[Tuple[str, str], Node] = {}
        nodes_by_bus_stop: dict[str, set[Node]] = defaultdict(set)

        for c in connections:
            if (c.start, c.bus_n) not in nodes:
                node = Node(c.start, c.bus_n, c.start_latitude, c.start_longitude)
                nodes[(c.start, c.bus_n)] = node
                nodes_by_bus_stop[c.start].add(node)
            if (c.end, c.bus_n) not in nodes:
                node = Node(c.end, c.bus_n, c.end_latitude, c.end_longitude)
                nodes[(c.end, c.bus_n)] = node
                nodes_by_bus_stop[c.end].add(node)

        for n in nodes.values():
            n.set_same_stop_nodes(list(nodes_by_bus_stop[n.bus_stop_name] - set([n])))
        return list(nodes.values())

    def _append_connections_to_nodes(self, entries: list[RowEntry]):
        node_dict = {}
        for n in self._nodes:
            node_dict[(n.bus_stop_name, n.bus_n)] = n
        for entry in entries:

            start = node_dict[(entry.start, entry.bus_n)]
            end = node_dict[(entry.end, entry.bus_n)]

            start.add_connection(
                end, Connection(entry.departs_at, entry.arrives_at, entry.bus_n)
            )
        for n in self._nodes:
            n.sort_connections()
