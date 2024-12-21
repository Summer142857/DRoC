# tsp
First, you must install [ortools](https://pypi.org/project/ortools/) package in this colab.

```
%pip install ortools
```

Simple Travelling Salesman Problem.

A description of the problem can be found here:
http://en.wikipedia.org/wiki/Travelling_salesperson_problem.

```
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


def create_data_model():
    """Stores the data for the problem."""
    data = {}
    # Locations in block units
    locations = [
        # fmt:off
      (4, 4),  # depot
      (2, 0), (8, 0),  # locations to visit
      (0, 1), (1, 1),
      (5, 2), (7, 2),
      (3, 3), (6, 3),
      (5, 5), (8, 5),
      (1, 6), (2, 6),
      (3, 7), (6, 7),
      (0, 8), (7, 8)
        # fmt:on
    ]
    # Convert locations in meters using a city block dimension of 114m x 80m.
    data["locations"] = [(l[0] * 114, l[1] * 80) for l in locations]
    data["num_vehicles"] = 1
    data["depot"] = 0
    return data


def create_distance_callback(data, manager):
    """Creates callback to return distance between points."""
    distances_ = {}
    index_manager_ = manager
    # precompute distance between location to have distance callback in O(1)
    for from_counter, from_node in enumerate(data["locations"]):
        distances_[from_counter] = {}
        for to_counter, to_node in enumerate(data["locations"]):
            if from_counter == to_counter:
                distances_[from_counter][to_counter] = 0
            else:
                distances_[from_counter][to_counter] = abs(
                    from_node[0] - to_node[0]
                ) + abs(from_node[1] - to_node[1])

    def distance_callback(from_index, to_index):
        """Returns the manhattan distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = index_manager_.IndexToNode(from_index)
        to_node = index_manager_.IndexToNode(to_index)
        return distances_[from_node][to_node]

    return distance_callback


def print_solution(manager, routing, assignment):
    """Prints assignment on console."""
    print(f"Objective: {assignment.ObjectiveValue()}")
    index = routing.Start(0)
    plan_output = "Route for vehicle 0:\n"
    route_distance = 0
    while not routing.IsEnd(index):
        plan_output += f" {manager.IndexToNode(index)} ->"
        previous_index = index
        index = assignment.Value(routing.NextVar(index))
        route_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
    plan_output += f" {manager.IndexToNode(index)}\n"
    plan_output += f"Distance of the route: {route_distance}m\n"
    print(plan_output)


def main():
    """Entry point of the program."""
    # Instantiate the data problem.
    data = create_data_model()

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(
        len(data["locations"]), data["num_vehicles"], data["depot"]
    )

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback.
    distance_callback = create_distance_callback(data, manager)
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    # Solve the problem.
    assignment = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if assignment:
        print_solution(manager, routing, assignment)


main()
```
