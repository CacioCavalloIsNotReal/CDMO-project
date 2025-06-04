include "globals.mzn";

% pars
int: M;                     % n. of couriers
int: N;                     % n. of items
int: E;                     % n. of edges
array [1..M] of int: L;     % couerier maximum load
array [1..N-2] of int: S;   % item size/ endpoint
int: LOWER;                 % lower value for max_distance
%  graphs represented as lists of edges
array [1..E] of int: FROM;  % nodes of the graph
array [1..E] of int: TO;    % nodes of the graph
array [1..E] of int: W;     % weight of the link FROM[i] -> TO[i]

% vars 
var int: start;
var int: endpoint;
var int: max_distance;
array [1..M] of var int: courier_distances;
array [1..M, 1..N] of var bool: node_subset;  % subset of nodes for each courier
array [1..M, 1..E] of var bool: edge_subset;  % subset of edges for each courier

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

constraint forall(j in 1..N-2 )( % where i!=start /\ i!= endpoint
  sum(i in 1..M)(bool2int(node_subset[i, j])) = 1 % each node is visited once
);

constraint forall(i in 1..M)(  % evaluate current load of each courier
  current_load[i] = sum(j in 1..N-2)( % where i!=start /\ i!= endpoint
    node_subset[i,j]*S[j]
  )
);

constraint forall(i in 1..M)(  % each courier can't exceed its maximum load rating
  current_load[i] <= L[i]
);

% ************************************************************************************************
% ******************************************lower bound*******************************************
% ************************************************************************************************
constraint max_distance >= LOWER;

% ************************************************************************************************
% **************************this part reconstruct the ORDER OF THE PATH***************************
% ************************************************************************************************
array[1..M, 1..N] of var 0..N: path; 
array [1..M] of var int: evaluated_courier_distances;
var 1..M: max_index;

constraint forall(i in 1..M)(
  path[i, N-1]=1 /\                         % forces the start to be 1 (first point to be seen)
  path[i, N]=sum(row(node_subset,i)) /\     % forces the end to be sum(node_subset) (n of items the courier is transporting)

  forall(j in 1..N-2)(              % forces path[i,j] under consideration (if node_subset[i, j] is true) to be:
    if node_subset[i, j] then
      path[i, j]>1 /\                       % bigger than 0 -> courier cross the point  
      path[i, j]<path[i, N]                 % lower than the n of items the courier is transporting
    else
      path[i, j]=0
    endif
  ) /\
  alldifferent_except_0(row(path, i))       % each value which is not 0 (so the courier cross that point) must be differentcourier_distances
);

constraint forall(i in 1..M)(
  evaluated_courier_distances[i] =
    sum(         
      j in 1..path[i, N]-1,           % n. of items that must be transported, j= 1, 2, ... |node_subset|-1
      k in 1..E                       % index
    where                       % reconstruct the trajectory
      path[i, FROM[k] ]=j    /\
      path[i, TO[k]   ]=j+1 
    )(W[k])
);

constraint forall(i in 1..M)(
  evaluated_courier_distances[i] <= max_distance
);

constraint courier_distances[max_index] = max_distance;

constraint 
  if evaluated_courier_distances[max_index] < max_distance then
    courier_distances[max_index] = evaluated_courier_distances[max_index]
  endif;

constraint max_distance = max(courier_distances);

%       Search annotations https://docs.minizinc.dev/en/stable/mzn_search.html#finite-domain-search
% dom_w_deg     -> number of times it has been in a constraint that caused failure earlier in the search.
% indomain_min  -> choose the smallest value in the domain (the search is constrained from the start)
ann: search_assignment = bool_search(node_subset, dom_w_deg, indomain_min); 
% input_order   -> choose in order from the array
% indomain_min  -> choose the smallest value in the domain (the search is constrained from the start)
ann: search_sequencing = int_search(path, input_order, indomain_min); 
ann: search_combined = seq_search([
    search_assignment,  % first search an assignment here
    search_sequencing   % then here
]);
% this makes sense as node_subset has a boolean domain, path has integers
solve :: search_combined minimize max_distance
      :: restart_luby(1000);  % is an integer defining the initial number of nodes before the first restart. The second restart gets twice as many nodes, the third gets three times, etc.
% solve minimize max_distance;