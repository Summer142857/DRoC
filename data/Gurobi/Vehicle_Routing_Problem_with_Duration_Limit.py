# Vehicle Routing Problem with Duration Limit (VRPL)

from gurobipy import *

def solve(time_matrix: list, num_vehicle: int, depot: int, duration_limit: int):
    """
    Args:
        time_matrix: contains the integer travel times between locations
        num_vehicle: the number of the vehicle
        depot: the index of the depot node
        duration_limit: the time duration of each route is upper bounded by the duration limit

    Returns:
        obj: a number representing the objective value of the solution
    """
    num_nodes = len(time_matrix)
    # Create a new model
    m = Model("VRPL")

    # Decision variables
    x = {}  # Binary variables for routes between nodes
    for v in range(num_vehicle):
        for i in range(num_nodes):
            for j in range(num_nodes):
                if i != j:
                    x[v, i, j] = m.addVar(vtype=GRB.BINARY, name=f"x_{v}_{i}_{j}")

    # Variables to track the duration of each vehicle's route
    duration = {v: m.addVar(vtype=GRB.CONTINUOUS, name=f"duration_{v}") for v in range(num_vehicle)}

    # Ensure each node is visited exactly once (by any vehicle)
    for i in range(num_nodes):
        if i != depot:
            m.addConstr(quicksum(x[v, i, j] for v in range(num_vehicle) for j in range(num_nodes) if i != j) == 1,
                        f"Visit_{i}")

    # Flow conservation constraints for each vehicle
    for v in range(num_vehicle):
        m.addConstr(quicksum(x[v, depot, j] for j in range(num_nodes) if j != depot) == 1, f"StartFromDepot_{v}")
        m.addConstr(quicksum(x[v, i, depot] for i in range(num_nodes) if i != depot) == 1, f"ReturnToDepot_{v}")

        # Flow conservation within the route
        for i in range(num_nodes):
            if i != depot:
                m.addConstr(quicksum(x[v, i, j] for j in range(num_nodes) if i != j) ==
                            quicksum(x[v, j, i] for j in range(num_nodes) if i != j), f"FlowConserve_{v}_{i}")

        # Duration constraint for each vehicle
        m.addConstr(duration[v] == quicksum(time_matrix[i][j] * x[v, i, j] for i in range(num_nodes)
                                            for j in range(num_nodes) if i != j), f"DurationCalc_{v}")
        m.addConstr(duration[v] <= duration_limit, f"DurationLimit_{v}")

    # Objective function: minimize the total travel time of all vehicles
    m.setObjective(quicksum(time_matrix[i][j] * x[v, i, j] for v in range(num_vehicle)
                            for i in range(num_nodes) for j in range(num_nodes) if i != j), GRB.MINIMIZE)

    # Optimize the model
    m.optimize()

    # Return the objective value of the optimized solution
    obj = m.objVal if m.status == GRB.OPTIMAL else -1

    return obj