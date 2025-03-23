import sys
from utils import pretty_print_bus_stops
from pathfinder import Pathfinder, BusStop
from time import time


p = Pathfinder.from_csv("connection_graph.csv")

start = input("Select starting point: ")
if not p.stop_exists(start):
    raise ValueError("Bus stop doesnt exist")
end = input("Select destination: ")
if not p.stop_exists(start):
    raise ValueError("Bus stop doesnt exist")
optimization = input("[t/p] t - time, p - transfers: ")
if optimization not in ["t", "p"]:
    raise ValueError("Invalid choice")
arr_time = input("Starting time [13:54:00]: ")
algorithm = input("[a/d] a - a*, d - dijkstra: ")
if algorithm not in ["a", "d"]:
    raise ValueError("Invalid choice")

km_cost = 0
minute_cost = 0
transfer_cost = 0
if algorithm == "a":
    km_cost = 100000
if optimization == "t":
    minute_cost = 1
else:
    transfer_cost = 1

# start = "Górnickiego"
# end = "GAJ"
# arr_time = "8:00"
# optimization = "t"
# algorithm = "d"

start_t = time()
result = p.find_path(
    start,
    end,
    arr_time,
    minute_cost=minute_cost,
    transfer_cost=transfer_cost,
    km_cost=km_cost,
)
end_t = time()
time_ms = (end_t - start_t) * 1000


if result:
    bus_stops, cost = result
    pretty_print_bus_stops(bus_stops)
    print(f"Time taken: {time_ms:.2f}ms. Path cost: {cost}", file=sys.stderr)
else:
    print(f"Time taken: {time_ms:.2f}ms. Path not found", file=sys.stderr)
    print(f"Couldnt find the path")
