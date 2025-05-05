from CP.utils import read_raw_instances
from .CP_file_instance import *
from .cp import *
from tqdm import tqdm

def run_cp():
# if __name__ == '__main__':
    convert_files=False

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

    solutions = []
    dzn_names = os.listdir(savepath)    # list of dzn contained into CP/instances
    for name in dzn_names[:10]:
        path = savepath+'/'+name
        solutions.append(cp_model(path, verbose=True)) 

    for solution in solutions:
        print(solution.failed)
