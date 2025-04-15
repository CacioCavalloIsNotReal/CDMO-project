import model_symbreak as model
import mip_utils as utils
import os

INSTANCES_PATH = "/Users/giacomopiergentili/Developer/CDMO/project-final/CDMO-project/instances"


def choose_solver():
    solver_name = input("Please enter the solver you want to use: ").upper()
    match solver_name:
        case "GUROBI":
            return "GUROBI_CMD"
        case "CBC":
            return "PULP_CBC_CMD"
        case "HIGHS":
            return "HiGHS_CMD"
        case _:
            print("Invalid solver name. Please choose from Gurobi, CBC, or HiGHS.")
            return choose_solver()

def choose_symbreak():
    symbreak_choice = input("Do you want to use symmetry breaking? (yes/no): ").strip().lower()
    if symbreak_choice == "yes":
        return True
    elif symbreak_choice == "no":
        return False
    else:
        print("Invalid choice. Please choose 'yes' or 'no'.")
        return choose_symbreak()

def choose_instances_num():
    run_choice = input("Do you want to run on a single instance or all instances? (single/all): ").strip().lower()
    if run_choice == "single":
        return False
    elif run_choice == "all":
        return True
    else:
        print("Invalid choice. Please choose 'single' or 'all'.")
        return choose_instances_num()

def choose_instance():
    instance_name = input("Please enter the instance file name (e.g., inst01): ").strip()
    instance_path = os.path.join(INSTANCES_PATH, instance_name + ".dat")
    if not os.path.exists(instance_path):
        print(f"Instance {instance_name} does not exist. Please try again.")
        return choose_instance()
    return instance_path

def run_solver(instance_path, solver_name, symbreak):
    """Runs the solver on the given instance."""
    params = utils.parse_instance(instance_path)

    return model.solve_mcp_mip(
        params=params,
        solver=solver_name,
        time_limit_sec=300,  # Set a time limit of 10 minutes
        add_symmetry_break=symbreak,
    )

# if __name__ == "__main__":
def run_mip():
    # Choose solver
    print("Welcome to the MIP Solver!")
    print("This program solves the MIP problem using different solvers.")
    print("Available solvers: Gurobi, CBC, HiGHS.")
    solver_name = choose_solver()
    symbreak = choose_symbreak()

    if symbreak:
        results_dir = os.path.join("MIP/result_symbreak", solver_name)
    else:
        results_dir = os.path.join("MIP/result_nosymbreak", solver_name)

    
    # Run on a single instance or all the instances
    if choose_instances_num(): 
        print("Running on all instances...")
        
        for instance_file in os.listdir(INSTANCES_PATH):
            if instance_file.endswith(".dat"):  # Ensure only .dat files are processed
                instance_path = os.path.join(INSTANCES_PATH, instance_file)
                print(f"Running on instance: {instance_file}")
                results = run_solver(instance_path, solver_name, symbreak)
                print(f"Results for {instance_file}: {results}")
                
                # Write results to file
                output_path = os.path.join(results_dir, f"{instance_file}.json")
                utils.write_output(results, output_path, solver_name)
    
    else:
        print("Running on a single instance...")

        instance_path = choose_instance()
        instance_name = os.path.basename(instance_path).split('.')[0]
        print(f"Running on instance: {instance_name}")
        
        results = run_solver(instance_path, solver_name, symbreak)
        print(f"Results for {instance_name}: {results}")

        # Write results to file
        output_path = os.path.join(results_dir, instance_name + ".json")
        utils.write_output(results, output_path, solver_name)

