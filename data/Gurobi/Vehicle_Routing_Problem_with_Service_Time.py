# Vehicle Routing Problem with Service Time (VRPS)

from gurobipy import Model, GRB, quicksum

def solve(time_matrix: list, num_vehicle: int, depot: int, service_time: list):
    """
    Args:
        time_matrix: contains the integer travel times between locations
        num_vehicle: the number of the vehicle
        depot: the index of the depot node
        service_time: service time for each customer node

    Returns:
        obj: a number representing the objective value of the solution
    """
    # Create a new model
    model = Model("VRPS")

    # Get the number of nodes
    n = len(time_matrix)

    # Create variables
    x = model.addVars(n, n, num_vehicle, vtype=GRB.BINARY, name="x")  # Binary: if vehicle k travels from i to j
    y = model.addVars(n, num_vehicle, vtype=GRB.BINARY, name="y")     # Binary: if vehicle k serves customer i
    u = model.addVars(n, num_vehicle, vtype=GRB.CONTINUOUS, name="u") # Continuous: for MTZ subtour elimination

    # Set objective: minimize total travel time + service time
    obj = quicksum(time_matrix[i][j] * x[i, j, k] for i in range(n) for j in range(n) for k in range(num_vehicle))
    obj += quicksum(service_time[i] * y[i, k] for i in range(n) for k in range(num_vehicle))
    model.setObjective(obj, GRB.MINIMIZE)

    # Add constraints

    # Each customer (except depot) is visited exactly once by one vehicle
    for i in range(n):
        if i != depot:
            model.addConstr(quicksum(y[i, k] for k in range(num_vehicle)) == 1)

    # Flow conservation: if a vehicle arrives at a node, it must leave
    for k in range(num_vehicle):
        for i in range(n):
            model.addConstr(quicksum(x[i, j, k] for j in range(n) if j != i) == quicksum(x[j, i, k] for j in range(n) if j != i))
            model.addConstr(quicksum(x[i, j, k] for j in range(n) if j != i) == y[i, k])

    # Each vehicle starts and ends at the depot
    for k in range(num_vehicle):
        model.addConstr(quicksum(x[depot, j, k] for j in range(n) if j != depot) == 1)
        model.addConstr(quicksum(x[i, depot, k] for i in range(n) if i != depot) == 1)

    # Vehicle capacity: each vehicle serves at most n - 1 customers
    for k in range(num_vehicle):
        model.addConstr(quicksum(y[i, k] for i in range(n) if i != depot) <= n - 1)

    # Subtour elimination (MTZ formulation)
    for i in range(n):
        for j in range(n):
            if i != j and i != depot and j != depot:
                for k in range(num_vehicle):
                    model.addConstr(u[i, k] - u[j, k] + n * x[i, j, k] <= n - 1)

    # Set bounds for u (MTZ variables)
    for i in range(n):
        for k in range(num_vehicle):
            if i != depot:
                model.addConstr(u[i, k] >= 1)
                model.addConstr(u[i, k] <= n - 1)

    # Optimize model
    model.optimize()

    # Get the objective value
    if model.status == GRB.OPTIMAL:
        obj = model.objVal
    elif model.status == GRB.TIME_LIMIT:
        obj = model.objVal  # Return the best solution found within the time limit
    else:
        obj = -1

    return obj
