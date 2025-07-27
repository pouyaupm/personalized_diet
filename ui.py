import argparse
from optimizer import run_optimization, OBJECTIVE_NAMES, RDA
from visualization import plot_objectives, plot_radar


def display_solution(result, idx):
    arrays = result.arrays
    X = result.X[idx]
    q = X / 100.0
    totals = {
        'Calories': q @ arrays['CALS'],
        'Protein': q @ arrays['PRO'],
        'Fat': q @ arrays['FAT'],
        'Carbs': q @ arrays['CARB'],
        'Fiber': q @ arrays['FIBER'],
        'Sodium': q @ arrays['SODIUM'],
    }
    print(f"\nSolution {idx} summary:")
    for k, v in totals.items():
        print(f"  {k:8s}: {v:.1f}")
    for g, desc in zip(X, arrays['DESC']):
        if g >= 10:
            print(f"   {desc[:30]:30s} » {int(g)}g")
    plot_radar(result, idx, arrays['MICRO'], RDA)


def main():
    parser = argparse.ArgumentParser(description="Meal Plan Optimizer UI")
    parser.add_argument('--objectives', default='0,1', help='Comma-separated objective indices to plot')
    args = parser.parse_args()

    result = run_optimization()
    indices = [int(i) for i in args.objectives.split(',') if i.strip().isdigit()]
    if not indices:
        print('No valid objectives selected; using 0,1')
        indices = [0, 1]

    print("Objectives:")
    for i, name in enumerate(OBJECTIVE_NAMES):
        print(f"  {i}: {name}")
    print(f"Plotting objectives: {indices}")
    plot_objectives(result, indices, OBJECTIVE_NAMES)

    print(f"Pareto set contains {result.F.shape[0]} solutions.")
    try:
        sel = int(input("Select solution index to view details (0-based): "))
    except Exception:
        sel = 0
    sel = max(0, min(sel, result.F.shape[0]-1))
    display_solution(result, sel)


if __name__ == '__main__':
    main()
