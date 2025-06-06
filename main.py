import sys
from CP.cp_run import execute_cp
import os
from contextlib import redirect_stdout, redirect_stderr
# Suppress Gurobi license messages during import
with open(os.devnull, 'w') as devnull:
    with redirect_stdout(devnull), redirect_stderr(devnull):
        from MIP.mip_run import execute_mip
from SMT.smt_run import execute_smt

if __name__ == "__main__":

    try:
        approach = sys.argv[1]
        solver = sys.argv[2]
        symbreak = sys.argv[3].lower() == "true"
        instance = sys.argv[4]      # integer os str, if str then 'all' is considered

        if approach == "cp":
            execute_cp(
                instance_name=instance,
                solver_name=solver,
                symbreak=symbreak,
            )
            
        if approach == "mip":
            
            
            # EXAMPLE: python main.py mip gurobi False 1
            # You can choose between gurobi and highs
            execute_mip(
                solver_name=solver, 
                symbreak=symbreak, 
                instance_name=instance
                )
            
        if approach == "smt":
            # EXAMPLE: python main.py smt z3 False 1
            # The only solver supported is z3
            execute_smt(
                symbreak=symbreak,
                instance_name=instance
            )
    except Exception as e:
        print("Wrong values, try again", e)

