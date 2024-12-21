# Travelling Salesman Problem Solver using Gurobi

import gurobipy as gp
from gurobipy import GRB

def solve(distance_matrix: list, depot: int):
    """
    Solves the Travelling Salesman Problem using Gurobi optimizer.

    Args:
        distance_matrix: contains the integer distance between customers
        depot: the index of the start node

    Returns:
        obj: a number representing the objective value of the solution
    """
    # Get the number of nodes
    n = len(distance_matrix)
    
    # Create a new Gurobi model
    model = gp.Model("TSP")

    # Create decision variables
    # vars[i,j] = 1 if the path goes from city i to j, 0 otherwise
    vars = model.addVars(n, n, vtype=GRB.BINARY, name="x")
    # u[i] represents the order of city i in the path
    u = model.addVars(n, vtype=GRB.INTEGER, name="u")

    # Set objective: minimize total distance
    obj = model.addVar(name="objective")
    model.setObjective(obj, GRB.MINIMIZE)

    # Add constraints
    # The objective equals the sum of distances of chosen paths
    model.addConstr(gp.quicksum(vars[i, j] * distance_matrix[i][j] for i in range(n) for j in range(n) if i != j) == obj)

    # Each city is visited exactly once
    for i in range(n):
        model.addConstr(gp.quicksum(vars[i, j] for j in range(n) if i != j) == 1)  # Outgoing
        model.addConstr(gp.quicksum(vars[j, i] for j in range(n) if i != j) == 1)  # Incoming

    # Subtour elimination constraints (Miller-Tucker-Zemlin formulation)
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                model.addConstr(u[i] - u[j] + n * vars[i, j] <= n - 1)

    # Set depot as the starting point
    model.addConstr(u[depot] == 0)

    # Optimize the model
    model.optimize()

    # Get the objective value (total distance of the optimal tour)
    obj = model.objVal

    return obj