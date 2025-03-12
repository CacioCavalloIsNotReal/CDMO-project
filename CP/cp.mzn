% problem pars
int: M;
int: N;
array[1..M] of int: L;
array[1..N] of int: S;
array[1..N+1,1..N+1] of int: D;

% Numero massimo di archi
int: e = (N+1)*(N+1);

array[1..e] of var 1..N+1: _from;
array[1..e] of var 1..N+1: _to;
array[1..e] of var 0..max(D): _weight;

constraint forall (i in 1..N+1, j in 1..N+1 where i != j)(
    _from[i]=i/\
    _to[j]=j/\
    _weight[(N+1)*i+j]=D[i,j]
);

solve satisfy;

output [show(_from)," ",show(_to)," ",show(_weight)];
