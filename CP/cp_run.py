from CP.utils import *
from CP.CP_file_instance import *
from CP.cp import *
from tqdm import tqdm

def execute_cp(solver_name, symbreak, instance_name):
    convert_files=True
    solvers = ['gecode', 'chuffed']
    symm_break = [True, False]

    if solver_name not in solvers:
        return "Solver spelled wrong or not implemented"
    
    if instance_name == "all":
        module_path = os.path.dirname(os.path.realpath(__file__))
        savepath = module_path+'/instances/'
        instances_path = "/".join(module_path.split('/')[:-1]+['instances'])
        instances_names = os.listdir(instances_path)

        if convert_files:
            for name in tqdm(instances_names, desc="Converting instances into .dzn files"):
                # creating the .dzn file
                path = instances_path+'/'+name
                istc = read_raw_instances(path)
                cp_path = istc.to_file(savepath)

        outpath = "/".join(module_path.split('/')[:-1]+['res', 'CP'])
        dzn_names = os.listdir(savepath)    # list of dzn contained into CP/instances
        solutions = {name:{} for name in dzn_names}

        pbar = tqdm(dzn_names)
        # pbar = tqdm(['inst01.dzn','inst03.dzn','inst07.dzn'])
        for name in pbar:
            pbar.set_description(f"solving problem {name}")
            for solver in solvers:
                for sb in symm_break:
                    path = savepath+'/'+name
                    result_tmp = cp_model(path,
                                            verbose=True, 
                                            symm_break=sb, 
                                            solver=solver
                                            ).get_solution()
                    solutions[name].update(result_tmp)
            save_result(solutions[name], outpath+'/'+'.'.join(name.split('.')[:-1]+['json']))
        # save_solutions(solutions, outpath)
        print("execution ended correctly")