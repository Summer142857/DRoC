# Vehicle Routing Problem with Multiple Depots

from gurobipy import Model, GRB, quicksum

def solve(distance_matrix: list, num_vehicle: int, starts: list, ends: list):
    """
    Args:
        distance_matrix: contains the integer distance between customers
        num_vehicle: the number of the vehicle
        starts: the index of the multiple starting depot for vehicles
        ends: the index of the multiple ending depot for vehicles

    Returns:
        obj: a number representing the objective value of the solution
    """
    num_nodes = len(distance_matrix)
    nodes = range(num_nodes)
    vehicles = range(num_vehicle)

    # Create the model
    model = Model("VRPMD")

    # Decision variables: x[i, j, k] is 1 if vehicle k travels from node i to node j
    x = model.addVars(nodes, nodes, vehicles, vtype=GRB.BINARY, name="x")

    # Objective: minimize total travel distance
    model.setObjective(
        quicksum(distance_matrix[i][j] * x[i, j, k] for i in nodes for j in nodes for k in vehicles), 
        GRB.MINIMIZE
    )

    # Constraints: each node is visited exactly once by exactly one vehicle
    for i in nodes:
        if i not in starts and i not in ends:  # Exclude depot nodes
            model.addConstr(quicksum(x[i, j, k] for j in nodes for k in vehicles if j != i) == 1)

    # Flow conservation constraints for each vehicle at each node
    for k in vehicles:
        for j in nodes:
            model.addConstr(
                quicksum(x[i, j, k] for i in nodes if i != j) == quicksum(x[j, l, k] for l in nodes if l != j)
            )

    # Ensure vehicles start and end at the correct depots
    for k in vehicles:
        model.addConstr(quicksum(x[starts[k], j, k] for j in nodes if j != starts[k]) == 1)
        model.addConstr(quicksum(x[i, ends[k], k] for i in nodes if i != ends[k]) == 1)

    # Optimize the model
    model.optimize()

    # Retrieve the objective value
    if model.status == GRB.OPTIMAL:
        obj = model.objVal
    else:
        obj = -1

    return obj
