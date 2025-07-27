import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def plot_objectives(result, obj_indices, names):
    n = len(obj_indices)
    F = result.F[:, obj_indices]

    if n == 2:
        plt.figure()
        plt.scatter(F[:, 0], F[:, 1])
        plt.xlabel(names[obj_indices[0]])
        plt.ylabel(names[obj_indices[1]])
        plt.title('Objective Scatter Plot')
        plt.grid(True)
    elif n == 3:
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter(F[:, 0], F[:, 1], F[:, 2])
        ax.set_xlabel(names[obj_indices[0]])
        ax.set_ylabel(names[obj_indices[1]])
        ax.set_zlabel(names[obj_indices[2]])
        ax.set_title('3D Objective Scatter')
    else:
        df = pd.DataFrame(F, columns=[names[i] for i in obj_indices])
        plt.figure()
        pd.plotting.parallel_coordinates(df.reset_index(), 'index')
        plt.title('Parallel Coordinates of Objectives')
        plt.legend([])
    plt.tight_layout()
    plt.show()


def plot_radar(result, sol_index, micro_arrays, rda):
    q = result.X[sol_index] / 100.0
    micro_totals = [q @ micro_arrays[k] for k in rda.keys()]
    completeness = np.minimum(np.array(micro_totals) / np.array(list(rda.values())), 1)
    labels = list(rda.keys())
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    completeness = np.concatenate((completeness, [completeness[0]]))
    angles += angles[:1]
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, polar=True)
    ax.plot(angles, completeness, 'o-', linewidth=2)
    ax.fill(angles, completeness, alpha=0.25)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels)
    ax.set_title('Micronutrient Completeness')
    ax.set_ylim(0, 1)
    plt.tight_layout()
    plt.show()
