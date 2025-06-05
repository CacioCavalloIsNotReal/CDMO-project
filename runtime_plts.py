import os
import json
from collections import defaultdict
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt

def main():
    folder = 'res/CP/'
    files = sorted(os.listdir(folder))
    runtime = defaultdict(dict)

    for index, file_name in enumerate(files):
        file_path = os.path.join(folder, file_name)
        with open(file_path) as f:
            data = json.load(f)
            for solver, solver_data in data.items():
                runtime[solver][index] = solver_data['time']

    solvers = list(runtime.keys())
    fig, axs = plt.subplots(int(len(solvers)/2), 2, figsize=(12, 4*int(len(solvers)/2))) 
    axs = axs.flatten()  

    for i, solver in enumerate(solvers):
        times = [runtime[solver][j] for j in sorted(runtime[solver])]
        x_vals = list(range(1,len(times)+1))
        axs[i].bar(x_vals, times, color='gray')
        axs[i].set_xticks(x_vals)
        axs[i].set_xticklabels(x_vals, rotation=90)  # rotazione opzionale

        axs[i].set_title(f'{solver}')
        axs[i].set_xlabel('Instance')
        axs[i].set_ylabel('Time (s)')
        axs[i].grid(True, axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.savefig(f"{folder.split('/')[-2]}.png")
    plt.show()

if __name__ == '__main__':
    main()


