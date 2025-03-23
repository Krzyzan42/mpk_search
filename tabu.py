from collections.abc import Callable
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class Solution:
    bus_stops: list[str]

    def __eq__(self, other) -> bool:
        if not isinstance(other, Solution):
            return False
        return self.bus_stops == other.bus_stops


class Tabu:
    initial_solution: Solution
    calculate_cost: Callable
    generate_neighborhood: Callable

    def __init__(
        self,
        initial_solution: Solution,
        calculate_cost: Callable,
        generate_neighborhood: Callable,
    ):
        self.initial_solution = initial_solution
        self.calculate_cost = calculate_cost
        self.generate_neighborhood = generate_neighborhood

    def find_best_neighbour(
        self, neighbours: list[Solution], tabu
    ) -> Tuple[Optional[Solution], float]:
        best_neighbour = None
        best_neighbour_cost = float("inf")

        for n in neighbours:
            if n in tabu:
                continue

            cost = self.calculate_cost(n)
            if cost < best_neighbour_cost:
                best_neighbour = n
                best_neighbour_cost = cost

        return best_neighbour, best_neighbour_cost

    def run(self, iterations: int):

        current_solution = self.initial_solution
        current_cost = self.calculate_cost(current_solution)

        best_solution = current_solution
        best_cost = current_cost
        tabu: list[Solution] = []

        for _ in range(iterations):

            neighborhood: list[Solution] = self.generate_neighborhood(current_solution)
            new_solution, new_cost = self.find_best_neighbour(neighborhood, tabu)
            if not new_solution:
                return best_solution, best_cost
            while len(tabu) > 3 * len(current_solution.bus_stops):
                tabu.remove(tabu[0])

            tabu.append(new_solution)
            tabu.extend(neighborhood)

            current_solution = new_solution
            current_cost = new_cost

            if current_cost < best_cost:
                best_solution = current_solution
                best_cost = current_cost
                print("New best solution!")

            print(f"Finished iteration")
            print(
                f'Found {current_cost} cost solution: {"->".join(current_solution.bus_stops)}'
            )

        return best_solution, best_cost


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
