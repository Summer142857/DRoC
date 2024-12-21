#!/usr/bin/env python3
# Copyright 2010-2024 Google LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Simple prize collecting TSP problem with a max distance."""

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

DISTANCE_MATRIX = ...

MAX_DISTANCE = 80_000

VISIT_VALUES = [60_000, 50_000, 40_000, 30_000] * (len(DISTANCE_MATRIX) // 4)
VISIT_VALUES[0] = 0


# Create a console solution printer.
def print_solution(manager, routing, assignment):
    """Prints assignment on console."""
    print(f'Objective: {assignment.ObjectiveValue()}')
   # Display dropped nodes.
    dropped_nodes = 'Dropped nodes:'
    for index in range(routing.Size()):
        if routing.IsStart(index) or routing.IsEnd(index):
            continue
        if assignment.Value(routing.NextVar(index)) == index:
            node = manager.IndexToNode(index)
            dropped_nodes += f' {node}({VISIT_VALUES[node]})'
    print(dropped_nodes)
    # Display routes
    index = routing.Start(0)
    plan_output = 'Route for vehicle 0:\n'
    route_distance = 0
    value_collected = 0
    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        value_collected += VISIT_VALUES[node]
        plan_output += f' {node} ->'
        previous_index = index
        index = assignment.Value(routing.NextVar(index))
        route_distance += routing.GetArcCostForVehicle(previous_index, index, 0)

    plan_output += f' {manager.IndexToNode(index)}\n'
    plan_output += f'Distance of the route: {route_distance}m\n'
    plan_output += f'Value collected: {value_collected}/{sum(VISIT_VALUES)}\n'
    print(plan_output)


def main():
    """Entry point of the program."""
    num_nodes = len(DISTANCE_MATRIX)
    print(f'Num nodes = {num_nodes}')
    num_vehicles = 1
    depot = 0
    all_nodes = range(num_nodes)

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(
            num_nodes,
            num_vehicles,
            depot)

    # Create routing model.
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback.
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return DISTANCE_MATRIX[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Limit Vehicle distance.
    dimension_name = 'Distance'
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        MAX_DISTANCE,  # vehicle maximum travel distance
        True,  # start cumul to zero
        dimension_name)


    # Allow to drop nodes.
    for node in range(1, num_nodes):
        routing.AddDisjunction(
                [manager.NodeToIndex(node)],
                VISIT_VALUES[node])

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.FromSeconds(15)
    #search_parameters.log_search = True

    # Solve the problem.
    assignment = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if assignment:
        print_solution(manager, routing, assignment)


if __name__ == '__main__':
    main()
