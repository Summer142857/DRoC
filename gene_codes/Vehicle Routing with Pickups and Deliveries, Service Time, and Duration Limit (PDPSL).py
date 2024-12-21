# Vehicle Routing with Pickups and Deliveries, Service Time, and Duration Limit (PDPSL)
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

def solve(time_matrix: list, pickups_deliveries: list, num_vehicle: int, depot: int, service_time: list, duration_limit: int):
    """
    Args:
        time_matrix: contains the integer travel times between customers
        pickups_deliveries: a list of pairs of pickup and delivery locations
        num_vehicle: the number of the vehicle
        depot: the index of the depot node
        service_time: service time for each customer node
        duration_limit: the time duration of each route is upper bounded by the duration limit

    Returns:
        obj: a number representing the objective value of the solution
    """
    # Create the routing index manager
    manager = pywrapcp.RoutingIndexManager(len(time_matrix), num_vehicle, depot)

    # Create Routing Model
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback
    def time_callback(from_index, to_index):
        # Convert from routing variable Index to time matrix NodeIndex
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return time_matrix[from_node][to_node] + service_time[from_node]

    # Register the transit callback with the routing model
    transit_callback_index = routing.RegisterTransitCallback(time_callback)

    # Define cost of each arc
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Time Dimension
    time = 'Time'
    routing.AddDimension(
        transit_callback_index,
        30,  # allow waiting time
        duration_limit,  # maximum time per vehicle
        False,  # Don't force start cumul to zero.
        time)
    time_dimension = routing.GetDimensionOrDie(time)

    # Add Pickup and Delivery constraints
    for request in pickups_deliveries:
        pickup_index = manager.NodeToIndex(request[0])
        delivery_index = manager.NodeToIndex(request[1])
        routing.AddPickupAndDelivery(pickup_index, delivery_index)
        routing.solver().Add(
            routing.VehicleVar(pickup_index) == routing.VehicleVar(delivery_index))
        routing.solver().Add(
            time_dimension.CumulVar(pickup_index) <= time_dimension.CumulVar(delivery_index))

    # Setting first solution heuristic
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Solve the problem
    solution = routing.SolveWithParameters(search_parameters)

    # Return the objective value
    if solution:
        return solution.ObjectiveValue()
    else:
        return -1