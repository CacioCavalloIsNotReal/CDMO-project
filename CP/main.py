from CP.utils import *
from CP.CP_file_instance import *
from CP.cp import *
from tqdm import tqdm
     
def run_cp():
    convert_files=True
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
            cp_path = istc.to_file(savepath)

    outpath = "/".join(module_path.split('/')[:-1]+['res', 'CP'])
    dzn_names = os.listdir(savepath)    # list of dzn contained into CP/instances
    solutions = {name:{} for name in dzn_names}

    # pbar = tqdm(dzn_names)
    pbar = tqdm(['inst01.dzn','inst03.dzn','inst04.dzn','inst07.dzn'])
    for name in pbar:
        pbar.set_description(f"solving problem {name}")
        for solver in solvers:
            for sb in symm_break:
                path = savepath+'/'+name
                print(name, solver, sb)
                result_tmp = cp_model(path,
                                        verbose=True, 
                                        symm_break=sb, 
                                        solver=solver
                                        ).get_solution()
                solutions[name].update(result_tmp)
        save_result(solutions[name], outpath+'/'+'.'.join(name.split('.')[:-1]+['json']))
    # save_solutions(solutions, outpath)
    print("execution ended correctly")

if __name__ == '__main__':
    run_cp()
    '''
        constraint forall(i in 1..M)(
        courier_path_weight[i] =
            sum(k in 1..N-1)(
            let {
                var int: u = path[i,k],
                var int: v = path[i,k+1]
            } in
            sum(e in 1..E where FROM[e] = u /\ TO[e] = v)(W[e])
            )
        );
        

        V0
        constraint forall(i in 1..M)(
            forall(j in 1..sum(row(node_subset,i))-1
            where(node_subset[i, j]))(
                courier_path_weight[i] = sum(
                    k in 1..N where(
                        FROM[k] = path[i,j] /\
                        TO[k] = path[i,j+1]
                    ))(W[k])
            )
            );
                
        io ho bisogno di una grande mano
        constraint forall(i in 1..M)(
    courier_path_weight[i] = sum(j in 1..sum(row(node_subset,i))-1, k in 1..sum(row(node_subset,i))-1

        where
        
            path[i, FROM[k] ]=j    /\
            path[i, TO[k]   ]=j+1 
        
        )(W[k])
    );
    '''