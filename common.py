from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, TypedDict
import traceback
import os, glob, sys, importlib
import subprocess
import tempfile
import json
import re
import ast

class UnusedParameterError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f'UnusedParameterError: {self.message}'

class ParameterUsageVisitor(ast.NodeVisitor):
    def __init__(self, parameters):
        self.parameters = set(parameters)
        self.used_params = set()

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load) and node.id in self.parameters:
            self.used_params.add(node.id)
        self.generic_visit(node)

    def visit_Lambda(self, node):
        # Process the lambda body
        self.generic_visit(node.body)


def check_unused_parameters(code):
    # Parse the source code into an AST
    tree = ast.parse(code)
    func_defs = [node for node in tree.body if isinstance(node, ast.FunctionDef)]

    for func_def in func_defs:
        params = {arg.arg for arg in func_def.args.args}

        # Visit the AST to find used parameters
        visitor = ParameterUsageVisitor(params)
        visitor.visit(func_def)

        unused_params = params - visitor.used_params

        if unused_params:
            raise UnusedParameterError(f"Params {unused_params} are not used,"
                                       f" you should ensure all the params are used in the function.")



def remove_line_with_routing_solve(lines):
    # Split the multiline string into lines
    lines = lines.splitlines()

    # Use list comprehension to filter out lines containing "routing.SolveWithParameters"
    filtered_lines = [line for line in lines if "routing.SolveWithParameters" not in line]

    # Join the filtered lines back into a single string
    result = "\n".join(filtered_lines)

    return result


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# Data model
class code(BaseModel):
    """Code output"""
    prefix: str = Field(description="Description of the problem and approach")
    imports: str = Field(description="Code block import statements")
    code: str = Field(description="Code block not including import statements")
    description = "The code to solve an optimization problem."

class code_debug(BaseModel):
    """Code output"""
    prefix: str = Field(description="Reason of the error and the strategy for fixing it")
    imports: str = Field(description="Code block import statements")
    code: str = Field(description="Code block not including import statements")
    description = "The refined code to solve an optimization problem."


class commented_code(BaseModel):
    """Code output"""
    code: str = Field(description="Code block with comments")


class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        error : Binary flag for control flow to indicate whether test error was tripped
        messages : With user question, error messages, reasoning
        generation : Code solution
        iterations : Number of tries
    """

    error: str
    messages: List
    generation: str
    iterations: int

def write_and_run(code_string, params):
    param_names = params.keys()
    param_assignments = "\n".join([f"    {name} = params['{name}']" for name in param_names])
    param_list = ", ".join(param_names)
    main_code = f"""
if __name__ == "__main__":
    # Read parameters from the JSON file
    import sys
    import json
    import traceback
    with open(sys.argv[1], 'r') as f:
        params = json.load(f)

{param_assignments}
    try:
        result = solve({param_list})
        print('Code executed successfully, and the obj = '+ str(result))
    except Exception as e:
        print('Error:', e)
        print('Traceback:', traceback.format_exc())
    """
    code_string = code_string + main_code
    with tempfile.NamedTemporaryFile(delete=False, suffix='.py', mode='w') as temp_script:
        temp_script.write(code_string)
        temp_script_path = temp_script.name

    # Create a temporary file to hold the JSON parameters
    with tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w') as temp_params:
        json.dump(params, temp_params)
        temp_params_path = temp_params.name

    try:
        # Run the temporary script as a subprocess
        result = subprocess.run(['python', temp_script_path, temp_params_path], capture_output=True, text=True,
                                check=True, timeout=60)
        if 'Code executed successfully' in result.stdout:
            pattern = r'obj = \s*([\d.]+)'
            match = re.search(pattern, result.stdout)
            if match is not None:
                return match.group(1)
            else:
                return -1
        else:
            return result.stdout
    except subprocess.TimeoutExpired as e:
        print(f"Subprocess timed out after {e.timeout} seconds")
        return e
    except subprocess.CalledProcessError as e:
        print(f"Subprocess failed with exit code {e.returncode}")
        return e
    finally:
        # Optionally, delete the temporary script and parameters file if you don't need them anymore
        os.remove(temp_script_path)
        os.remove(temp_params_path)


def code_check(state: GraphState, param_dict: dict, optimal:float):
    """
    Check code

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, error
    """

    print("---CHECKING CODE---")

    # State
    messages = state["messages"]
    code_solution = state["generation"]
    iterations = state["iterations"]

    # Get solution components
    imports = code_solution.imports
    code = code_solution.code

    # Check imports
    try:
        exec(imports)
    except Exception as e:
        print("---CODE IMPORT CHECK: FAILED---")
        error_message = [("user", f"Your solution failed the import test: {e}")]
        messages += error_message
        return {
            "generation": code_solution,
            "messages": messages,
            "iterations": iterations,
            "error": "yes",
        }

    # Check all params are used
    try:
        globals_dict = param_dict.copy()
        # avoid running code in exec, otherwise the code may stuck
        revised_code = remove_line_with_routing_solve(code)
        params_str = ', '.join(f"{key}={repr(value)}" for key, value in globals_dict.items())
        revised_code = revised_code + f"\nsolve({params_str})"
        check_unused_parameters(revised_code)
        # exec(imports + "\n" + check_usage_string + "\n" + revised_code, globals_dict)
        # sol = globals_dict['solve'](**param_dict)
    except Exception as e:
        if "UnusedParameterError" in str(e):
            print("---CODE IMPORT CHECK: FAILED---")
            error_message = [("user", f"{e}")]
            messages += error_message
            return {
                "generation": code_solution,
                "messages": messages,
                "iterations": iterations,
                "error": "yes",
            }
        else:
            pass
    # Check execution
    try:
        sol = write_and_run(imports + "\n" + code, param_dict)
        if type(sol) != float:
            if type(sol) == str:
                if 'Error' in sol:
                    error_message = [("user", f"The solution failed the code execution test: {sol}" )]
                    print("---CODE BLOCK CHECK: FAILED---")
                    messages += error_message
                    return {
                        "generation": code_solution,
                        "messages": messages,
                        "iterations": iterations,
                        "error": "yes",
                    }
            else:
                error_message = [("user", f"The generated code cannot run or time out." )]
                print("---CODE BLOCK CHECK: FAILED---")
                messages += error_message
                return {
                    "generation": code_solution,
                    "messages": messages,
                    "iterations": iterations,
                    "error": "yes",
                }
    except Exception as e:
        print("---CODE BLOCK CHECK: FAILED---")
        error_message = [("user", f"The solution failed the code execution test: {e}, and the stack trace is {traceback.format_exc()}" )]
        messages += error_message
        return {
            "generation": code_solution,
            "messages": messages,
            "iterations": iterations,
            "error": "yes",
        }
    if sol is None or float(sol) == 0.:
        print("---CODE BLOCK CHECK: NOTHING RETURN---")
        error_message = [("user", f"You solution returns nothing or 0. The program may be incomplete or your solution does not work for the task." )]
        messages += error_message
        return {
            "generation": code_solution,
            "messages": messages,
            "iterations": iterations,
            "error": "yes",
        }
    if sol == -1:
        print("---CODE BLOCK CHECK: NOT FINISHED---")
        error_message = [("user", f"You did not finish the function for solving the task." )]
        messages += error_message
        return {
            "generation": code_solution,
            "messages": messages,
            "iterations": iterations,
            "error": "yes",
        }
    if abs(((optimal-float(sol)) / float(sol))) > 0.05:
        print("---CODE BLOCK CHECK: NOT ACCURATE---")
        print(f"optimal: {optimal}, calculated sol: {sol}")
        error_message = [("user", f"The obj. is far from the optimum, and you may not have considered all the constraints." )]
        messages += error_message
        return {
            "generation": code_solution,
            "messages": messages,
            "iterations": iterations,
            "error": "yes",
        }

    # No errors
    print("---NO CODE TEST FAILURES---")
    return {
        "generation": code_solution,
        "messages": messages,
        "iterations": iterations,
        "error": "no",
        "solution": sol
    }

def get_dataset(dir='./problems'):
    files = glob.glob(os.path.join(dir, '*.py'))
    names = []
    param_lists = []
    inputs = []
    optimums = []
    for file_path in files:
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, 'input'):
            inputs.append(module.input)
            names.append(module.input['problem'])
        else:
            print(f"Warning: Module '{module_name}' does not have an 'input' variable.")

        if hasattr(module, 'params_dict'):
            param_lists.append(module.params_dict)
        else:
            print(f"Warning: Module '{module_name}' does not have an 'params_dict' variable.")

        if hasattr(module, 'optimal'):
            optimums.append(module.optimal)
        else:
            print(f"Warning: Module '{module_name}' does not have an 'optimal' variable.")

    return names, param_lists, inputs, optimums

if __name__ == "__main__":
    # name, params, inputs = get_dataset()
    code_string = "from ortools.constraint_solver import pywrapcp, routing_enums_pb2\ndef solve(distance_matrix: list, depot: int):\n    def create_data_model():\n        data = {}\n        locations = [(i, j) for i, row in enumerate(distance_matrix) for j, _ in enumerate(row)]\n        data['locations'] = locations\n        data['num_vehicles'] = 1\n        data['depot'] = depot\n        return data\n\n    def create_distance_callback(data, manager):\n        distances_ = {}\n        index_manager_ = manager\n        for from_counter, from_node in enumerate(data['locations']):\n            distances_[from_counter] = {}\n            for to_counter, to_node in enumerate(data['locations']):\n                if from_counter == to_counter:\n                    distances_[from_counter][to_counter] = 0\n                else:\n                    distances_[from_counter][to_counter] = abs(from_node[0] - to_node[0]) + abs(from_node[1] - to_node[1])\n        def distance_callback(from_index, to_index):\n            from_node = index_manager_.IndexToNode(from_index)\n            to_node = index_manager_.IndexToNode(to_index)\n            return distances_[from_node][to_node]\n        return distance_callback\n\n    def print_solution(manager, routing, assignment):\n        index = routing.Start(0)\n        route_distance = 0\n        while not routing.IsEnd(index):\n            previous_index = index\n            index = assignment.Value(routing.NextVar(index))\n            route_distance += routing.GetArcCostForVehicle(previous_index, index, 0)\n        return route_distance\n\n    data = create_data_model()\n    manager = pywrapcp.RoutingIndexManager(len(data['locations']), data['num_vehicles'], data['depot'])\n    routing = pywrapcp.RoutingModel(manager)\n    distance_callback = create_distance_callback(data, manager)\n    transit_callback_index = routing.RegisterTransitCallback(distance_callback)\n    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)\n    search_parameters = pywrapcp.DefaultRoutingSearchParameters()\n    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC\n    assignment = routing.SolveWithParameters(search_parameters)\n    if assignment1:\n        obj = print_solution(manager, routing, assignment)\n        return obj\n    return -1"
    problem = [
        [0, 2451, 713, 1018, 1631, 1374, 2408, 213, 2571, 875, 1420, 2145, 1972],
        [2451, 0, 1745, 1524, 831, 1240, 959, 2596, 403, 1589, 1374, 357, 579],
        [713, 1745, 0, 355, 920, 803, 1737, 851, 1858, 262, 940, 1453, 1260],
        [1018, 1524, 355, 0, 700, 862, 1395, 1123, 1584, 466, 1056, 1280, 987],
        [1631, 831, 920, 700, 0, 663, 1021, 1769, 949, 796, 879, 586, 371],
        [1374, 1240, 803, 862, 663, 0, 1681, 1551, 1765, 547, 225, 887, 999],
        [2408, 959, 1737, 1395, 1021, 1681, 0, 2493, 678, 1724, 1891, 1114, 701],
        [213, 2596, 851, 1123, 1769, 1551, 2493, 0, 2699, 1038, 1605, 2300, 2099],
        [2571, 403, 1858, 1584, 949, 1765, 678, 2699, 0, 1744, 1645, 653, 600],
        [875, 1589, 262, 466, 796, 547, 1724, 1038, 1744, 0, 679, 1272, 1162],
        [1420, 1374, 940, 1056, 879, 225, 1891, 1605, 1645, 679, 0, 1017, 1200],
        [2145, 357, 1453, 1280, 586, 887, 1114, 2300, 653, 1272, 1017, 0, 504],
        [1972, 579, 1260, 987, 371, 999, 701, 2099, 600, 1162, 1200, 504, 0],
    ]

    params_dict = {'distance_matrix': problem, 'depot': 0}
    write_and_run(code_string, params_dict)