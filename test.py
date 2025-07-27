import os
import urllib.request
import pandas as pd
import numpy as np
from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.termination import get_termination
from pymoo.optimize import minimize
import matplotlib.pyplot as plt

"""
NSGA‑II Meal‑Planning Prototype (dynamic nutrient detection)
===========================================================

This version dynamically detects macro, fiber, and sodium column names
from the USDA/CORGIS CSV. If fiber or sodium columns are missing, it
initializes them to zero arrays (and warns).

Objectives:
1. Minimize summed relative macro deviation
2. Minimize total food weight (g)
3. Minimize sodium overage
4. Minimize fiber shortfall
5. Minimize carbon footprint (optional via footprint.csv)
6. Minimize micronutrient deficiency across 15+ vitamins and minerals

Quick Start:
1) pip install pandas numpy matplotlib pymoo
2) python test.py
"""

# 1. Setup and download
DATA_DIR  = "data"
USDA_URL  = "https://corgis-edu.github.io/corgis/datasets/csv/food/food.csv"
FOODS_CSV = os.path.join(DATA_DIR, "food.csv")
FP_CSV    = os.path.join(DATA_DIR, "footprint.csv")

os.makedirs(DATA_DIR, exist_ok=True)
if not os.path.exists(FOODS_CSV):
    print("Downloading USDA data...")
    urllib.request.urlretrieve(USDA_URL, FOODS_CSV)

# 2. Load dataset and detect columns
df = pd.read_csv(FOODS_CSV)
# Normalize column names
df.columns = [c.replace(" ", "_").replace(".", "_") for c in df.columns]
# Detect columns dynamically
protein_col = next((c for c in df.columns if 'protein' in c.lower()), None)
carb_col    = next((c for c in df.columns if 'carbohydrate' in c.lower()), None)
fat_col     = next((c for c in df.columns if 'lipid' in c.lower() or 'fat_total' in c.lower()), None)
fiber_col   = next((c for c in df.columns if 'fiber' in c.lower()), None)
sodium_col  = next((c for c in df.columns if 'sodium' in c.lower()), None)

# Detect micronutrient columns of interest
micros = {
    'calcium':  'data_major_minerals_calcium',
    'iron':     'data_major_minerals_iron',
    'magnesium':'data_major_minerals_magnesium',
    'phosphorus':'data_major_minerals_phosphorus',
    'potassium':'data_major_minerals_potassium',
    'zinc':     'data_major_minerals_zinc',
    'selenium': 'data_selenium',
    'choline':  'data_choline',
    'vitamin_a':'data_vitamins_vitamin_a_-_rae',
    'vitamin_b6':'data_vitamins_vitamin_b6',
    'vitamin_b12':'data_vitamins_vitamin_b12',
    'vitamin_c':'data_vitamins_vitamin_c',
    'vitamin_e':'data_vitamins_vitamin_e',
    'vitamin_k':'data_vitamins_vitamin_k',
    'riboflavin':'data_riboflavin',
    'thiamin':  'data_thiamin',
    'niacin':   'data_niacin'
}
for k, col in list(micros.items()):
    found = next((c for c in df.columns if c.lower() == col), None)
    if found:
        micros[k] = found
    else:
        print(f"Warning: {k} column not found; using zeros for {k}.")
        micros[k] = None

# Ensure required macros are present
for col in [protein_col, carb_col, fat_col]:
    if col is None:
        raise KeyError("Required macro column not found in USDA data.")

# Warn if optional nutrients are missing
if fiber_col is None:
    print("Warning: Fiber column not found; using zeros for fiber.")
if sodium_col is None:
    print("Warning: Sodium column not found; using zeros for sodium.")

# Drop rows missing required values or optional if detected
required_cols = [protein_col, carb_col, fat_col]
optional_cols = [c for c in [fiber_col, sodium_col] if c]
optional_cols += [c for c in micros.values() if c]
df_clean = df.dropna(subset=required_cols + optional_cols)

# Compute calories if not present
df_clean['calories'] = (
    4 * df_clean[protein_col] +
    4 * df_clean[carb_col] +
    9 * df_clean[fat_col]
)

# 3. Sample subset for speed
MAX_FOODS = 200
df_samp = df_clean.sample(n=min(len(df_clean), MAX_FOODS), random_state=1).reset_index(drop=True)
N = len(df_samp)

# 4. Extract nutrient arrays per 100 g
CALS   = df_samp['calories'].to_numpy()
PRO    = df_samp[protein_col].to_numpy()
FAT    = df_samp[fat_col].to_numpy()
CARB   = df_samp[carb_col].to_numpy()
FIBER  = df_samp[fiber_col].to_numpy() if fiber_col else np.zeros(N)
SODIUM = df_samp[sodium_col].to_numpy() if sodium_col else np.zeros(N)
DESC   = df_samp['Description'].to_list()

# Micronutrient arrays
MICRO_ARRS = {}
for k, col in micros.items():
    # store per-food amounts for each micronutrient (0 if column missing)
    MICRO_ARRS[k] = df_samp[col].to_numpy() if col else np.zeros(N)

# 5. Load sustainability data if available
if os.path.exists(FP_CSV):
    fp_df = pd.read_csv(FP_CSV)
    merged = df_samp.merge(fp_df, on='Description', how='left')
    fp_arr = merged['footprint_kgCO2e_per_kg'].fillna(fp_df['footprint_kgCO2e_per_kg'].mean()).to_numpy()
else:
    fp_arr = np.zeros(N)

# 6. Define daily targets
targets_macro = np.array([2000, 50, 70, 310])  # cal, protein, fat, carbs
target_fiber  = 25    # g/day minimum
target_sodium = 2300  # mg/day maximum

# Recommended Dietary Allowances for select micronutrients
# Units are mg unless noted otherwise (vitamin_a, vitamin_b12, selenium in mcg)
RDA = {
    'calcium': 1000,
    'iron': 18,
    'magnesium': 400,
    'phosphorus': 700,
    'potassium': 4700,
    'zinc': 11,
    'selenium': 55,
    'choline': 550,
    'vitamin_a': 900,
    'vitamin_b6': 1.3,
    'vitamin_b12': 2.4,
    'vitamin_c': 90,
    'vitamin_e': 15,
    'vitamin_k': 120,
    'riboflavin': 1.3,
    'thiamin': 1.2,
    'niacin': 16,
}

# 7. Define the Problem
class ExtendedMealPlan(Problem):
    def __init__(self):
        super().__init__(n_var=N, n_obj=6, n_constr=0,
                         xl=np.zeros(N), xu=np.full(N, 500))

    def _evaluate(self, X, out, *args, **kwargs):
        q = X / 100.0
        # Total macros
        totals = np.column_stack([
            q @ CALS,  # calories
            q @ PRO,
            q @ FAT,
            q @ CARB
        ])
        # Objective 1: Macro deviation
        dev = np.abs(totals - targets_macro) / targets_macro
        f1 = dev.sum(axis=1)
        # Objective 2: Total weight
        f2 = X.sum(axis=1)
        # Objective 3: Sodium overage
        f3 = np.maximum(q @ SODIUM - target_sodium, 0) / target_sodium
        # Objective 4: Fiber shortfall
        f4 = np.maximum(target_fiber - (q @ FIBER), 0) / target_fiber
        # Objective 5: Carbon footprint
        f5 = (X / 1000) @ fp_arr

        # Objective 6: Micronutrient deficiency
        micro_totals = np.column_stack([q @ MICRO_ARRS[k] for k in RDA.keys()])
        rdas = np.array(list(RDA.values()))
        completeness = micro_totals / rdas
        deficiency = np.maximum(1 - completeness, 0)
        f6 = deficiency.mean(axis=1)

        out['F'] = np.column_stack([f1, f2, f3, f4, f5, f6])

# 8. Run NSGA-II
if __name__ == '__main__':
    problem = ExtendedMealPlan()
    algorithm = NSGA2(pop_size=150)
    termination = get_termination('n_gen', 300)
    result = minimize(problem, algorithm, termination, seed=42, verbose=True)

    print(f"Pareto-optimal solutions: {result.X.shape[0]}")
    for i in range(min(5, result.X.shape[0])):
        print(f"\nSolution {i+1}:")
        print(f"  Macro dev: {result.F[i,0]:.3f}")
        print(f"  Total wt : {result.F[i,1]:.0f} g")
        print(f"  Sodium   : {result.F[i,2]:.3f}")
        print(f"  Fiber    : {result.F[i,3]:.3f}")
        print(f"  Footprint: {result.F[i,4]:.3f} kgCO2e")
        print(f"  Micro def: {result.F[i,5]:.3f}")
        for idx, g in enumerate(result.X[i]):
            if g >= 10:
                print(f"   {DESC[idx][:30]:30s} » {int(g)}g")

    # Plot Nutrition vs Sustainability
    plt.scatter(result.F[:,0], result.F[:,4])
    plt.xlabel('Macro Deviation')
    plt.ylabel('Carbon Footprint (kgCO2e)')
    plt.title('Pareto Front: Nutrition vs Footprint')
    plt.grid(True)
    plt.tight_layout()

    # Micro deficiency vs Macro deviation
    plt.figure()
    plt.scatter(result.F[:,0], result.F[:,5], c='orange')
    plt.xlabel('Macro Deviation')
    plt.ylabel('Micronutrient Deficiency')
    plt.title('Macro vs Micro Balance')
    plt.grid(True)

    # Radar plot of micronutrient completeness for best solution
    best = result.X[0]
    q = best / 100.0
    micro_totals = [q @ MICRO_ARRS[k] for k in RDA.keys()]
    completeness = np.minimum(np.array(micro_totals) / np.array(list(RDA.values())), 1)
    labels = list(RDA.keys())
    angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
    completeness = np.concatenate((completeness, [completeness[0]]))
    angles += angles[:1]
    fig = plt.figure(figsize=(6,6))
    ax = fig.add_subplot(111, polar=True)
    ax.plot(angles, completeness, 'o-', linewidth=2)
    ax.fill(angles, completeness, alpha=0.25)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels)
    ax.set_title('Micronutrient Completeness')
    ax.set_ylim(0,1)

    plt.show()
