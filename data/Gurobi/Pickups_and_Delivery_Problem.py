# Pickups and Deliveries (PDP) Problem Solver using Gurobi

import gurobipy as gp
from gurobipy import GRB

def solve(distance_matrix: list, pickups_deliveries: list, num_vehicle: int, depot: int):
    """
    Args:
        distance_matrix: contains the integer distance between customers
        pickups_deliveries: a list of pairs of pickup and delivery locations
        num_vehicle: the number of the vehicle
        depot: the index of the depot node

    Returns:
        obj: a number representing the objective value of the solution
    """
    # Create a new model
    model = gp.Model("VRP_PDP")

    # Get the number of nodes
    num_nodes = len(distance_matrix)

    # Create variables
    x = model.addVars(num_nodes, num_nodes, num_vehicle, vtype=GRB.BINARY, name="x")
    u = model.addVars(num_nodes, num_vehicle, vtype=GRB.CONTINUOUS, name="u")

    # Set objective
    model.setObjective(
        gp.quicksum(distance_matrix[i][j] * x[i, j, k]
                    for i in range(num_nodes)
                    for j in range(num_nodes)
                    for k in range(num_vehicle)),
        GRB.MINIMIZE
    )

    # Add constraints
    # Each node is visited exactly once
    for j in range(num_nodes):
        if j != depot:
            model.addConstr(gp.quicksum(x[i, j, k] for i in range(num_nodes) for k in range(num_vehicle) if i != j) == 1)

    # Flow conservation
    for k in range(num_vehicle):
        for j in range(num_nodes):
            model.addConstr(
                gp.quicksum(x[i, j, k] for i in range(num_nodes) if i != j) ==
                gp.quicksum(x[j, i, k] for i in range(num_nodes) if i != j)
            )

    # Subtour elimination
    M = num_nodes
    for i in range(num_nodes):
        for j in range(num_nodes):
            if i != j and (i != depot and j != depot):
                for k in range(num_vehicle):
                    model.addConstr(u[i, k] - u[j, k] + M * x[i, j, k] <= M - 1)

    # Pickups and deliveries
    for pickup, delivery in pickups_deliveries:
        for k in range(num_vehicle):
            model.addConstr(gp.quicksum(x[pickup, j, k] for j in range(num_nodes) if j != pickup) ==
                            gp.quicksum(x[i, delivery, k] for i in range(num_nodes) if i != delivery))
            model.addConstr(u[pickup, k] <= u[delivery, k])

    # All vehicles start and end at the depot
    for k in range(num_vehicle):
        model.addConstr(gp.quicksum(x[depot, j, k] for j in range(num_nodes) if j != depot) == 1)
        model.addConstr(gp.quicksum(x[i, depot, k] for i in range(num_nodes) if i != depot) == 1)

    # Optimize the model
    model.optimize()

    # Get the objective value
    if model.status == GRB.OPTIMAL:
        obj = model.objVal
    else:
        obj = -1

    return obj