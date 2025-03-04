var int: x;  % Prima variabile
var int: y;  % Seconda variabile

% Definiamo un dominio per x e y, ad esempio tra 0 e 10


% Constrains
constraint x + y = 10;

% Soluzione
solve satisfy;

% Mostra la soluzione
output ["x = ", show(x), ", y = ", show(y)];
