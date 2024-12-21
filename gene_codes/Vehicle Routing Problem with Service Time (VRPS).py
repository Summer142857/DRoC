# Vehicle Routing Problem with Service Time (VRPS)
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def solve(time_matrix: list, num_vehicle: int, depot: int, service_time: list):
    """
    Args:
        time_matrix: contains the integer travel times between locations
        num_vehicle: the number of the vehicle
        depot: the index of the depot node
        service_time: service time for each customer node 

    Returns:
        obj: a number representing the objective value of the solution
    """
    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(time_matrix), num_vehicle, depot)

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback.
    def time_callback(from_index, to_index):
        """Returns the travel time between the two nodes including service time."""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return time_matrix[from_node][to_node] + service_time[from_node]

    # Register the transit callback with the routing model.
    transit_callback_index = routing.RegisterTransitCallback(time_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Time Windows constraint.
    time = 'Time'
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        3000,  # maximum time per vehicle
        False,  # Don't force start cumul to zero.
        time)
    # Get the time dimension to add constraints later if needed.
    time_dimension = routing.GetDimensionOrDie(time)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Return the objective value of the solution.
    if solution:
        return solution.ObjectiveValue()
    else:
        return -1