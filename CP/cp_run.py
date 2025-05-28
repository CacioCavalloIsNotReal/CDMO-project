from CP.utils import *
from CP.CP_file_instance import *
from CP.cp import *
from tqdm import tqdm

def execute_cp(instance_name: str, solver_name: str = 'gecode', symbreak: bool = True):
    solvers = ['gecode', 'chuffed']
    symm_break = [True, False]

    module_path = os.path.dirname(os.path.realpath(__file__))
    savepath = module_path+'/instances/'
    instances_path = "/".join(module_path.split('/')[:-1]+['instances'])
    instances_names = os.listdir(instances_path)
    if solver_name not in solvers:
        raise Exception(f"{solver_name} does not exist")
    if not type(symbreak) == bool:
        raise Exception(f"sb parameter must be boolean")
    
    # Converting all instances
    for name in tqdm(instances_names, desc="Converting instances into .dzn files"):
        # creating the .dzn file
        path = instances_path+'/'+name
        istc = read_raw_instances(path)
        istc.to_file(savepath)

    outpath = "/".join(module_path.split('/')[:-1]+['res', 'CP'])
    os.makedirs(outpath, exist_ok=True)
    dzn_names = os.listdir(savepath)    # list of dzn contained into CP/instances

    solutions = {name:{} for name in dzn_names}

    try:
        inst = int(instance_name)

        instance_name = choose_instance(inst)

        if instance_name in dzn_names:
            # execute cp and return result
            path = savepath+instance_name

            result_tmp = cp_model(path,
                                verbose=False, 
                                symm_break=symbreak, 
                                solver=solver_name
                                ).get_solution()
            solutions[instance_name].update(result_tmp)
            save_result(solutions[instance_name], outpath+'/'+'.'.join(instance_name.split('.')[:-1]+['json']))
        
    except ValueError as e:
        # instance_name is a string all
        pbar = tqdm(sorted(dzn_names))
        for name in pbar:
            pbar.set_description(f"solving problem {name}")
            for solver in solvers:
                for sb in symm_break:
                    path = savepath+'/'+name
                    
                    result_tmp = cp_model(path,
                                            verbose=False, 
                                            symm_break=sb, 
                                            solver=solver
                                            ).get_solution()
                    solutions[name].update(result_tmp)
            save_result(solutions[name], outpath+'/'+'.'.join(name.split('.')[:-1]+['json']))
        # save_solutions(solutions, outpath)
    print("execution ended correctly")
    
