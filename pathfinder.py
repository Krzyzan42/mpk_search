from dataclasses import dataclass
from typing import Optional, Tuple
from graph import (
    Connection,
    ExpandedGraph,
    Node,
    RowEntry,
    to_row_entry,
    to_datetime,
)
from datetime import datetime
import math


def difference_in_minutes(a: datetime, b: datetime):
    c = b - a
    return math.floor(c.total_seconds() / 60)

def cartesian(a :Tuple[float, float], b :Tuple[float, float]):
    return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)


@dataclass
class BusStop:
    departs_from: str
    departure: str
    arrives_to: str
    arrival: str
    bus_n: str


@dataclass
class SavedConnection:
    previous: Node
    connection: Optional[Connection]

    def __hash__(self) -> int:
        return (self.previous).__hash__()


class Pathfinder:
    _graph: ExpandedGraph
    _minute_cost: float
    _tranfer_cost: float
    _km_cost: float

    _starting_time: datetime
    _target_coords: Tuple[float, float]
    _target_bus_stop: str
    _scores: dict[Node, Tuple[float, datetime]]

    def __init__(self, row_entries: list[RowEntry]) -> None:
        self._graph = ExpandedGraph(row_entries)

    def find_path(
        self,
        start: str,
        end: str,
        time: str,
        minute_cost: float = 1,
        transfer_cost: float = 5,
        km_cost: float = 1,
        starting_line: Optional[str] = None,
    ):
        self._graph.reset()
        self._minute_cost = minute_cost
        self._tranfer_cost = transfer_cost
        self._km_cost = km_cost

        self._starting_time = to_datetime(time)
        self._target_bus_stop = end
        self._saved_parents = {}
        self._init_scores(start, starting_line)
        target_node = self._graph.get_nodes_by_stop_name(end)[0]
        self._target_coords = (target_node.longitude, target_node.latitude)

        winner = self._run()

        if winner is not None:
            stops = self._prepare_results(winner, self._saved_parents)
            cost = self._calculate_cost(stops)
            return stops, cost
        else:
            return None

    def _run(self):
        best = self._get_best_node()
        while best != None:
            if best.bus_stop_name == self._target_bus_stop:
                return best
            else:
                self._discover_node(best)
                best = self._get_best_node()

    def _discover_node(self, node: Node):
        for n in self._graph.get_neighbouring_nodes(node):
            if n.bus_stop_name != node.bus_stop_name:
                self._discover_regular_connection(node, n)
            else:
                self._discover_transfer_connection(node, n)

        self._graph.remove_node(node)
        self._scores.pop(node)

    def _discover_regular_connection(self, a: Node, b: Node):
        score, arrival_time = self._scores[a]

        connection = self._graph.get_best_connection(a, b, arrival_time)
        if connection:
            minutes = difference_in_minutes(arrival_time, connection.arrives_at)
            heuristic_cost = self._heuristic_cost(b)
            total_cost = score + minutes * self._minute_cost + heuristic_cost
            if total_cost < self._scores[b][0]:
                self._scores[b] = (total_cost, connection.arrives_at)
                self._saved_parents[b] = SavedConnection(a, connection)

    def _discover_transfer_connection(self, a: Node, b: Node):
        score, arrival_time = self._scores[a]
        heuristic_cost = self._heuristic_cost(b)
        total_cost = score + self._tranfer_cost + heuristic_cost
        if total_cost < self._scores[b][0]:
            self._scores[b] = (total_cost, arrival_time)
            self._saved_parents[b] = SavedConnection(a, None)

    def _heuristic_cost(self, a :Node):
        coords = (a.longitude, a.latitude)
        return cartesian(coords, self._target_coords) * self._km_cost

    def _prepare_results(
        self, winner: Node, saved_parents: dict[Node, SavedConnection]
    ) -> list[BusStop]:
        current = winner
        bus_stops = []
        while current in saved_parents:
            c = saved_parents[current]
            if c.connection:
                bus_stops.append(
                    BusStop(
                        departs_from=c.previous.bus_stop_name,
                        arrives_to=current.bus_stop_name,
                        bus_n=current.bus_n,
                        departure=c.connection.departs_at.strftime("%H:%M"),
                        arrival=c.connection.arrives_at.strftime("%H:%M"),
                    )
                )
            current = saved_parents[current].previous
        bus_stops.reverse()
        return bus_stops

    def _calculate_cost(self, bus_stops: list[BusStop]):
        lines_set = set()
        for b in bus_stops:
            lines_set.add(b.bus_n)
        transfers = len(lines_set) - 1
        total_time = difference_in_minutes(
            self._starting_time, to_datetime(bus_stops[-1].arrival)
        )
        cost = transfers * self._tranfer_cost + total_time * self._minute_cost
        return cost

    def _init_scores(self, start: str, starting_line=None):
        if starting_line:
            starting_nodes = [self._graph.get_node(start, starting_line)]
        else:
            starting_nodes = self._graph.get_nodes_by_stop_name(start)
        scores: dict[Node, Tuple[float, datetime]] = {}
        for n in self._graph.get_nodes():
            scores[n] = (100000000, self._starting_time)
        for n in starting_nodes:
            scores[n] = (0, self._starting_time)
        self._scores = scores

    def _get_best_node(self) -> Optional[Node]:
        best_node = None
        best_score = 1000000000

        for node, (score, _) in self._scores.items():
            if score < best_score:
                best_node = node
                best_score = score
        return best_node

    @staticmethod
    def from_csv(csv_filename) -> "Pathfinder":
        rows = open(csv_filename).read().splitlines()[1:]
        row_entries = [to_row_entry(r) for r in rows]
        return Pathfinder(row_entries)

    def node_exists(self, name: str):
        return len(self._graph.get_nodes_by_stop_name(name)) > 0

    def stop_exists(self, stop_name: str):
        return self._graph.get_nodes_by_stop_name(stop_name) != []
