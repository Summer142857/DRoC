# Vehicle Routing with Pickups and Deliveries, Time Windows, and Duration Limit (PDPTWL)
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

def solve(time_matrix: list, time_windows: list, pickups_deliveries: list, num_vehicle: int, depot: int, duration_limit: int):
    # Create the routing index manager
    # This manager maps the nodes to indices used in the routing model
    manager = pywrapcp.RoutingIndexManager(len(time_matrix), num_vehicle, depot)

    # Create Routing Model
    # The routing model is used to solve the vehicle routing problem
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback
    # This callback returns the travel time between two nodes
    def time_callback(from_index, to_index):
        # Convert from routing variable Index to time matrix NodeIndex
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return time_matrix[from_node][to_node]

    # Register the transit callback with the routing model
    transit_callback_index = routing.RegisterTransitCallback(time_callback)

    # Define cost of each arc
    # The cost is defined as the travel time between nodes
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Time Windows constraint
    # This constraint ensures that each vehicle operates within a time window
    routing.AddDimension(
        transit_callback_index,
        30,  # allow waiting time
        duration_limit,  # maximum time per vehicle
        False,  # Don't force start cumul to zero.
        'Time')
    time_dimension = routing.GetDimensionOrDie('Time')

    # Add time window constraints for each location except depot
    for location_idx, (start, end) in enumerate(time_windows):
        if location_idx == depot:
            continue
        index = manager.NodeToIndex(location_idx)
        # Set the time window for each location
        time_dimension.CumulVar(index).SetRange(start, end)

    # Add pickup and delivery constraints
    # Ensure that each pickup and delivery pair is handled by the same vehicle
    for pickup, delivery in pickups_deliveries:
        pickup_index = manager.NodeToIndex(pickup)
        delivery_index = manager.NodeToIndex(delivery)
        routing.AddPickupAndDelivery(pickup_index, delivery_index)
        # Ensure that the same vehicle performs both pickup and delivery
        routing.solver().Add(routing.VehicleVar(pickup_index) == routing.VehicleVar(delivery_index))
        # Ensure that delivery happens after pickup
        routing.solver().Add(time_dimension.CumulVar(pickup_index) <= time_dimension.CumulVar(delivery_index))

    # Setting first solution heuristic
    # Use the PATH_CHEAPEST_ARC strategy to find an initial solution
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Solve the problem
    solution = routing.SolveWithParameters(search_parameters)

    # Return the objective value
    # If a solution is found, return the objective value, otherwise return -1
    if solution:
        obj = solution.ObjectiveValue()
    else:
        obj = -1
    return obj