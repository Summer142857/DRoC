# Vehicle Routing Problem with Time Windows (VRPTW)
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

def solve(time_matrix: list, time_windows: list, num_vehicle: int, depot: int):
    """
    Args:
        time_matrix: contains the integer travel times between locations
        time_windows: the list of tuples for time windows of the customers
        num_vehicle: the number of the vehicle
        depot: the index of the depot node

    Returns:
        obj: a number representing the objective value of the solution
    """
    # Create the routing index manager
    manager = pywrapcp.RoutingIndexManager(len(time_matrix), num_vehicle, depot)

    # Create Routing Model
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback
    def time_callback(from_index, to_index):
        # Returns the travel time between the two nodes.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return time_matrix[from_node][to_node]

    # Register the transit callback with the routing model
    transit_callback_index = routing.RegisterTransitCallback(time_callback)

    # Define cost of each arc (edge) in the routing model
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Time Windows constraint
    time = 'Time'
    routing.AddDimension(
        transit_callback_index,
        30,  # allow waiting time
        30,  # maximum time per vehicle
        False,  # Don't force start cumul to zero.
        time)
    # Get the time dimension to add time window constraints
    time_dimension = routing.GetDimensionOrDie(time)

    # Add time window constraints for each location except depot
    for location_idx, (start, end) in enumerate(time_windows):
        if location_idx == depot:
            continue
        # Convert location index to routing index and set time window
        index = manager.NodeToIndex(location_idx)
        time_dimension.CumulVar(index).SetRange(start, end)

    # Instantiate route start and end times to produce feasible times
    for vehicle_id in range(num_vehicle):
        index = routing.Start(vehicle_id)
        # Set time window for the start of each vehicle at the depot
        time_dimension.CumulVar(index).SetRange(time_windows[depot][0], time_windows[depot][1])

    # Setting first solution heuristic
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Solve the problem
    solution = routing.SolveWithParameters(search_parameters)

    # Return the objective value
    if solution:
        obj = solution.ObjectiveValue()
    else:
        obj = -1  # Return -1 if no solution is found
    return obj