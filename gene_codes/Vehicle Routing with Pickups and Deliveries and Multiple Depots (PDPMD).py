# Vehicle Routing with Pickups and Deliveries and Multiple Depots (PDPMD)
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

def solve(distance_matrix: list, pickups_deliveries: list, num_vehicle: int, starts: list, ends: list):
    """
    Args:
        distance_matrix: contains the integer distance between customers
        pickups_deliveries: a list of pairs of pickup and delivery locations
        num_vehicle: the number of the vehicle
        starts: the index of the starting depot for vehicles
        ends: the index of the ending depot for vehicles

    Returns:
        obj: a number representing the objective value of the solution
    """
    # Create the routing index manager
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), num_vehicle, starts, ends)

    # Create Routing Model
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback
    def distance_callback(from_index, to_index):
        # Convert from routing variable Index to distance matrix NodeIndex
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]

    # Register the transit callback with the routing model
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc using the transit callback
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Distance constraint
    dimension_name = 'Distance'
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        3000,  # vehicle maximum travel distance
        True,  # start cumul to zero
        dimension_name)
    # Get the distance dimension to use for constraints
    distance_dimension = routing.GetDimensionOrDie(dimension_name)

    # Add Pickup and Delivery constraints
    for request in pickups_deliveries:
        # Convert pickup and delivery nodes to indices
        pickup_index = manager.NodeToIndex(request[0])
        delivery_index = manager.NodeToIndex(request[1])
        # Add pickup and delivery to the routing model
        routing.AddPickupAndDelivery(pickup_index, delivery_index)
        # Ensure that pickup and delivery happen on the same vehicle
        routing.solver().Add(
            routing.VehicleVar(pickup_index) == routing.VehicleVar(delivery_index))
        # Ensure that delivery happens after pickup
        routing.solver().Add(
            distance_dimension.CumulVar(pickup_index) <= distance_dimension.CumulVar(delivery_index))

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