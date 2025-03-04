var 0..10: x;  % Prima variabile
var 0..10: y;  % Seconda variabile

% Constrains
constraint x + y = 10;

% Soluzione
solve satisfy;

% Mostra la soluzione
output ["x = ", show(x), ", y = ", show(y)];
