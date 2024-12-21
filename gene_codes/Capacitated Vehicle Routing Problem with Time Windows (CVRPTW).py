# Capacitated Vehicle Routing Problem with Time Windows (CVRPTW)
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

def solve(time_matrix: list, time_windows: list, demands: list, vehicle_capacities: list, num_vehicle: int, depot: int):
    """
    Args:
        time_matrix: contains the integer travel times between locations
        time_windows: the list of tuples for time windows of the customers
        demands: the list of integer customer demands
        vehicle_capacities: the capacity of each vehicle
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

    # Register the transit callback to be used for arc costs
    transit_callback_index = routing.RegisterTransitCallback(time_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Capacity constraint
    def demand_callback(from_index):
        # Returns the demand of the node.
        from_node = manager.IndexToNode(from_index)
        return demands[from_node]

    # Register the demand callback
    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        vehicle_capacities,  # vehicle maximum capacities
        True,  # start cumul to zero
        'Capacity')

    # Add Time Window constraint
    def time_window_callback(from_index):
        # Returns the time window of the node.
        from_node = manager.IndexToNode(from_index)
        return time_windows[from_node]

    # Register the time window callback
    time_callback_index = routing.RegisterUnaryTransitCallback(time_window_callback)
    routing.AddDimension(
        transit_callback_index,
        30,  # allow waiting time
        30,  # maximum time per vehicle
        False,  # Don't force start cumul to zero.
        'Time')
    time_dimension = routing.GetDimensionOrDie('Time')
    for location_idx, time_window in enumerate(time_windows):
        if location_idx == depot:
            continue
        index = manager.NodeToIndex(location_idx)
        # Set the time window for each location
        time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])

    # Instantiate route start and end times to produce feasible times.
    for vehicle_id in range(num_vehicle):
        index = routing.Start(vehicle_id)
        # Set the time window for the depot
        time_dimension.CumulVar(index).SetRange(time_windows[depot][0], time_windows[depot][1])

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Return the objective value
    if solution:
        obj = solution.ObjectiveValue()
    else:
        obj = -1
    return obj
