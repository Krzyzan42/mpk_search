from dataclasses import dataclass
from typing import Optional, Tuple
from graph import ExpandedGraph, Node, to_row_entry, to_datetime, difference_in_minutes
from datetime import datetime
from time import time

@dataclass
class BusStop:
    time :str
    stop_name :str
    bus_n :str
    score :float


class Pathfinder:
    _graph: ExpandedGraph

    def __init__(self, csv_filename) -> None:
        rows = open(csv_filename).read().splitlines()[1:]
        row_entries = [to_row_entry(r) for r in rows]
        self._graph = ExpandedGraph(row_entries)

    def node_exists(self, name :str):
        return len(self._graph.get_nodes_by_stop_name(name)) > 0

    def find_path(self, start: str, end: str, time: str, optimize :str = 't', use_astar = True):
        self._graph.reset()

        starting_time = to_datetime(time)
        target_node = self._graph.get_nodes_by_stop_name(end)[0]

        target_coords = None
        use_astar = False
        if use_astar:
            target_coords = (target_node.latitude, target_node.longitude)

        target_node_name = target_node.bus_stop_name
        scores = self._init_scores(start, starting_time)

        saved_scores = {}
        winner = None

        while len(scores) > 0:
            current = self._get_best_node(scores)
            if current is None:
                break
            if current.bus_stop_name == target_node_name:
                saved_scores[current] = scores[current]
                winner = current
                break

            current_score, current_arr_time = scores[current]

            for n in self._graph.get_neighbouring_nodes(current):
                cost, arr_time = self._graph.get_connection_weight(
                    current,
                    n,
                    current_arr_time,
                    heuristic_target=target_coords,
                )
                if cost:
                    cost += current_score
                    if cost < scores[n][0]:
                        scores[n] = (cost, arr_time)
                        n.parent = current

            self._graph.remove_node(current)
            saved_scores[current] = (current_score, current_arr_time)
            scores.pop(current)

        if not winner:
            return None, None
        else:
            bus_stops, total_cost = self._prepare_result(winner, saved_scores, starting_time)
            return bus_stops, total_cost

    def _prepare_result(self, end_node :'Node', scores :dict[Node, Tuple[float, datetime]], starting_time :datetime) -> Tuple[list[BusStop], float]:
        path = self._traverse_final_path(end_node)
        bus_stops = self._node_path_to_bus_stops(path, scores)
        transfer_cost = self._calculate_transfer_cost(path)
        _, arrival_time = scores[end_node]
        time_cost = self._calculate_time_cost(starting_time, arrival_time)
        print(transfer_cost)
        print(time_cost)

        return bus_stops, transfer_cost + time_cost

    def _traverse_final_path(self, end_node :Optional[Node]) -> list[Node]:
        traversed_nodes = []
        while end_node != None:
            traversed_nodes.append(end_node)
            end_node = end_node.parent
        traversed_nodes.reverse()
        return traversed_nodes

    def _node_path_to_bus_stops(self, path :list[Node], scores :dict[Node, Tuple[float, datetime]]) -> list[BusStop]:
        bus_stops = []
        for node in path:
            _, arrival_time = scores[node]
            bus_stops.append(BusStop(arrival_time.strftime('%H:%M'), node.bus_stop_name, node.bus_n, scores[node][0]))
        return bus_stops

    def _calculate_transfer_cost(self, path :list[Node]) -> float:
        current_bus = path[0].bus_n
        transfer_count = 0
        for p in path:
            if p.bus_n != current_bus:
                transfer_count += 1
                current_bus = p.bus_n
        return self._graph._transfer_cost * transfer_count

    def _calculate_time_cost(self, starting_time :datetime, arrival_time :datetime) -> float:
        return difference_in_minutes(starting_time, arrival_time)


    def _init_scores(self, start: str, starting_time: datetime):
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

    def _debug_print_scores(self, scores):
        print("SCORES --------------------------------------")
        items = list(scores.items())
        items.sort(key=(lambda x: -x[1][0]))
        for key, (score, arr_time) in items:
            if score > 1000000:
                continue
            print(f"{key} - {score} at {arr_time}")
        print("END OF SCORES--------------------------------")


p = Pathfinder("connection_graph.csv")

start = time()
bus_stops, cost = p.find_path("Górnickiego", "GAJ", "8:00:00")
end = time()

if bus_stops != None:
    [print(s) for s in bus_stops]
    print(cost)
print(f"Script took {(end - start)*1000}ms")
