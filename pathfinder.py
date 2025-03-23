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



@dataclass
class BusStop:
    departs_from :str
    departure :str
    arrives_to: str
    arrival :str
    bus_n: str

@dataclass
class SavedConnection:
    previous :Node
    connection :Connection

    def __hash__(self) -> int:
        return (self.previous).__hash__()

@dataclass
class SavedTransfer:
    previous :Node
    arrival_time :datetime
    

class Pathfinder:
    _graph: ExpandedGraph

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

        starting_time = to_datetime(time)
        target_node = self._graph.get_nodes_by_stop_name(end)[0]
        scores = self._init_scores(start, starting_time, starting_line)
        saved_scores = {}
        saved_parents = {}
        winner = None

        while len(scores) > 0:
            current = self._get_best_node(scores)
            if current is not None:
                if current.bus_stop_name != target_node.bus_stop_name:
                    current_score, current_arr_time = scores[current]

                    for n in self._graph.get_neighbouring_nodes(current):
                        if n.bus_stop_name != current.bus_stop_name:
                            connection = self._graph.get_best_connection(current, n, current_arr_time)
                            if connection:
                                minutes = difference_in_minutes(current_arr_time, connection.arrives_at)
                                total_cost = current_score + minutes * minute_cost
                                if total_cost < scores[n][0]:
                                    scores[n] = (total_cost, connection.arrives_at)
                                    saved_parents[n] = SavedConnection(current, connection)
                        else:
                            total_cost = current_score + transfer_cost
                            if total_cost < scores[n][0]:
                                scores[n] = (total_cost, current_arr_time)
                                saved_parents[n] = SavedTransfer(current, current_arr_time)

                    self._graph.remove_node(current)
                    saved_scores[current] = (current_score, current_arr_time)
                    scores.pop(current)
                else:
                    saved_scores[current] = scores[current]
                    winner = current
                    break

        if not winner:
            return None
        else:
            stops = self._prepare_results(winner, saved_parents) 
            cost = self._calculate_cost(starting_time, stops)
            return stops, cost

    def _prepare_results(self, winner :Node, saved_parents :dict[Node, SavedConnection | SavedTransfer]) -> list[BusStop]:
        current = winner
        bus_stops = []
        while current in saved_parents:
            c = saved_parents[current]
            if isinstance(c, SavedConnection):
                bus_stops.append(BusStop(
                    departs_from=c.previous.bus_stop_name,
                    arrives_to=current.bus_stop_name,
                    bus_n=current.bus_n,
                    departure=c.connection.departs_at.strftime('%H:%M'),
                    arrival=c.connection.arrives_at.strftime('%H:%M'),
                ))
            current = saved_parents[current].previous
        bus_stops.reverse()
        return bus_stops

    def _calculate_cost(self, starting_time :datetime, bus_stops :list[BusStop]):
        lines_set = set()
        for b in bus_stops:
            lines_set.add(b.bus_n)
        transfers = len(lines_set) - 1
        total_time = difference_in_minutes(starting_time, to_datetime(bus_stops[-1].arrival))
        cost = transfers * self._tranfer_cost + total_time * self._minute_cost
        return cost

            

    def _init_scores(self, start: str, starting_time: datetime, starting_line=None):
        if starting_line:
            starting_nodes = [self._graph.get_node(start, starting_line)]
        else:
            starting_nodes = self._graph.get_nodes_by_stop_name(start)
        scores: dict[Node, Tuple[float, datetime]] = {}
        for n in self._graph.get_nodes():
            scores[n] = (100000000, starting_time)
        for n in starting_nodes:
            scores[n] = (0, starting_time)
        return scores

    def _get_best_node(
        self, scores: dict[Node, Tuple[float, datetime]]
    ) -> Optional[Node]:
        best_node = None
        best_score = 1000000000

        for node, (score, _) in scores.items():
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

