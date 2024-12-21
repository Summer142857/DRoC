# Prize Collecting Vehicle Routing Problem (PCVRP)

import gurobipy as gp
from gurobipy import GRB

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
    # Create a new model
    model = gp.Model("PCVRP")

    # Get the number of nodes
    n = len(distance_matrix)

    # Create variables
    x = model.addVars(n, n, num_vehicle, vtype=GRB.BINARY, name="x")
    y = model.addVars(n, num_vehicle, vtype=GRB.BINARY, name="y")

    # Set objective: minimize travel distance + value of dropped nodes
    travel_distance = gp.quicksum(distance_matrix[i][j] * x[i, j, k]
                                  for i in range(n) for j in range(n) for k in range(num_vehicle))
    dropped_value = gp.quicksum(prizes[i] * (1 - gp.quicksum(y[i, k] for k in range(num_vehicle)))
                                for i in range(n) if i != depot)
    obj = travel_distance + dropped_value
    model.setObjective(obj, GRB.MINIMIZE)


    # Add constraints
    # Each node is visited at most once
    model.addConstrs(gp.quicksum(y[i, k] for k in range(num_vehicle)) <= 1 for i in range(n) if i != depot)

    # Flow conservation
    model.addConstrs(gp.quicksum(x[i, j, k] for j in range(n) if j != i) ==
                     gp.quicksum(x[j, i, k] for j in range(n) if j != i)
                     for i in range(n) for k in range(num_vehicle))

    # Link x and y variables
    model.addConstrs(gp.quicksum(x[i, j, k] for j in range(n) if j != i) == y[i, k]
                     for i in range(n) for k in range(num_vehicle))

    # Ensure each route starts and ends at the depot
    model.addConstrs(gp.quicksum(x[depot, j, k] for j in range(n) if j != depot) == 1 for k in range(num_vehicle))
    model.addConstrs(gp.quicksum(x[i, depot, k] for i in range(n) if i != depot) == 1 for k in range(num_vehicle))

    # Maximum travel distance constraint
    model.addConstrs(gp.quicksum(distance_matrix[i][j] * x[i, j, k] for i in range(n) for j in range(n)) <= max_distance
                     for k in range(num_vehicle))

    # Optimize model
    model.optimize()

    # Get the objective value
    if model.status == GRB.OPTIMAL:
        return model.objVal
    else:
        return -1