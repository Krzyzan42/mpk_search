from pathfinder import Pathfinder
from utils import pretty_print_bus_stops
import sys
import time
import random
from tabu import Tabu, Solution


def get_cost_function(initial_time, minute_cost, transfer_cost, km_cost):

    def calculate_path(sol: Solution):
        stops = sol.bus_stops

        line = None
        time = initial_time
        total_cost = 0
        full_path = []

        for i in range(len(stops) - 1):
            a = stops[i]
            b = stops[i + 1]
            result = pathfinder.find_path(
                a,
                b,
                time,
                starting_line=line,
                minute_cost=minute_cost,
                transfer_cost=transfer_cost,
                km_cost=km_cost,
            )
            if not result:
                return 10000000

            partial_path, cost = result
            full_path.extend(partial_path)

            last_stop = partial_path[-1]

            line = last_stop.bus_n
            time = last_stop.arrival
            total_cost += cost

        return total_cost, full_path
    return calculate_path


def two_swap_neighbourhood(sol: Solution) -> list[Solution]:
    neighbourhood = []

    for _ in range(8):
        swaps = random.sample(range(1, len(sol.bus_stops) - 1), 3)
        route = []
        route.extend(sol.bus_stops)
        route[swaps[0]] = sol.bus_stops[swaps[1]]
        route[swaps[1]] = sol.bus_stops[swaps[0]]
        neighbourhood.append(Solution(route))
    return neighbourhood


pathfinder = Pathfinder.from_csv("connection_graph.csv")

# starting_point = input('Przystanek początkowy: ')
# visited_stops = input('Przystanki do odwiedzenia: ')
# optimize = input('Kryterium optymalizacyjne, t/p: ')
# starting_time = input('Czas początkowy: ')

starting_point = "Tramwajowa"
visited_stops = 'Kępa Mieszczańska;Wyszyńskiego;Kochanowskiego;Sanocka'
optimize = 'p'
starting_time = '8:00'

time_cost = 1 if optimize == 't' else 0
transfer_cost = 1 if optimize == 'p' else 0

path = [starting_point] + visited_stops.split(';') + [starting_point]
tabu = Tabu(
    initial_solution=Solution(path),
    calculate_cost=get_cost_function(starting_time, time_cost, transfer_cost, 0),
    generate_neighborhood=two_swap_neighbourhood,
)

start = time.time()
solution, cost, path = tabu.run(1)
end = time.time()

print(f'Found solution: {"->".join(solution.bus_stops)}')
print(f"Time taken: {end - start:.2f}s. Path cost: {cost}", file=sys.stderr)
pretty_print_bus_stops(path)

