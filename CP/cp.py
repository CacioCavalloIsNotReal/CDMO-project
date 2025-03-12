import os
import numpy as np
import datetime
import minizinc
from minizinc import Instance, Model, Solver, Status

print("Minizinc Python API version:", minizinc.__version__, '\n')
module_path = os.path.dirname(os.path.realpath(__file__))
print(module_path)

def cp_model( instance_file, solver:str = 'gecode', time_limit:int=300)->dict:
    output = {}
    
    cp_model = Model(module_path+'/cp.mzn')
    cp_model.add_file(instance_file, parse_data=True)
    print('CP model loaded')

    solver_ins = Solver.lookup(solver)
    instance = Instance(solver_ins, cp_model)

    result = instance.solve(timeout=datetime.timedelta(seconds=time_limit), intermediate_solutions=True)

    for _, solution in (enumerate(result)):
        print(solution._from)
        print(solution._to)
        print(solution._weight)
        #print(solution.c)
        print()

    return output