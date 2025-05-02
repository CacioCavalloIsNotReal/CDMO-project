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
        E,
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

constraint forall(i in 1..M)(  % evaluate current load for each courier
  current_load[i] = sum(j in 1..N-2)(
    node_subset[i,j]*S[j]
  )
);

constraint forall(i in 1..M)(  % each courier can't exceed its maximum load rating
  current_load[i] <= L[i]
);

% symmetry breaking
constraint symmetry_breaking_constraint(
  forall(i in 1..M-1)(
    courier_distances[i] >= courier_distances[i+1]
  )
);

constraint max_distance = courier_distances[1]; % max(courier_distances);

% Search annotations
ann: search_ann1 = int_search(node_subset, input_order, indomain_min);
ann: search_ann2 = int_search(node_subset, input_order, indomain_random);
ann: search_ann3 = int_search(node_subset, first_fail, indomain_min);
ann: search_ann4 = int_search(node_subset, first_fail, indomain_random);
ann: search_ann5 = int_search(node_subset, dom_w_deg, indomain_min); 
ann: search_ann6 = int_search(node_subset, dom_w_deg, indomain_random); 

solve :: search_ann3  minimize max_distance;

