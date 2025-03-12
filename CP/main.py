from cp import *

class CP_instance:
    def __init__(self, filename, m, n, l, s, d):
        self.filename=filename
        self.m = m  # n. couriers
        self.n = n  # n. items
        self.l = l  # courier load
        self.s = s  # item size and endpoint
        self.d = d  # manhattan distance matrix

    def __repr__(self):
        return f"CP_instance(m={self.m}, n={self.n}, l={self.l}, s={self.s}, d={self.d})"
    
    def to_file(self, path):
        out_path = "".join([path, self.filename, '.dzn'])
        with open(out_path, 'w') as f:
            f.write('M = %d;\n' % self.m)
            f.write('N = %d;\n' % self.n)
            f.write('L = [' + ', '.join(map(str, self.l)) + '];\n')
            f.write('S = [' + ', '.join(f'{size}' for size in self.s) + '];\n')
            f.write('D = [')
            for row in self.d:
                f.write('|' + ','.join(map(str, row)) + '\n')
            f.write('|];\n')
        return out_path
    
def read_row_instances(path:str) -> CP_instance:
    filename = "".join(path.split('/')[-1].split('.')[:-1])
    with open(path, 'r') as f:
        matrix = ''
        for i, line in enumerate(f):
            if i == 0:
                m = int(line)
            elif i == 1:
                n = int(line)
            elif i == 2:
                l = [int(x) for x in line.split(' ')]   # load
            elif i == 3:
                s = [int(x) for x in line.split(' ')]   # item size
            else:
                matrix += line[:-1] + '; '
    d = np.matrix(matrix[:-2]).tolist()
    instance = CP_instance(filename,m,n,l,s,d)
    return instance

if __name__ == '__main__':
    module_path = os.path.dirname(os.path.realpath(__file__))
    savepath = module_path+'/instances/'

    path = "instances/inst01.dat"
    istc = read_row_instances(path)
    cp_path = istc.to_file(savepath)
    # cp_path = savepath+'inst01.dzn'
    print('percorso file che sta venendo caricato:',cp_path)
    cp_model(cp_path)
    




    ...
