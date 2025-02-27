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