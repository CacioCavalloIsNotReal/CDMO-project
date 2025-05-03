from CP.utils import *
from CP.CP_file_instance import *
from CP.cp import *
from tqdm import tqdm
     
def run_cp():
    convert_files=False
    solvers = ['gecode', 'chuffed']
    symm_break = [True, False]

    module_path = os.path.dirname(os.path.realpath(__file__))
    savepath = module_path+'/instances/'
    instances_path = "/".join(module_path.split('/')[:-1]+['instances'])
    instances_names = os.listdir(instances_path)

    if convert_files:
        for name in tqdm(instances_names, desc="Converting instances into .dzn files"):
            # creating the .dzn file
            path = instances_path+'/'+name
            istc = read_raw_instances(path)
            cp_path = istc.to_file(savepath, raw=False)
    
    dzn_names = os.listdir(savepath)    # list of dzn contained into CP/instances
    solutions = {name:[] for name in dzn_names}
    for name in tqdm(dzn_names[:1]):
        for solver in solvers:
            for sb in symm_break:
                path = savepath+'/'+name
                solutions[name].append(cp_model(path,
                                                verbose=False, 
                                                symm_break=sb, 
                                                solver=solver
                                                ).get_solution()) 
    outpath = "/".join(module_path.split('/')[:-1]+['res', 'CP'])
    save_solutions(solutions, outpath)
    print("execution ended correctly")

if __name__ == '__main__':
    run_cp()