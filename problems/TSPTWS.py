problem = [
            [0, 6, 6, 8, 7],
            [6, 0, 8, 3, 2],
            [6, 8, 0, 5, 10],
            [8, 3, 5, 0, 1],
            [7, 2, 10, 1, 0]
          ]

time_windows = [
                (0, 3),  # depot
                (3, 10),  # 1
                (10, 20),  # 2
                (18, 25),  # 3
                (10, 30),  # 4
              ]
depot = 0
service_time = [0, 2, 3, 5, 2]

params_dict = {'time_matrix': problem, 'time_windows': time_windows, 'depot': 0, 'service_time': service_time}
input = {"problem": "Travelling Salesman Problem with Time Windows and Service Time (TSPTWS)",
         "code_example": '''def solve(time_matrix: list, time_windows: list, depot: int, service_time: list):\n    """\n    Args:\n        time_matrix: contains the integer travel times between locations\n        time_windows: the list of tuples for time windows of the customers\n       depot: the index of the depot node\n           service_time: service time for each customer node\n\n    Returns:\n        obj: a number representing the objective value of the solution\n    """\n    obj = -1\n    return obj\n''',
         'solver': 'OR-tools'}

optimal = 39