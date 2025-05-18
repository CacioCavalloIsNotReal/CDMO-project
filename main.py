from MIP.mip_run import execute_mip
from CP.cp_run import execute_cp
import sys


if __name__ == "__main__":

    approach = sys.argv[1]
    solver = sys.argv[2]
    symbreak = sys.argv[3]
    instance = sys.argv[4]
    
    if approach == "cp":
        execute_cp(instance, solver, symbreak)
    if approach == "mip":
        # EXAMPLE: python main.py mip gurobi False 1
        execute_mip(solver, symbreak, instance)
