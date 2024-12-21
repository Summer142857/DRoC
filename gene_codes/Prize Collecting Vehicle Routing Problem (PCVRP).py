# Prize Collecting Vehicle Routing Problem (PCVRP)
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def solve(distance_matrix: list, prizes: list, max_distance: int, num_vehicle: int, depot: int):
    """
    Args:
        distance_matrix: contains the integer distance between customers
        prizes: the value of prize that a vehicle can collect at each node
        max_distance: maximum distance that a vehicle can travel
        num_vehicle: the number of the vehicle
        depot: the index of the depot node

    Returns:
        obj: a number representing the objective value of the solution
    """
    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(
        len(distance_matrix),  # Number of nodes
        num_vehicle,  # Number of vehicles
        depot)  # Depot node index

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback.
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]

    # Register the distance callback with the routing model
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Distance constraint.
    dimension_name = 'Distance'
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        max_distance,  # vehicle maximum travel distance
        True,  # start cumul to zero
        dimension_name)

    # Allow to drop nodes.
    for node in range(1, len(distance_matrix)):
        routing.AddDisjunction([manager.NodeToIndex(node)], prizes[node])

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.FromSeconds(15)

    # Solve the problem.
    assignment = routing.SolveWithParameters(search_parameters)

    # Return the objective value.
    if assignment:
        return assignment.ObjectiveValue()
    else:
        return -1  # Return -1 if no solution is found