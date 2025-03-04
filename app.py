import subprocess

# Comando per eseguire MiniZinc
command = ["minizinc", "examples/model0.mzn"]

# Esegui il comando e cattura l'output
result = subprocess.run(command, capture_output=True, text=True)

# Mostra l'output di MiniZinc
print(result.stdout)
