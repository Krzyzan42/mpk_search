from dataclasses import dataclass
from typing import Optional, Tuple
from graph import graph_from_data
from datetime import datetime

rows = open("connection_graph.csv").read().splitlines()
graph = graph_from_data(rows[1:-1])


@dataclass
class Distance:
    current_bus: str
    transfer_n: int


max_distance = Distance("", 10000)


def get_best_node(scores: dict[str, Distance]) -> Tuple[Optional[str], Distance]:
    best_distance = max_distance
    best_node = None
    for node, time in scores.items():
        if time.transfer_n < best_distance.transfer_n:
            best_distance = time
            best_node = node

    return best_node, best_distance


nodes = graph.get_nodes()
scores: dict[str, Distance] = {}
for n in nodes:
    scores[n] = max_distance

starting_node = "PL. GRUNWALDZKI"
scores[starting_node] = Distance("", -1)
saved_scores: dict[str, Distance] = {}

while len(scores) > 0:
    node, distance = get_best_node(scores)
    if not node:
        break
    neighbours = graph.get_neighbouring_nodes(node)

    for n in neighbours:
        transfer_weight = graph.get_transfer_weight(node, n, distance.current_bus)
        if not transfer_weight:
            continue

        new_bus = distance.current_bus
        new_weight = distance.transfer_n + transfer_weight

        if new_weight < scores[n].transfer_n:
            scores[n] = Distance(distance.current_bus, new_weight)

    graph.remove_node(node)
    saved_scores[node] = scores.pop(node)

a = []
for key, val in saved_scores.items():
    a.append((key, val))
a.sort(key=lambda x: x[1].transfer_n)

for dest, time in a:
    print(f"{dest}: {time.transfer_n}")
