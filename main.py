import argparse
import os
from typing import Tuple, List, Dict
from common import get_dataset
from DRoC import System
from utils import context_all
from standard import run


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='DRoC Vehicle Routing Problem Solver')

    # Model configuration
    parser.add_argument('--method', type=str, default='DRoC',
                        help='The method to use for solving the problem')
    parser.add_argument('--solver', type=str, default='OR-tools', choices=['OR-tools', 'Gurobi'],
                        help='Solver to use (OR-tools or Gurobi)')
    parser.add_argument('--llm', type=str, default='claude-3-5-sonnet-20241022',
                        help='LLM model to use for code generation')

    # Dataset configuration
    parser.add_argument('--start_idx', type=int, default=0,
                        help='Starting index in the dataset')
    parser.add_argument('--end_idx', type=int, default=None,
                        help='Ending index in the dataset')
    parser.add_argument('--skip_existing', action='store_true',
                        help='Skip problems that already have generated solutions')

    # System configuration
    parser.add_argument('--output_dir', type=str, default='generated_codes',
                        help='Directory to save generated code')
    parser.add_argument('--max_iterations', type=int, default=4,
                        help='Maximum number of refinement iterations')

    args = parser.parse_args()
    return args


def setup_environment(args: argparse.Namespace) -> None:
    """Setup environment variables and directories."""
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    # You can add your API key setup here if needed
    os.environ["ANTHROPIC_API_KEY"] = "your-key-here"

    # os.environ["OPENAI_API_KEY"] = "your-key-here"


def get_problem_indices(args: argparse.Namespace, total_problems: int) -> Tuple[int, int]:
    """Get the start and end indices for problem processing."""
    start_idx = args.start_idx
    end_idx = args.end_idx if args.end_idx is not None else total_problems

    if start_idx < 0 or start_idx >= total_problems:
        raise ValueError(f"Start index {start_idx} is out of range")
    if end_idx <= start_idx or end_idx > total_problems:
        raise ValueError(f"End index {end_idx} is invalid")

    return start_idx, end_idx


def run_evaluation(args: argparse.Namespace,
                   names: List[str],
                   params: List[Dict],
                   inputs: List[Dict],
                   optimums: List[float],
                   method: str) -> Tuple[List[str], List[str], List[str]]:
    """Run the evaluation process for the specified problems."""
    successful_tasks = []
    runtime_error_tasks = []
    error_tasks = []

    existing_solutions = []
    if args.skip_existing:
        existing_solutions = [f.split('.')[0] for f in os.listdir(args.output_dir)]

    start_idx, end_idx = get_problem_indices(args, len(names))

    for i in range(start_idx, end_idx):
        problem_name = names[i]

        if args.skip_existing and problem_name in existing_solutions:
            print(f"Skipping {problem_name} - solution already exists")
            continue

        print(f"-----Testing task: {problem_name}-----")

        # Prepare input
        current_input = inputs[i].copy()
        current_input['solver'] = args.solver
        current_input['optimum'] = optimums[i]

        try:
            if method == 'DRoC':
                system = System(current_input, params[i], args.llm)
                system.max_iteration = args.max_iterations
                no_runtime_error, accurate = system.run()
            elif method == 'standard':
                no_runtime_error, accurate = run(params[i], current_input, optimums[i], args.llm,
                                                 max_iterations=args.max_iterations, self_debug=False)
            elif method == 'self_debug':
                no_runtime_error, accurate = run(params[i], current_input, optimums[i], args.llm,
                                                 max_iterations=args.max_iterations, self_debug=True)
            else:
                raise ValueError(f"Invalid method: {method}")

            if not no_runtime_error:
                runtime_error_tasks.append(problem_name)
            if accurate:
                successful_tasks.append(problem_name)
        except Exception as e:
            print(f"Error in task {problem_name}: {str(e)}")
            runtime_error_tasks.append(problem_name)
            error_tasks.append(problem_name)

    return successful_tasks, runtime_error_tasks, error_tasks


def main():
    # Parse arguments
    args = parse_args()

    # Setup environment
    setup_environment(args)

    # Load dataset
    names, params, inputs, optimums = get_dataset()

    # Run evaluation
    successful_tasks, runtime_error_tasks, error_tasks = run_evaluation(
        args, names, params, inputs, optimums, args.method
    )

    # Print results
    total_problems = len(names)
    print("\nEvaluation Results:")
    print(f"Total problems tested: {total_problems}")
    print(f"Successful solutions: {len(successful_tasks)} ({len(successful_tasks) / total_problems * 100:.2f}%)")
    print(f"Runtime errors: {len(runtime_error_tasks)} ({len(runtime_error_tasks) / total_problems * 100:.2f}%)")

    # Print lists of problem names if needed
    if successful_tasks:
        print("\nSuccessful tasks:", successful_tasks)
    if runtime_error_tasks:
        print("\nTasks with runtime errors:", runtime_error_tasks)


if __name__ == "__main__":
    main()
