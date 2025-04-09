class CP_file_instance:
    def __init__(self, filename, m, n, l, s, d):
        self.filename=filename
        self.m = m  # n. couriers
        self.n = n  # n. items
        self.l = l  # courier load
        self.s = s  # item size and endpoint
        self.d = d  # manhattan distance matrix
        self.generate_graph()

    def __repr__(self):
        return f"instance(m={self.m}, n={self.n}, l={self.l}, s={self.s}, d={self.d})"
    
    def generate_graph(self):
        """
        it creates a new representation which consist in a set of vertices and edges of the graph
        G=(V,E)

        """
        n_nodes = self.n
        start = n_nodes+1
        end = n_nodes+2

        self.edges = []
        for i in [start]+list(range(1, start)):
            for j in range(1, end+1):
                if j!=start and (i,j)!=(start,end) and i!=j:
                    self.edges.append((i,j))

        self.weights = []
        for edge in self.edges:
            if edge[1]!=end:
                self.weights.append(self.d[edge[0]-1][edge[1]-1])
            else:
                self.weights.append(self.d[edge[0]-1][start-1])

    def get_graph(self):
        return self.edges, self.weights

    def to_file(self, path, raw=False):
        out_path = "".join([path, self.filename, '.dzn'])
        if raw:
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
        else:
            e, w = self.get_graph()

            _from = [i for i, j in e]
            _to = [j for i, j in e]

            with open(out_path, 'w') as f:
                f.write('M = %d;\n' % self.m)
                f.write('N = %d;\n' % (self.n+2))
                f.write('L = [' + ', '.join(map(str, self.l)) + '];\n')
                f.write('E = %d;\n' % (self.n**2 + self.n))
                f.write('S = [' + ', '.join(f'{size}' for size in self.s) + '];\n')
                f.write('FROM = %s;\n' % str(_from))
                f.write('TO = %s;\n' % str(_to))
                f.write('W = %s;\n' % str(w))
            return out_path

