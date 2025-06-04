import numpy as np
import networkx as nx
import json 

class CP_file_instance:
    def __init__(self, filename, m, n, l, s, d):
        self.filename=filename
        self.m = m  # n. couriers
        self.n = n  # n. items
        self.l = l  # courier load
        self.s = s  # item size and endpoint
        self.d = np.array(d)  # manhattan distance matrix
        self.generate_graph()
        self.lower = self.generate_lowerbound()

    def __repr__(self):
        return f"instance(m={self.m}, n={self.n}, l={self.l}, s={self.s}, d={self.d})"
    
    def generate_lowerbound(self):
        distances = []
        for i in range(self.n):
            distances.append(self.d[i][self.n] + self.d[self.n][i])
        return max(distances)

    def generate_graph(self):
        """
        it creates a new representation which consist in a set of vertices and edges of the graph
        G=(V,E)

        """
        tmp_d = np.vstack([self.d, self.d[-1,:]])
        tmp_d = np.hstack([tmp_d, tmp_d[:, -1].reshape(-1, 1)]) # nb the square on the bottom right corner means you can't go from start to end, thats why its all 0

        start = tmp_d.shape[0]-2 # eg. 9x9, 9-2=7

        G = nx.from_numpy_array(tmp_d, create_using=nx.DiGraph) # created the directed, weighted graph
        to_be_removed = [(u, v)
                         for u, v in G.edges 
                         if     u==start+1    # cant start from the end
                            or  v==start      # we do not want to go back to the starting poing
                            or  u==v]        # can't stay in the same place
        
        G.remove_edges_from(to_be_removed)

        self.graph = G
        self.edges = G.edges

        edges_array = np.array(G.edges).T

        self.e_from = edges_array[0]+1 # indexes strat from 1 
        self.e_to   = edges_array[1]+1

        self.weights = [G[u][v]['weight'] for u, v in G.edges ]
        
    def get_graph(self):
        return self.edges, self.weights

    def to_file(self, path):
        out_path = "".join([path, self.filename, '.dzn'])

        with open(out_path, 'w') as f:
            f.write('M = %d;\n' % self.m)
            f.write('N = %d;\n' % (self.n+2))
            f.write('L = [' + ', '.join(map(str, self.l)) + '];\n')
            f.write('E = %d;\n' % (len(self.e_from)))# (self.n**2 + self.n))
            f.write('S = [' + ', '.join(f'{size}' for size in self.s) + '];\n')
            f.write('LOWER = %d;\n' % self.lower)
            
            f.write('FROM = %s;\n' % json.dumps(self.e_from.tolist()))
            f.write('TO = %s;\n' % json.dumps(self.e_to.tolist()))
            f.write('W = %s;\n' % json.dumps(self.weights))
        return out_path