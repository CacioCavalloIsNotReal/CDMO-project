from MIP.run import run_mip
from CP.main import run_cp

# THIS IS JUST FOR TESTING PURPOSES
from SMT.smt_model import solve_mcp_smt
from MIP.mip_utils import parse_instance
# Choose what to run

if __name__ == "__main__":
    print("Welcome to the Problem Solver!")
    print("This program solves the problem using different approaches.")
    print("Available approaches: CP, MIP, SMT.")

    # Choose approach
    approach = input("Choose an approach (CP/MIP/SMT): ").strip().lower()
    if approach not in ["cp", "mip", "smt"]:
        print("Invalid choice. Please choose 'CP', 'MIP', or 'SMT'.")
        exit(1)
    elif approach == "cp":
        run_cp()
    elif approach == "mip":
        run_mip()
    elif approach == "smt":
        instance = input("instance name: ")
        instance = parse_instance("instances/" + instance + ".dat")
        solve_mcp_smt(instance)
        # print("SMT approach is not implemented yet.")
        # exit(1)
    