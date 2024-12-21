# Capacitated Vehicle Routing Problem with Distance Limit (CVRPL)
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

def solve(distance_matrix: list, demands: list, num_vehicle: int, vehicle_capacities: list, depot: int, distance_limit: int):
    # Create the routing index manager
    # The manager handles the conversion between the node indices and the routing indices
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), num_vehicle, depot)

    # Create Routing Model
    # The routing model is used to define the problem and find the solution
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback
    def distance_callback(from_index, to_index):
        # Returns the distance between the two nodes
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]

    # Register the distance callback with the routing model
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc
    # The cost is defined as the distance between nodes
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Capacity constraint
    def demand_callback(from_index):
        # Returns the demand of the node
        from_node = manager.IndexToNode(from_index)
        return demands[from_node]

    # Register the demand callback with the routing model
    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        vehicle_capacities,  # vehicle maximum capacities
        True,  # start cumul to zero
        'Capacity')

    # Add Distance constraint
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        distance_limit,  # maximum distance per vehicle
        True,  # start cumul to zero
        'Distance')

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
        return solution.ObjectiveValue()
    else:
        return -1
