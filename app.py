from MIP.run import run_mip
from CP.main import run_cp

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
        print("SMT approach is not implemented yet.")
        exit(1)
    