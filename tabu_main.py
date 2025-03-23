from pathfinder import Pathfinder
import random
from tabu import Tabu, Solution

inital_time = "8:00"
optimize = "t"


def calculate_path(sol: Solution):
    stops = sol.bus_stops

    line = None
    time = inital_time
    total_cost = 0

    solution_stops = []
    for i in range(len(stops) - 1):
        a = stops[i]
        b = stops[i + 1]
        partial_path = pathfinder.find_path(
            a, b, time, starting_line=line, minute_cost=0, transfer_cost=5, km_cost=0
        )
        if partial_path[0] is None or partial_path[1] is None:
            raise ValueError("Couldnt find the path")

        last_stop = partial_path[0][-1]
        cost = partial_path[1]

        line = last_stop.bus_n
        time = last_stop.time
        total_cost += cost

        if len(solution_stops) == 0:
            solution_stops.extend(partial_path[0])
        else:
            solution_stops.extend(partial_path[1:])

        string = ''
        for b in partial_path[0]:
            string += str(b) + ', '
        print(string)


    path = ", ".join(sol.bus_stops)
    print(f"{total_cost} : {path}")
    return total_cost


def generate_neighbourhood(sol: Solution) -> list[Solution]:
    neighbourhood = []
    initial = sol.bus_stops[0]
    stops = sol.bus_stops[1:-1]
    last = sol.bus_stops[-1]

    for _ in range(20):
        swaps = random.sample(range(1, len(sol.bus_stops) - 1), 2)
        route = []
        route.extend(sol.bus_stops)
        route[swaps[0]] = sol.bus_stops[swaps[1]]
        route[swaps[1]] = sol.bus_stops[swaps[0]]
        neighbourhood.append(Solution(route))
    return neighbourhood


pathfinder = Pathfinder.from_csv('connection_graph.csv')
path = []
tabu = Tabu(
    initial_solution=Solution(
        [
            "Tramwajowa",
            "Kępa Mieszczańska",
            "Wyszyńskiego",
            "Kochanowskiego",
            "Sanocka",
            "Tramwajowa",
        ]
    ),
    calculate_cost=calculate_path,
    generate_neighborhood=generate_neighbourhood,
)
tabu.run(100)
