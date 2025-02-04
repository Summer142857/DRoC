# DRoC: Vehicle Routing Problem Solver with Large Language Model

Official implementation for paper "Elevating Large Language Models for Complex Vehicle Routing via Decomposed Retrieval of Constraints (ICLR2025)"

This repository contains an implementation of a Vehicle Routing Problem solver that leverages Large Language Models (LLMs) to generate and refine solution code. The system supports multiple solving methods and can work with different optimization solvers.

## Features

- Support for multiple solvers:
  - Google OR-Tools
  - Gurobi
- Flexible LLM integration (currently supports):
  - Claude models (default: claude-3-5-sonnet-20241022)
  - GPT models
- Automated code generation and refinement
- Retrieval-augmented generation (RAG)+Self-debug

## Requirements

- Python 3.7+
- OR-Tools or Gurobi solver
- Required Python packages:
  - langchain
  - anthropic
  - openai (for GPT models)

## Project Structure

```
project_directory/
├── main.py          # Main execution file with argument parsing
├── chroma_db        # Vector store for RAG
├── data             # Local data source for retrieval
├── gene_codes       # The generated codes by DRoC
├── problems         # The VRP benchmark for problem solving
├── DRoC.py          # Implementation of DRoC method
├── standard.py      # Standard solving method implementation
├── utils.py         # Utility functions
└── common.py        # Common functions and data structures
```

## Installation

1. Clone the repository:
   
   ```bash
   git clone [repository-url]
   cd [repository-name]
   ```

2. Install required packages:
   
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your API keys in environment variables or in the code:
   
   ```python
   os.environ["ANTHROPIC_API_KEY"] = "your-key-here"
   os.environ["OPENAI_API_KEY"] = "your-key-here"  # if using GPT models
   ```

## Usage

Run the solver using the command line interface with various configuration options:

```bash
python main.py --method DRoC --solver OR-tools --llm claude-3-5-sonnet-20241022
```

### Command Line Arguments

- `--method`: Solving method to use (DRoC, standard, or self_debug)
- `--solver`: Optimization solver to use (OR-tools or Gurobi)
- `--llm`: LLM model to use for code generation
- `--start_idx`: Starting index in the dataset
- `--end_idx`: Ending index in the dataset
- `--skip_existing`: Skip problems that already have generated solutions
- `--output_dir`: Directory to save generated code
- `--max_iterations`: Maximum number of refinement iterations

### Example Commands

1. Run with default settings:
   
   ```bash
   python main.py
   ```

2. Use specific solver and LLM:
   
   ```bash
   python main.py --solver Gurobi --llm claude-3-5-sonnet-20241022
   ```

3. Process specific range of problems:
   
   ```bash
   python main.py --start_idx 5 --end_idx 10 --skip_existing
   ```

4. Custom output directory and iterations:
   
   ```bash
   python main.py --output_dir custom_output --max_iterations 6
   ```

## Evaluation Results

The system provides comprehensive evaluation results including:

- Total problems tested
- Success rate
- Runtime error rate
- Lists of successful and failed tasks

Example output:

```
Evaluation Results:
Total problems tested: 48
Successful solutions: 23 (47.92%)
Runtime errors: 10 (20.83%)

Successful tasks: ['CVRP', 'VRPTW', ...]
Tasks with runtime errors: ['VRPMD', 'PCTSP', ...]
```

## Contributing

Contributions are welcome! Please feel free to submit pull requests or create issues for bugs and feature requests.

## License

MIT

## Citation

If you use this code in your research, please cite:

```bibtex
@inproceedings{
droc2025,
title={{DR}oC: Elevating Large Language Models for Complex Vehicle Routing via Decomposed Retrieval of Constraints},
author={Xia Jiang, Yaoxin Wu, Chenhao Zhang, Yingqian_Zhang},
booktitle={The Thirteenth International Conference on Learning Representations},
year={2025},
url={https://openreview.net/forum?id=s9zoyICZ4k}
}
```

## Acknowledgments

- Thanks to the developers of OR-Tools and Gurobi
- Thanks to Anthropic and OpenAI for their LLM APIs
