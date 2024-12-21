# Vehicle Routing with Pickups and Deliveries (PDP)
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

def solve(distance_matrix: list, pickups_deliveries: list, num_vehicle: int, depot: int):
    # Create the routing index manager
    # This manager maps the nodes to indices and vice versa
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), num_vehicle, depot)

    # Create Routing Model
    # The routing model is used to define the problem and find the solution
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback
    # This callback returns the distance between two nodes
    def distance_callback(from_index, to_index):
        # Convert from routing variable Index to distance matrix NodeIndex
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]

    # Register the distance callback with the routing model
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc
    # The cost is defined as the distance between nodes
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Distance constraint
    dimension_name = 'Distance'
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        3000,  # vehicle maximum travel distance
        True,  # start cumul to zero
        dimension_name)
    # Get the distance dimension to add constraints later
    distance_dimension = routing.GetDimensionOrDie(dimension_name)

    # Add Pickup and Delivery constraints
    for request in pickups_deliveries:
        # Convert pickup and delivery nodes to indices
        pickup_index = manager.NodeToIndex(request[0])
        delivery_index = manager.NodeToIndex(request[1])
        # Add the pickup and delivery pair to the routing model
        routing.AddPickupAndDelivery(pickup_index, delivery_index)
        # Ensure that the same vehicle performs both pickup and delivery
        routing.solver().Add(
            routing.VehicleVar(pickup_index) == routing.VehicleVar(delivery_index))
        # Ensure that the delivery happens after the pickup
        routing.solver().Add(
            distance_dimension.CumulVar(pickup_index) <= distance_dimension.CumulVar(delivery_index))

    # Setting first solution heuristic
    # Use the PATH_CHEAPEST_ARC strategy to find an initial solution
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Solve the problem
    solution = routing.SolveWithParameters(search_parameters)

    # Return the objective value
    # If a solution is found, return its objective value, otherwise return -1
    if solution:
        return solution.ObjectiveValue()
    else:
        return -1