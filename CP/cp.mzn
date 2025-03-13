include "globals.mzn";
include "alldifferent_except.mzn";
include "count_leq.mzn";
include "count.mzn";
include "value_precede.mzn";

% problem pars
int: M;
int: N;

set of int: LOADS = 1..M;
set of int: SIZES = 1..N;

array[LOADS] of int: L;
array[SIZES] of int: S;
array[1..N+1,1..N+1] of int: D;


% DECISION VARIABLES
array[1..M, 1..N+1] of var 1..N+1: routes; % Routes for each courier


% ---------------------------------------------------------------------------------------------------------------------
% CONSTRAINTS

% TWO COURIERS CANNOT GO TO THE SAME DISTRIBUTION POINT
% Value of all the variables must be different (except n+1 representing the origin point)
constraint 
  alldifferent_except(routes,{N+1});


% THE COURIER MUST FINISH IN THE ORIGIN POINT
% Force the value n+1 to appear at least once
constraint 
  forall(i in 1..M, j in N-M+2..N+1) (
    routes[i, j] = N + 1);


% ALL ITEMS NEED TO BE DELIVERED
% Force values from 1 to n to appear exactly once
constraint 
  forall(i in 1..N)(
    count(routes,i,1));


% ONCE RETURNED TO ORIGIN, A COURIER CANNOT DELIVER MORE
% Force all the numbers after the first n+1 to be also n+1
constraint 
  forall(i in 1..M, j in 1..N)(
      if routes[i,j]==N+1 then routes[i,j+1] = N+1 
        else true endif);


% AVOID COURIER OVERLOAD
% Force that the total size of items assigned to each courier cannot exceed their maximum load size
constraint
  forall(i in 1..M)(
    sum(j in 1..N where routes[i,j] != N+1)(S[routes[i,j]]) <= L[i]);

% ---------------------------------------------------------------------------------------------------------------------
% OBJECTIVE FUNCTION


%Application of the same objective function above to all couriers 
array[1..M] of var opt int: dist_courier =[sum(j in 1..N)(D[ routes[i, j], routes[i, j+1]]) +(D[N+1, routes[i,1]])|i in 1..M];


% ---------------------------------------------------------------------------------------------------------------------

% Solve
% Search annotations

ann: search_ann1 = int_search(routes, input_order, indomain_min);
ann: search_ann2 = int_search(routes, input_order, indomain_random);
ann: search_ann3 = int_search(routes, first_fail, indomain_min);
ann: search_ann4 = int_search(routes, first_fail, indomain_random);
ann: search_ann5 = int_search(routes, dom_w_deg, indomain_min); 
ann: search_ann6 = int_search(routes, dom_w_deg, indomain_random); 
 


solve :: search_ann3  minimize max(dist_courier);


       
output ["\(max(dist_courier))\n"];
output [show(routes[i, j]) ++ if j == N then "\n" else " " endif | i in 1..M, j in 1..N];

