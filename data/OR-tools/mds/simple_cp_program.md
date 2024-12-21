# simple_cp_program

First, you must install [ortools](https://pypi.org/project/ortools/) package in this colab.

```
%pip install ortools
```

Simple Constraint optimization example.

```
from ortools.constraint_solver import pywrapcp


def main():
    """Entry point of the program."""
    # Instantiate the solver.
    solver = pywrapcp.Solver("CPSimple")

    # Create the variables.
    num_vals = 3
    x = solver.IntVar(0, num_vals - 1, "x")
    y = solver.IntVar(0, num_vals - 1, "y")
    z = solver.IntVar(0, num_vals - 1, "z")

    # Constraint 0: x != y.
    solver.Add(x != y)
    print("Number of constraints: ", solver.Constraints())

    # Solve the problem.
    decision_builder = solver.Phase(
        [x, y, z], solver.CHOOSE_FIRST_UNBOUND, solver.ASSIGN_MIN_VALUE
    )

    # Print solution on console.
    count = 0
    solver.NewSearch(decision_builder)
    while solver.NextSolution():
        count += 1
        solution = f"Solution {count}:\n"
        for var in [x, y, z]:
            solution += f" {var.Name()} = {var.Value()}"
        print(solution)
    solver.EndSearch()
    print(f"Number of solutions found: {count}")

    print("Advanced usage:")
    print(f"Problem solved in {solver.WallTime()}ms")
    print(f"Memory usage: {pywrapcp.Solver.MemoryUsage()}bytes")


main()
```
