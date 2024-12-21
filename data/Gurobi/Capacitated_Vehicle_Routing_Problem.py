# Capacitated Vehicle Routing Problem (CVRP) Solver using Gurobi

from gurobipy import Model, GRB, quicksum

def solve(distance_matrix: list, demands: list, num_vehicle: int, vehicle_capacity: list, depot: int):
    """
    Args:
        distance_matrix: contains the integer distance between customers
        demands: the list of integer customer demands
        num_vehicle: the number of the vehicle
        vehicle_capacity: the capacity of each vehicle
        depot: the index of the depot node

    Returns:
        obj: a number representing the objective value of the solution
    """
    # Create a new model
    model = Model("CVRP")

    # Get the number of customers (including depot)
    n = len(distance_matrix)

    # Create variables
    x = model.addVars(n, n, num_vehicle, vtype=GRB.BINARY, name="x")
    u = model.addVars(n, num_vehicle, vtype=GRB.CONTINUOUS, name="u")

    # Set objective: minimize total distance
    model.setObjective(quicksum(distance_matrix[i][j] * x[i, j, k]
                                for i in range(n) for j in range(n) for k in range(num_vehicle)), GRB.MINIMIZE)

    # Add constraints
    # Each customer is visited exactly once
    for j in range(n):
        if j != depot:
            model.addConstr(quicksum(x[i, j, k] for i in range(n) for k in range(num_vehicle) if i != j) == 1)

    # Flow conservation
    for k in range(num_vehicle):
        for j in range(n):
            model.addConstr(quicksum(x[i, j, k] for i in range(n) if i != j) ==
                            quicksum(x[j, i, k] for i in range(n) if i != j))

    # Subtour elimination
    for i in range(n):
        for j in range(n):
            if i != j and (i != depot and j != depot):
                for k in range(num_vehicle):
                    model.addConstr(u[i, k] - u[j, k] + vehicle_capacity[k] * x[i, j, k] <= vehicle_capacity[k] - demands[j])

    # Capacity constraints
    for k in range(num_vehicle):
        model.addConstr(quicksum(demands[i] * x[i, j, k] for i in range(n) for j in range(n) if i != j) <= vehicle_capacity[k])

    # Vehicle starts and ends at depot
    for k in range(num_vehicle):
        model.addConstr(quicksum(x[depot, j, k] for j in range(n) if j != depot) == 1)
        model.addConstr(quicksum(x[i, depot, k] for i in range(n) if i != depot) == 1)

    # Optimize the model
    model.optimize()

    # Get the objective value
    obj = model.objVal if model.status == GRB.OPTIMAL else -1

    return obj