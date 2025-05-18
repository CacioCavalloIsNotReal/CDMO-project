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
    row(node_subset, i),
    row(edge_subset, i),
    courier_distances[i]
  )
);

constraint forall(j in 1..N where(j!=start /\ j!= endpoint))( % each node is visited once
  sum(i in 1..M)(bool2int(node_subset[i, j])) = 1
);

constraint forall(j in 1..M)(  % evaluate current load of each courier
  current_load[j] = sum(i in 1..N where(i!=start /\ i!= endpoint))(
    node_subset[j,i]*S[i]
  )
);

constraint forall(j in 1..M)(  % each courier can't exceed its maximum load rating
  current_load[j] < L[j]+1
);

% symmetry breaking
constraint symmetry_breaking_constraint(
  forall(i in 1..M-1, j in i+1..M
    where L[i] == L[j])(  % want to lexicographically order only equivalent couriers
      lex_lesseq(
        [node_subset[i, k] | k in 1..N],
        [node_subset[j, k] | k in 1..N],
      )
    )
);

constraint max_distance = max(courier_distances);

% ************************************************************************************************
% **************************this part reconstruct the ORDER OF THE PATH***************************
% ************************************************************************************************
array[1..M, 1..N] of var 0..N: path; 
% array[1..M] of var int: courier_path_weight;

constraint forall(i in 1..M)(
  path[i, N-1]=1 /\                                 % forces the start to be 1 (first point to be seen)
  path[i, N]=sum(row(node_subset,i)) /\             % forces the end to be sum(node_subset) (n of items the courier is transporting)
  forall(j in 1..N where(node_subset[i, j]))(       % forces path[i,j] under consideration (if node_subset[i, j] is true) to be:
    path[i, j]>0 /\                                    % bigger than 0 -> courier cross the point  
    path[i, j]<=sum(row(node_subset,i))                % lower than the n of items the courier is transporting
  ) /\
  alldifferent(
    [path[i, j] | j in 1..N where(path[i, j]!=0)]  % each value which is not 0 (so the courier cross that point) must be different
  ) 
);

constraint forall(i in 1..M)(
   courier_distances[i] = sum(         % impose the order
      j in 1..sum(row(node_subset,i))-1,   % n. of items that must be transported, j= 1, 2, ... |node_subset|-1
      k in 1..E                            % index
     where                               % reconstruct the trajectory
        path[i, FROM[k] ]=j    /\
        path[i, TO[k]   ]=j+1 
    )(W[k])  % sum of weights visited in a certain order
);

% Search annotations
ann: search_ann1 = int_search(node_subset, input_order, indomain_min);
ann: search_ann2 = int_search(node_subset, input_order, indomain_random);
ann: search_ann3 = int_search(node_subset, first_fail, indomain_min);
ann: search_ann4 = int_search(node_subset, first_fail, indomain_random);
ann: search_ann5 = int_search(node_subset, dom_w_deg, indomain_min); 
ann: search_ann6 = int_search(node_subset, dom_w_deg, indomain_random); 

solve :: search_ann3 minimize max_distance;
% solve minimize max_distance;

