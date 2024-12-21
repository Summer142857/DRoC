#!/usr/bin/env python3
# Copyright 2010-2024 Google LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Simple travelling salesman problem between cities."""

from ortools.sat.python import cp_model

DISTANCE_MATRIX = ...


def main():
    """Entry point of the program."""
    num_nodes = len(DISTANCE_MATRIX)
    all_nodes = range(num_nodes)
    print("Num nodes =", num_nodes)

    # Model.
    model = cp_model.CpModel()

    obj_vars = []
    obj_coeffs = []

    # Create the circuit constraint.
    arcs = []
    arc_literals = {}
    for i in all_nodes:
        for j in all_nodes:
            if i == j:
                continue

            lit = model.new_bool_var("%i follows %i" % (j, i))
            arcs.append((i, j, lit))
            arc_literals[i, j] = lit

            obj_vars.append(lit)
            obj_coeffs.append(DISTANCE_MATRIX[i][j])

    model.add_circuit(arcs)

    # Minimize weighted sum of arcs. Because this s
    model.minimize(sum(obj_vars[i] * obj_coeffs[i] for i in range(len(obj_vars))))

    # Solve and print out the solution.
    solver = cp_model.CpSolver()
    solver.parameters.log_search_progress = True
    # To benefit from the linearization of the circuit constraint.
    solver.parameters.linearization_level = 2

    solver.solve(model)
    print(solver.response_stats())

    current_node = 0
    str_route = "%i" % current_node
    route_is_finished = False
    route_distance = 0
    while not route_is_finished:
        for i in all_nodes:
            if i == current_node:
                continue
            if solver.boolean_value(arc_literals[current_node, i]):
                str_route += " -> %i" % i
                route_distance += DISTANCE_MATRIX[current_node][i]
                current_node = i
                if current_node == 0:
                    route_is_finished = True
                break

    print("Route:", str_route)
    print("Travelled distance:", route_distance)


if __name__ == "__main__":
    main()
