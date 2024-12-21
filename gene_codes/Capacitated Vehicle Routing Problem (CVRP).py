# Capacitated Vehicle Routing Problem (CVRP)
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def solve(distance_matrix: list, demands: list, num_vehicle: int, vehicle_capacity: list, depot: int):
    """
    Args:
        distance_matrix: contains the integer distance between customers
        demands: the list of integer customer demands
        num_vehicle: the number of the vehicle
        vehicle_capacities: the capacity of each vehicle
        depot: the index of the depot node

    Returns:
        obj: a number representing the objective value of the solution
    """
    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), num_vehicle, depot)

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
        vehicle_capacity,  # vehicle maximum capacities
        True,  # start cumul to zero
        "Capacity",
    )

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Return the objective value of the solution.
    if solution:
        return solution.ObjectiveValue()
    else:
        return -1