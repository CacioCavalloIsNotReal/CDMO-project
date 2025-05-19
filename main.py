from CP.cp_run import execute_cp
from MIP.mip_run import execute_mip
from SMT.smt_run import execute_smt
import sys


if __name__ == "__main__":

    approach = sys.argv[1]
    solver = sys.argv[2]
    symbreak = sys.argv[3].lower() == "true"
    instance = sys.argv[4]
    
    if approach == "cp":
        execute_cp(
            solver_name=solver,
            symbreak=symbreak,
            instance_name=instance
        )
    if approach == "mip":
        # EXAMPLE: python main.py mip gurobi False 1
        execute_mip(
            solver_name=solver, 
            symbreak=symbreak, 
            instance_name=instance
            )
    if approach == "smt":
        # EXAMPLE: python main.py smt z3 False 1
        execute_smt(symbreak, instance)
        execute_smt(
            symbreak=symbreak,
            instance_name=instance
        )