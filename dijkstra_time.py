from typing import Optional, Tuple
from graph import Graph, graph_from_data
from datetime import datetime

rows = open("connection_graph.csv").read().splitlines()
graph = graph_from_data(rows[1:-1])

max_time = datetime.max


def get_best_node(scores: dict[str, datetime]) -> Tuple[Optional[str], datetime]:
    best_time = max_time
    best_node = None
    for node, time in scores.items():
        if time < best_time:
            best_time = time
            best_node = node

    return best_node, best_time


nodes = graph.get_nodes()
scores: dict[str, datetime] = {}
for n in nodes:
    scores[n] = max_time

starting_node = "PL. GRUNWALDZKI"
starting_time = datetime(2000, 1, 1, 8, 0, 0)

scores[starting_node] = starting_time

saved_scores: dict[str, datetime] = {}

while len(scores) > 0:
    node, time = get_best_node(scores)
    if not node:
        break
    neighbours = graph.get_neighbouring_nodes(node)
    print(f"Processing {node}")

    for n in neighbours:
        arrival_time = graph.get_arrival_time(node, n, time)
        if arrival_time and arrival_time < scores[n]:
            scores[n] = arrival_time

    graph.remove_node(node)
    saved_scores[node] = scores.pop(node)

a = []
for key, val in saved_scores.items():
    a.append((key, val))
a.sort(key=lambda x: x[1])

for dest, time in a:
    print(f'{dest}: {time.strftime("%H:%M")}')
