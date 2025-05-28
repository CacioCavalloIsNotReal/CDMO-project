from .mip_model import solve_mcp_mip
from .mip_utils import parse_instance, write_output, combine_results, run_z3_with_external_timeout
import os
import numpy as np

INSTANCES_DIR = os.path.abspath('instances')

def choose_solver(solver_name):
    match solver_name:
        case "gurobi":
            return "GUROBI_CMD"
        case "cbc":
            return "PULP_CBC_CMD"
        case "highs":
            return "HiGHS_CMD"
        case _:
            print("Invalid solver name. Please choose from Gurobi, CBC, or HiGHS.")

def choose_instance(instance_name):
    if int(instance_name) in range(1, 10): # Changed from range(1, 9) to range(1, 10) to include 9
        instance = f"inst0{instance_name}.dat"
    elif int(instance_name) in range(10, 22):
        instance = f"inst{instance_name}.dat"
    return instance

def prepare_solution(input):
    try:
        if not input['solution_found']:
            output = {
                'time' : 300,
                'optimal' : False,
                'obj' : 0,
                'sol': []
                }    
        else:
            output = input

    except:
        output = input

    return output

def execute_mip(instance_name: str, solver_name: str = 'highs', symbreak: bool = False):
    
    if instance_name == "all":
        print("Running on all instances...")
        for i in range(len(os.listdir(INSTANCES_DIR))):
            execute_mip(
                solver_name=solver_name, 
                symbreak=symbreak, 
                instance_name=str(i + 1)
                )

    else:
        print(f"Running on instance {instance_name}...")
        solver = choose_solver(solver_name.lower())
        instance = choose_instance(instance_name)
        params = parse_instance(INSTANCES_DIR + "/" + instance)

        os.makedirs("./MIP/result_symbreak", exist_ok=True)
        os.makedirs("./MIP/result_nosymbreak", exist_ok=True)
        
        if symbreak:
            results_dir = os.path.join("./MIP/result_symbreak", solver_name)
        else:
            results_dir = os.path.join("./MIP/result_nosymbreak", solver_name)

        solution = run_z3_with_external_timeout(
            external_timeout_seconds=300,
            model_func=solve_mcp_mip,
            params=params,
            solver=solver,
            time_limit_sec=300,
            add_symmetry_break=symbreak
        )

        print(solution)

        output_path = os.path.join(results_dir, f"{'.'.join(instance.split('.')[:-1])}.json")
        write_output(prepare_solution(solution), output_path, solver_name)
    
    combine_results(
        result_nosymbreak_dir="./MIP/result_nosymbreak",
        result_symbreak_dir="./MIP/result_symbreak"
    )
