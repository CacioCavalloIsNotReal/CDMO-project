include "globals.mzn";

% pars
int: M;                     % n. of couriers
int: N;                     % n. of items
int: E;                     % n. of edges
array [1..M] of int: L;     % couerier maximum load
array [1..N-2] of int: S;   % item size/ endpoint
%  graphs represented as lists of edges
array [1..E] of int: FROM;  % nodes of the graph
array [1..E] of int: TO;    % nodes of the graph
array [1..E] of int: W;     % weight of the link FROM[i] -> TO[i]

% vars 
var int: start;
var int: endpoint;
var int: max_distance;
array [1..M] of var int: courier_distances;
array [1..M, 1..N] of var bool: node_subset;
array [1..M, 1..E] of var bool: edge_subset;

array [1..M] of var int: current_load;

% constraints
constraint start = N - 1;    % where each path begin
constraint endpoint = N;     % there each path end

% it verify the existance of a path from a node s
% to a node t with weight k
% ns, es subset of nodes representing the path


constraint forall(i in 1..M)(   % for each courier evaluate bounded_dpath
    bounded_dpath(  % doc: https://docs.minizinc.dev/en/stable/lib-globals-graph.html
        N,
        E,% doc: https://docs.minizinc.dev/en/stable/lib-globals-graph.html
        FROM,
        TO,
        W,
        start,
        endpoint,
        [node_subset[i, j] | j in 1..N],
        [edge_subset[i, j] | j in 1..E],
        courier_distances[i]
    )
);

constraint forall(j in 1..N-2)( % each node is visited once
  sum(i in 1..M)(bool2int(node_subset[i, j])) = 1
);

constraint forall(j in 1..M)(  % evaluate current load of each courier
  current_load[j] = sum(i in 1..N-2)(
    node_subset[j,i]*S[i]
  )
);

constraint forall(j in 1..M)(  % each courier can't exceed its maximum load rating
  current_load[j] <= L[j]
);

constraint max_distance = max(courier_distances);

solve minimize max_distance;

output [
  "Nodi nel cammino: ", show(node_subset), "\n",
  "Archi nel cammino: ", show(edge_subset), "\n",
  "Peso totale: ", show(max_distance)
];