# Multiple Couriers Planning Problem

**Authors:** Francesco Cavaleri (francesco.cavaleri@studio.unibo.it), Giacomo Piergentili (giacomo.piergentili2@studio.unibo.it)
**Date:** June 2025

## Project Description

This project implements and evaluates three different approaches to solve the Multiple Couriers Planning Problem (MCPP). The implemented approaches are:
1.  **Constraint Programming (CP)**
2.  **Satisfiability Modulo Theories (SMT)**
3.  **Mixed Integer Programming (MIP)**

The primary goal is to assign a set of items to a team of couriers and plan their individual delivery routes. The objective is to minimize the maximum travel distance covered by any single courier, while respecting constraints such as courier capacities and ensuring all items are delivered starting from and returning to a central depot.

A common preprocessing step is applied across all methods, which involves parsing the raw instance data and computing a lower bound for the objective function.

## Technologies Used

*   **Programming Languages:** Python 3, MiniZinc
*   **Optimization Approaches & Solvers:**
    *   **Constraint Programming (CP):**
        *   Model: MiniZinc
        *   Solvers: Gecode, Chuffed
    *   **Satisfiability Modulo Theories (SMT):**
        *   Solver: Z3
    *   **Mixed Integer Programming (MIP):**
        *   Modeling Library: PuLP
        *   Solvers: Gurobi, HiGHS, CBC
*   **Key Python Libraries:**
    *   `minizinc` (for CP interfacing)
    *   `z3-solver` (for SMT modeling)
    *   `pulp` (for MIP modeling)
    *   `gurobipy` (Gurobi Python bindings)
    *   `highspy` (HiGHS Python bindings)
    *   `numpy`
    *   `tqdm` (for progress bars)
    *   `networkx` (potentially for graph operations, listed in requirements)
*   **Containerization:** Docker
*   **Documentation:** LaTeX (for the project report `report.tex`)

## Project Structure

```
.
├── CP/                  # Constraint Programming: model (.mzn), scripts, DZN instances
├── MIP/                 # Mixed Integer Programming: model, scripts, results
├── SMT/                 # Satisfiability Modulo Theories: model, scripts, results
├── instances/           # Raw instance files in .dat format
├── res/                 # Consolidated JSON results for CP, MIP, SMT approaches
├── Dockerfile           # Docker configuration for building the execution environment
├── main.py              # Main script to run experiments for all approaches
├── requirements.txt     # Python dependencies
├── report.tex           # Detailed project report in LaTeX
├── gurobi.lic           # Gurobi license file (user-provided, required for Gurobi solver)
```

## Setup and Installation

### Prerequisites
1.  **Docker:** Ensure Docker is installed and running on your system.
2.  **Gurobi License (Optional but Recommended for MIP):**
    *   If you intend to use the Gurobi solver for MIP, obtain a valid Gurobi license.
    *   Place your license file named `gurobi.lic` in the root directory of this project. The `Dockerfile` is configured to copy this license into the Docker image.

### Building the Docker Image
Navigate to the project root directory in your terminal and run the following command to build the Docker image:
```bash
docker build -t cdmo-project .
```
This command creates a Docker image named `cdmo-project` with all necessary dependencies, solvers (MiniZinc, HiGHS, Gurobi Python bindings), and Python packages installed.

### Running the Docker Container
To start an interactive session within the Docker container, use:
```bash
docker run -it --rm -v "$(pwd):/home/cdmo" cdmo-project bash
```
*   `-it`: Runs the container in interactive mode with a terminal.
*   `--rm`: Automatically removes the container when it exits.
*   `-v "$(pwd):/home/cdmo"`: Mounts the current project directory on your host machine to `/home/cdmo` inside the container. This allows you to edit files on your host and run them inside the container, with results appearing directly in your project directory.

All subsequent commands for running experiments should be executed from within this Docker container's terminal, in the `/home/cdmo` directory.

## Running the Models

The primary script for executing experiments is `main.py`.

### `main.py` Usage
```bash
python main.py <approach> <solver> <symbreak> <instance>
```

**Arguments:**

*   `<approach>`: The modeling approach.
    *   `cp`: Constraint Programming
    *   `mip`: Mixed Integer Programming
    *   `smt`: Satisfiability Modulo Theories
*   `<solver>`: The solver to use.
    *   For `cp`: `gecode`, `chuffed`
    *   For `mip`: `gurobi`, `highs`
    *   For `smt`: `z3` (implicitly used by the SMT scripts)
*   `<symbreak>`: Enable or disable symmetry breaking constraints.
    *   `true`: Enable symmetry breaking.
    *   `false`: Disable symmetry breaking.
*   `<instance>`: The instance identifier.
    *   An integer (e.g., `1`, `10`) corresponding to instance files (e.g., `inst01.dat`, `inst10.dat`).
    *   `all`: Run the specified configuration on all available instances.

### Examples:

*   **Run CP model with Gecode, no symmetry breaking, on instance 1:**
    ```bash
    python main.py cp gecode false 1
    ```

*   **Run MIP model with Gurobi, with symmetry breaking, on all instances:**
    ```bash
    python main.py mip gurobi true all
    ```
    (The `execute_mip_script.sh` file provides further examples for batch-running MIP experiments.)

*   **Run SMT model (Z3 solver), no symmetry breaking, on instance 5:**
    ```bash
    python main.py smt z3 false 5
    ```

## Output

*   **JSON Results:** Solution details, objective values, and execution times are saved as JSON files.
    *   Consolidated results are stored in `res/<APPROACH>/` (e.g., `res/CP/inst01.json`).
    *   The MIP and SMT scripts also generate intermediate results in their respective subdirectories (`MIP/result_nosymbreak/`, `SMT/result_symbreak/`, etc.) before consolidation.
*   **DZN Files (for CP):** The CP approach converts `.dat` instance files into `.dzn` (MiniZinc data) files, which are stored in `CP/instances/`.
```
