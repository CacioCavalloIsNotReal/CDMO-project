from CP.utils import *
from CP.CP_file_instance import *
from CP.cp import *
from tqdm import tqdm

def execute_cp(instance_name: str, solver_name: str = 'gecode', symbreak: bool = True):
    solvers = ['gecode', 'chuffed']

    module_path = os.path.dirname(os.path.realpath(__file__))
    savepath = module_path+'/instances/'
    instances_path = "/".join(module_path.split('/')[:-1]+['instances'])
    instances_names = os.listdir(instances_path)
    if solver_name not in solvers:
        raise Exception(f"{solver_name} does not exist")
    if not type(symbreak) == bool:
        raise Exception(f"sb parameter must be boolean")
    
    if instance_name in instances_names:
        # execute cp and return result
        path = savepath+'/'+instance_name
        return cp_model(path,
                            verbose=False, 
                            symm_break=symbreak, 
                            solver=solver_name
                            ).get_solution()
    else:
        raise Exception(f"{instance_name} does not exist")
