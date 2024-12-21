# Capacitated Vehicle Routing Problem with Time Windows and Resource Constraints (CVRPTWRC)
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
def solve(time_matrix: list, time_windows: list, demands: list, vehicle_capacities: list, num_vehicles: int, depot: int, vehicle_load_time: int, vehicle_unload_time: int, depot_capacity: int):
    """
    Args:
        time_matrix: contains the integer travel times between locations
        time_windows: the list of tuples for time windows of the customers
        demands: the list of integer customer demands
        vehicle_capacities: the capacity of each vehicle
        num_vehicles: the number of the vehicle
        depot: the index of the depot node
        vehicle_load_time: the time required to load a vehicle at depot
        vehicle_unload_time: the time required to unload a vehicle at depot
        depot_capacity: the maximum number of vehicles that can load or unload at the same time 

    Returns:
        obj: a number representing the objective value of the solution
    """
    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(time_matrix), num_vehicles, depot)

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback.
    def time_callback(from_index, to_index):
        """Returns the travel time between the two nodes."""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return time_matrix[from_node][to_node]

    # Register the transit callback with the routing model
    transit_callback_index = routing.RegisterTransitCallback(time_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Capacity constraint.
    def demand_callback(from_index):
        """Returns the demand of the node."""
        from_node = manager.IndexToNode(from_index)
        return demands[from_node]

    # Register the demand callback with the routing model
    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        vehicle_capacities,  # vehicle maximum capacities
        True,  # start cumul to zero
        "Capacity",
    )

    # Add Time Windows constraint.
    time = "Time"
    routing.AddDimension(
        transit_callback_index,
        30,  # allow waiting time
        30,  # maximum time per vehicle
        False,  # Don't force start cumul to zero.
        time,
    )
    # Get the time dimension from the routing model
    time_dimension = routing.GetDimensionOrDie(time)

    # Add time window constraints for each location except depot.
    for location_idx, time_window in enumerate(time_windows):
        if location_idx == depot:
            continue
        index = manager.NodeToIndex(location_idx)
        time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])

    # Add time window constraints for each vehicle start node.
    for vehicle_id in range(num_vehicles):
        index = routing.Start(vehicle_id)
        time_dimension.CumulVar(index).SetRange(
            time_windows[depot][0], time_windows[depot][1]
        )

    # Add resource constraints at the depot.
    solver = routing.solver()
    intervals = []
    for i in range(num_vehicles):
        # Add time windows at start of routes
        intervals.append(
            solver.FixedDurationIntervalVar(
                time_dimension.CumulVar(routing.Start(i)),
                vehicle_load_time,
                "depot_interval",
            )
        )
        # Add time windows at end of routes.
        intervals.append(
            solver.FixedDurationIntervalVar(
                time_dimension.CumulVar(routing.End(i)),
                vehicle_unload_time,
                "depot_interval",
            )
        )
    # Define the usage of depot resources
    depot_usage = [1 for _ in range(len(intervals))]
    # Add cumulative constraint to limit the number of vehicles at the depot
    solver.Add(
        solver.Cumulative(intervals, depot_usage, depot_capacity, "depot")
    )

    # Instantiate route start and end times to produce feasible times.
    for i in range(num_vehicles):
        routing.AddVariableMinimizedByFinalizer(
            time_dimension.CumulVar(routing.Start(i))
        )
        routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(routing.End(i)))

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    # Use guided local search as the metaheuristic
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    # Set a time limit for the search
    search_parameters.time_limit.FromSeconds(1)

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Return the objective value of the solution.
    if solution:
        return solution.ObjectiveValue()
    else:
        return -1