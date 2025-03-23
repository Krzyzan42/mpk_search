
from pathfinder import BusStop


def pretty_print_bus_stops(bus_stop: list[BusStop]):
    collapsed_stops = []
    line = bus_stop[0].bus_n
    line_index = 0
    for i in range(len(bus_stop) + 1):
        if i == len(bus_stop) or line != bus_stop[i].bus_n:

            start_name = bus_stop[line_index].departs_from
            departure = bus_stop[line_index].departure
            end_name = bus_stop[i - 1].arrives_to
            arrival = bus_stop[i - 1].arrival
            line_n = bus_stop[line_index].bus_n
            collapsed_stops.append(
                BusStop(start_name, departure, end_name, arrival, line_n)
            )

            line_index = i
            if i < len(bus_stop):
                line = bus_stop[i].bus_n

    for s in collapsed_stops:
        print(
            f"{s.bus_n}: {s.departs_from} at {s.departure} -> {s.arrives_to} at {s.arrival}"
        )
