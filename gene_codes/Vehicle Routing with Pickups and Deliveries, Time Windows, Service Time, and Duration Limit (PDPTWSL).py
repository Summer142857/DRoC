# Vehicle Routing with Pickups and Deliveries, Time Windows, Service Time, and Duration Limit (PDPTWSL)
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

def solve(time_matrix: list, time_windows: list, pickups_deliveries: list, num_vehicle: int, depot: int, service_time: list, duration_limit: int):
    # Create the routing index manager
    # The manager is responsible for handling the conversion between the node indices and the routing indices.
    manager = pywrapcp.RoutingIndexManager(len(time_matrix), num_vehicle, depot)

    # Create Routing Model
    # The routing model is the main component that will solve the vehicle routing problem.
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback
    # This callback returns the travel time between two nodes, including the service time at the from_node.
    def time_callback(from_index, to_index):
        # Convert routing indices to node indices in the time matrix.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        # Return the travel time between the two nodes plus the service time at the from_node.
        return time_matrix[from_node][to_node] + service_time[from_node]

    # Register the transit callback with the routing model.
    transit_callback_index = routing.RegisterTransitCallback(time_callback)

    # Define cost of each arc
    # The cost of each arc is defined by the transit callback, which is the travel time.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Time Windows constraint
    # This dimension keeps track of the time at each location and ensures that the time windows are respected.
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
        # Set the time window for each location.
        index = manager.NodeToIndex(location_idx)
        time_dimension.CumulVar(index).SetRange(start, end)

    # Add pickup and delivery constraints
    for pickup, delivery in pickups_deliveries:
        # Convert node indices to routing indices.
        pickup_index = manager.NodeToIndex(pickup)
        delivery_index = manager.NodeToIndex(delivery)
        # Add the pickup and delivery pair to the routing model.
        routing.AddPickupAndDelivery(pickup_index, delivery_index)
        # Ensure that the same vehicle performs both the pickup and delivery.
        routing.solver().Add(routing.VehicleVar(pickup_index) == routing.VehicleVar(delivery_index))
        # Ensure that the delivery happens after the pickup.
        routing.solver().Add(time_dimension.CumulVar(pickup_index) <= time_dimension.CumulVar(delivery_index))

    # Setting first solution heuristic
    # Use the PATH_CHEAPEST_ARC strategy to find an initial solution quickly.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Solve the problem
    # Attempt to find a solution to the routing problem with the given parameters.
    solution = routing.SolveWithParameters(search_parameters)

    # Return the objective value
    # If a solution is found, return the objective value (total travel time). Otherwise, return -1.
    if solution:
        return solution.ObjectiveValue()
    else:
        return -1
