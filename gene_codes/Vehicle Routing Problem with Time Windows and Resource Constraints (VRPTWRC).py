# Vehicle Routing Problem with Time Windows and Resource Constraints (VRPTWRC)
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def solve(time_matrix: list, time_windows: list, num_vehicle: int, vehicle_load_time: int, vehicle_unload_time: int, depot_capacity: int, depot: int):
    obj = -1  # Initialize the objective value to -1, which will be updated if a solution is found.
    
    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(time_matrix), num_vehicle, depot)

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback.
    def time_callback(from_index, to_index):
        # Convert from routing variable Index to time matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return time_matrix[from_node][to_node]  # Return the travel time between nodes.

    transit_callback_index = routing.RegisterTransitCallback(time_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Time Windows constraint.
    time = "Time"
    routing.AddDimension(
        transit_callback_index,
        30,  # allow waiting time
        30,  # maximum time per vehicle
        False,  # Don't force start cumul to zero.
        time,
    )
    time_dimension = routing.GetDimensionOrDie(time)

    # Add time window constraints for each location except depot.
    for location_idx, time_window in enumerate(time_windows):
        if location_idx == depot:
            continue  # Skip the depot as it has a different constraint.
        index = manager.NodeToIndex(location_idx)
        time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])  # Set time window for each location.

    # Add time window constraints for each vehicle start node.
    for vehicle_id in range(num_vehicle):
        index = routing.Start(vehicle_id)
        time_dimension.CumulVar(index).SetRange(
            time_windows[depot][0],
            time_windows[depot][1]
        )  # Set time window for the start of each vehicle.

    # Add resource constraints at the depot.
    solver = routing.solver()
    intervals = []
    for i in range(num_vehicle):
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
    depot_usage = [1 for _ in range(len(intervals))]  # Each interval uses one unit of depot capacity.
    solver.Add(
        solver.Cumulative(intervals, depot_usage, depot_capacity, "depot")  # Ensure depot capacity is not exceeded.
    )

    # Instantiate route start and end times to produce feasible times.
    for i in range(num_vehicle):
        routing.AddVariableMinimizedByFinalizer(
            time_dimension.CumulVar(routing.Start(i))
        )
        routing.AddVariableMinimizedByFinalizer(
            time_dimension.CumulVar(routing.End(i))
        )

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)  # Use the PATH_CHEAPEST_ARC strategy.

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Return the objective value.
    if solution:
        obj = solution.ObjectiveValue()  # Update the objective value if a solution is found.

    return obj  # Return the objective value, -1 if no solution is found.