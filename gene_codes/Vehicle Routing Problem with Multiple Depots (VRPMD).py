# Vehicle Routing Problem with Multiple Depots (VRPMD)
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

def solve(distance_matrix: list, num_vehicle: int, starts: list, ends: list):
    """
    Args:
        distance_matrix: contains the integer distance between customers
        num_vehicle: the number of the vehicle
        starts: the index of the starting depot for vehicles
        ends: the index of the ending depot for vehicles 

    Returns:
        obj: a number representing the objective value of the solution
    """
    # Create the routing index manager
    # This manager handles the conversion between the node indices and the routing indices
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), num_vehicle, starts, ends)

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
    # Set the cost of travel between nodes for all vehicles
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Set search parameters
    # Configure the search strategy for the solver
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Solve the problem
    # Attempt to find a solution to the routing problem
    solution = routing.SolveWithParameters(search_parameters)

    # Return the objective value
    # If a solution is found, return its objective value; otherwise, return -1
    if solution:
        obj = solution.ObjectiveValue()
    else:
        obj = -1
    return obj
