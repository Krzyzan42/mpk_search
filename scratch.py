from typing import Optional, Tuple
from expanded_graph import ExpandedGraph, Node, to_row_entry, to_datetime, distance
from datetime import datetime

rows = open('connection_graph.csv').read().splitlines()[500000:600000]
row_entries = [to_row_entry(r) for r in rows]
graph = ExpandedGraph(row_entries)

nodes :dict[str, Node] = {}
for n in graph.get_nodes():
    nodes[n.bus_stop_name] = n

target = nodes['Jedności Narodowej']
a = (target.latitude, target.longitude)

for n in nodes.values():
    b = (n.latitude, n.longitude)

    print(f'TO {n.bus_stop_name} - {distance(a, b)}m')
