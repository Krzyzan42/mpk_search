from typing import Optional, Tuple
from expanded_graph import ExpandedGraph, Node, to_row_entry, to_datetime
from datetime import datetime

rows = open('connection_graph.csv').read().splitlines()[1:]
row_entries = [to_row_entry(r) for r in rows]
graph = ExpandedGraph(row_entries)

starting_time = to_datetime('8:00:00')
starting_nodes = graph.get_nodes_by_stop_name('Górnickiego')

target_node = graph.get_nodes_by_stop_name('GAJ')[0]
target_coords = (target_node.latitude, target_node.longitude)
print(target_coords)
target_node_name = target_node.bus_stop_name

scores :dict[Node, Tuple[float, datetime]] = {}

def get_best_node() -> Optional[Node]:
    best_node = None
    best_score = 1000000000

    for node, (score, time) in scores.items():
        if score < best_score:
            best_node = node
            best_score = score
    return best_node


def print_scores():
    print('SCORES --------------------------------------')
    items = list(scores.items())
    items.sort(key=(lambda x: -x[1][0]))
    for key, (score, arr_time) in items:
        if score > 1000000:
            continue
        print(f'{key} - {score} at {arr_time}')
    print('END OF SCORES--------------------------------')

for n in graph.get_nodes():
    scores[n] = (100000000, starting_time)
for n in starting_nodes:
    scores[n] = (0, starting_time)
saved_scores = {}

while True:
    # print_scores()
    if len(scores) == 0:
        break
    current = get_best_node()
    if current is None:
        break
    if current.bus_stop_name == target_node_name:
        print('foudns solution')
        break
    current_score, current_arr_time = scores[current]

    for n in graph.get_neighbouring_nodes(current):
        cost, arr_time = graph.get_connection_weight(current, n, current_arr_time, heuristic_target=target_coords)
        if not cost:
            continue
        if cost < scores[n][0]:
            scores[n] = (cost, arr_time)
            n.parent = current

    graph.remove_node(current)
    saved_scores[current] = (current_score, current_arr_time)
    scores.pop(current)
print_scores()
 
target = get_best_node()
if not target:
    raise ValueError()
print(target)
while target.parent is not None:
    print(target.parent)
    target = target.parent

