# Vehicle Routing Problem with Time Windows (VRPTW)
from gurobipy import Model, GRB, quicksum

def solve(time_matrix: list, time_windows: list, num_vehicle: int, depot: int):
    """
    Args:
        time_matrix: contains the integer travel times between locations
        time_windows: the list of tuples for time windows of the customers
        num_vehicle: the number of the vehicle
        depot: the index of the depot node

    Returns:
        obj: a number representing the objective value of the solution
    """

    # Set virtual destination depot by adding a row and a column to the time matrix
    time_matrix = time_matrix + [time_matrix[depot]]
    for i in range(len(time_matrix)):
        time_matrix[i].append(time_matrix[depot][i])
    # Update the time windows with the virtual destination depot
    time_windows = time_windows + [(0, 1000)]

    num_locations = len(time_matrix)
    model = Model("VRPTW")

    # Variables
    x = model.addVars(num_locations, num_locations, num_vehicle, vtype=GRB.BINARY, name="x")
    t = model.addVars(num_locations, num_vehicle, vtype=GRB.CONTINUOUS, name="t")

    # Objective: Minimize total travel time
    model.setObjective(quicksum(time_matrix[i][j] * x[i, j, k]
                                for i in range(num_locations)
                                for j in range(num_locations)
                                for k in range(num_vehicle)), GRB.MINIMIZE)

    # Constraints

    # Each customer is visited exactly once by one vehicle
    for j in range(num_locations):
        if j not in [depot, num_locations-1]:
            model.addConstr(quicksum(x[i, j, k] for i in range(num_locations)
                                      for k in range(num_vehicle) if i != j) == 1)

    # Each vehicle leaves the origin depot
    for k in range(num_vehicle):
        model.addConstr(quicksum(x[depot, j, k] for j in range(num_locations) if j != depot) == 1)

    # Each vehicle returns to the virtual destination depot
    for k in range(num_vehicle):
        model.addConstr(quicksum(x[i, num_locations-1, k] for i in range(num_locations) if i != depot) == 1)

    # Flow conservation: each visit is followed by a departure
    for k in range(num_vehicle):
        for j in range(num_locations):
            if j not in [depot, num_locations-1]:
                model.addConstr(quicksum(x[i, j, k] for i in range(num_locations) if i != j) ==
                                quicksum(x[j, l, k] for l in range(num_locations) if l != j))

    # Time window constraints
    for k in range(num_vehicle):
        for i in range(num_locations):
            for j in range(num_locations):
                if i != j:
                    model.addConstr(t[i, k] + time_matrix[i][j] - (1 - x[i, j, k]) *
                                    (max(tw[1] for tw in time_windows) + max(time_matrix[i])) <= t[j, k])


    # Time windows for each location
    for i in range(num_locations):
        for k in range(num_vehicle):
            model.addConstr(t[i, k] >= time_windows[i][0])
            model.addConstr(t[i, k] <= time_windows[i][1])

    # Optimize the model
    model.optimize()

    # Return the objective value if a solution is found
    obj = model.objVal if model.status == GRB.OPTIMAL else -1
    return obj
