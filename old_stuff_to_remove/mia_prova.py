import numpy as np
import os
from tqdm import tqdm
from smt_utils import *
from smt_model import *

MAX_TIME = 5

if __name__=='__main__':


    symm_break = [True, False]

    module_path = os.path.dirname(os.path.realpath(__file__))
    outpath = "/".join(module_path.split('/')[:-1]+['res', 'SMT'])

    instances_folder =  "/".join(module_path.split('/')[:-1]+['instances'])
    file_names = sorted(os.listdir(instances_folder) )

    pbar = tqdm(file_names[:1])
    # pbar = tqdm(file_names[:1])
    # pbar = tqdm(file_names[-2:])
    for name in pbar:
        pbar.set_description(f"solving problem {name}")
        for sb in symm_break:
            path=instances_folder+f'/{name}'
            filename,m,n,l,s,d = read_raw_instances(path)
            print()
            print(filename,m,n,l,s,d)
            result_dict = run_z3_with_external_timeout(
                external_timeout_seconds=MAX_TIME,
                model_func=my_model,
                m=m, 
                n=n, 
                l=l, 
                s=s, 
                d=d,
                symm_break=sb, # Prova con True o False
                timeout=MAX_TIME # Timeout interno per Z3 (in ms)
            )
            print(result_dict)
    #         path=instances_folder+f'/{name}'
    #         filename,m,n,l,s,d = read_raw_instances(path)
    #         output = my_model(m,n,l,s,d,sb,2000)
    #         print(output)

    # print(filename)
    # indexed_l = list(enumerate(l)) 
    # sorted_indexed_l = sorted(indexed_l, key=lambda x: -x[1])
    # print(sorted_indexed_l)
    # new_l = [x[1] for x in sorted_indexed_l]
    # output = my_model(m,n,new_l,s,d)
    # permutation = [x[0] for x in sorted_indexed_l] 