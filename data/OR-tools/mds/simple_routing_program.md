# 

# simple_routing_program
First, you must install [ortools](https://pypi.org/project/ortools/) package in this colab.

```
%pip install ortools
```

Vehicle Routing example.

```
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


def main():
    """Entry point of the program."""
    # Instantiate the data problem.
    num_locations = 5
    num_vehicles = 1
    depot = 0

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(num_locations, num_vehicles, depot)

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback.
    def distance_callback(from_index, to_index):
        """Returns the absolute difference between the two nodes."""
        # Convert from routing variable Index to user NodeIndex.
        from_node = int(manager.IndexToNode(from_index))
        to_node = int(manager.IndexToNode(to_index))
        return abs(to_node - from_node)

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )  # pylint: disable=no-member

    # Solve the problem.
    assignment = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    print(f"Objective: {assignment.ObjectiveValue()}")
    index = routing.Start(0)
    plan_output = "Route for vehicle 0:\n"
    route_distance = 0
    while not routing.IsEnd(index):
        plan_output += f"{manager.IndexToNode(index)} -> "
        previous_index = index
        index = assignment.Value(routing.NextVar(index))
        route_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
    plan_output += f"{manager.IndexToNode(index)}\n"
    plan_output += f"Distance of the route: {route_distance}m\n"
    print(plan_output)


main()
```
