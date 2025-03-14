import sys
from pathfinder import Pathfinder, to_datetime, BusStop
from time import time


p = Pathfinder("connection_graph.csv")

# start = input('Select starting point: ')
# if not p.stop_exists(start):
#     raise ValueError('Bus stop doesnt exist')
# end = input('Select destination: ')
# if not p.stop_exists(start):
#     raise ValueError('Bus stop doesnt exist')
# optimization = input('[t/p] t - time, p - transfers: ')
# if optimization not in ['t', 'p']:
#     raise ValueError('Invalid choice')
# arr_time = input('Starting time [13:54:00]: ')
# algorithm = input('[a/d] a - a*, d - dijkstra: ')
# if algorithm not in ['a', 'd']:
#     raise ValueError('Invalid choice')

start = 'Górnickiego'
end = 'GAJ'
arr_time = '8:00:00'
optimization = 't'
algorithm = 'd'

start_t = time()
bus_stops, cost = p.find_path(start, end, arr_time, optimization, algorithm == 'a')
end_t = time()
time_ms = (end_t - start_t) * 1000


def pretty_print_bus_stops(bus_stop :list[BusStop]):
    important_stops = [bus_stop[0]]
    for i in range(len(bus_stop) - 1):
        if bus_stop[i].stop_name == bus_stop[i + 1].stop_name:
            important_stops.append(bus_stop[i])
            important_stops.append(bus_stop[i + 1])
    important_stops.append(bus_stop[-1])
    
    for i in range(0, len(important_stops), 2):
        a = important_stops[i]
        b = important_stops[i + 1]
        print(f'Line {a.bus_n}: {a.stop_name} at {a.time} -> {b.stop_name} at {b.time}')


if bus_stops:
    pretty_print_bus_stops(bus_stops)
    print(f'Time taken: {time_ms:.2f}ms. Path cost: {cost}', file=sys.stderr)
else:
    print(f'Time taken: {time_ms:.2f}ms. Path not found', file=sys.stderr)
    print(f'Couldnt find the path')




