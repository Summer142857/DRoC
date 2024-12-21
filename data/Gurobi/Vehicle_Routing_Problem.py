# Vehicle Routing Problem (VRP) Solver using Gurobi

from gurobipy import Model, GRB, quicksum


def solve(distance_matrix: list, num_vehicle: int, depot: int):
    """
    Args:
        distance_matrix: contains the integer distance between customers
        num_vehicle: the number of the vehicle
        depot: dummy depot

    Returns:
        obj: a number representing the objective value of the solution
    """
    n = len(distance_matrix)

    # Create a new model
    model = Model("VRP")

    # Create variables
    x = model.addVars(n, n, vtype=GRB.BINARY, name="x")
    u = model.addVars(n, vtype=GRB.CONTINUOUS, name="u")

    # Set objective
    model.setObjective(quicksum(distance_matrix[i][j] * x[i, j] for i in range(n) for j in range(n)), GRB.MINIMIZE)

    # Add constraints
    # Each customer is visited exactly once
    for j in range(n):
        if j != depot:
            model.addConstr(quicksum(x[i, j] for i in range(n) if i != j) == 1)

    # Flow conservation
    for j in range(n):
        if j != depot:
            model.addConstr(quicksum(x[i, j] for i in range(n) if i != j) ==
                            quicksum(x[j, i] for i in range(n) if i != j))

    # Subtour elimination
    for i in range(n):
        for j in range(n):
            if i != j and (i != depot and j != depot):
                model.addConstr(u[i] - u[j] + n * x[i, j] <= n - 1)

    # Number of vehicles constraint
    model.addConstr(quicksum(x[depot, j] for j in range(n) if j != depot) <= num_vehicle)
    model.addConstr(quicksum(x[i, depot] for i in range(n) if i != depot) <= num_vehicle)

    # Optimize model
    model.optimize()

    # Get objective value
    if model.status == GRB.OPTIMAL:
        obj = model.objVal
    else:
        obj = -1

    return obj