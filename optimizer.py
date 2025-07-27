import os
import urllib.request
import pandas as pd
import numpy as np
from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.termination import get_termination
from pymoo.optimize import minimize

DATA_DIR = "data"
USDA_URL = "https://corgis-edu.github.io/corgis/datasets/csv/food/food.csv"
FOODS_CSV = os.path.join(DATA_DIR, "food.csv")
FP_CSV = os.path.join(DATA_DIR, "footprint.csv")

OBJECTIVE_NAMES = [
    "Macro Deviation",
    "Total Weight",
    "Sodium Overage",
    "Fiber Shortfall",
    "Carbon Footprint",
    "Micronutrient Deficiency",
]

# Recommended Dietary Allowances (mg except where noted)
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


def _load_dataset():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(FOODS_CSV):
        print("Downloading USDA data...")
        urllib.request.urlretrieve(USDA_URL, FOODS_CSV)
    df = pd.read_csv(FOODS_CSV)
    df.columns = [c.replace(" ", "_").replace(".", "_") for c in df.columns]
    return df


def _detect_columns(df):
    protein_col = next((c for c in df.columns if 'protein' in c.lower()), None)
    carb_col = next((c for c in df.columns if 'carbohydrate' in c.lower()), None)
    fat_col = next((c for c in df.columns if 'lipid' in c.lower() or 'fat_total' in c.lower()), None)
    fiber_col = next((c for c in df.columns if 'fiber' in c.lower()), None)
    sodium_col = next((c for c in df.columns if 'sodium' in c.lower()), None)

    micros = {
        'calcium': 'data_major_minerals_calcium',
        'iron': 'data_major_minerals_iron',
        'magnesium': 'data_major_minerals_magnesium',
        'phosphorus': 'data_major_minerals_phosphorus',
        'potassium': 'data_major_minerals_potassium',
        'zinc': 'data_major_minerals_zinc',
        'selenium': 'data_selenium',
        'choline': 'data_choline',
        'vitamin_a': 'data_vitamins_vitamin_a_-_rae',
        'vitamin_b6': 'data_vitamins_vitamin_b6',
        'vitamin_b12': 'data_vitamins_vitamin_b12',
        'vitamin_c': 'data_vitamins_vitamin_c',
        'vitamin_e': 'data_vitamins_vitamin_e',
        'vitamin_k': 'data_vitamins_vitamin_k',
        'riboflavin': 'data_riboflavin',
        'thiamin': 'data_thiamin',
        'niacin': 'data_niacin',
    }
    for k, col in list(micros.items()):
        found = next((c for c in df.columns if c.lower() == col), None)
        if found:
            micros[k] = found
        else:
            print(f"Warning: {k} column not found; using zeros for {k}.")
            micros[k] = None
    return protein_col, carb_col, fat_col, fiber_col, sodium_col, micros


def _prepare_arrays(df, protein_col, carb_col, fat_col, fiber_col, sodium_col, micros):
    required_cols = [protein_col, carb_col, fat_col]
    optional_cols = [c for c in [fiber_col, sodium_col] if c]
    optional_cols += [c for c in micros.values() if c]
    df_clean = df.dropna(subset=required_cols + optional_cols)

    df_clean['calories'] = (
        4 * df_clean[protein_col] + 4 * df_clean[carb_col] + 9 * df_clean[fat_col]
    )

    MAX_FOODS = 200
    df_samp = df_clean.sample(n=min(len(df_clean), MAX_FOODS), random_state=1).reset_index(drop=True)
    n = len(df_samp)

    arrays = {
        'CALS': df_samp['calories'].to_numpy(),
        'PRO': df_samp[protein_col].to_numpy(),
        'FAT': df_samp[fat_col].to_numpy(),
        'CARB': df_samp[carb_col].to_numpy(),
        'FIBER': df_samp[fiber_col].to_numpy() if fiber_col else np.zeros(n),
        'SODIUM': df_samp[sodium_col].to_numpy() if sodium_col else np.zeros(n),
        'DESC': df_samp['Description'].to_list(),
    }

    micro_arrs = {}
    for k, col in micros.items():
        micro_arrs[k] = df_samp[col].to_numpy() if col else np.zeros(n)
    arrays['MICRO'] = micro_arrs

    if os.path.exists(FP_CSV):
        fp_df = pd.read_csv(FP_CSV)
        merged = df_samp.merge(fp_df, on='Description', how='left')
        arrays['FP'] = merged['footprint_kgCO2e_per_kg'].fillna(fp_df['footprint_kgCO2e_per_kg'].mean()).to_numpy()
    else:
        arrays['FP'] = np.zeros(n)
    return arrays, n


def run_optimization(pop_size=150, n_gen=300):
    df = _load_dataset()
    protein_col, carb_col, fat_col, fiber_col, sodium_col, micros = _detect_columns(df)
    arrays, n = _prepare_arrays(df, protein_col, carb_col, fat_col, fiber_col, sodium_col, micros)

    targets_macro = np.array([2000, 50, 70, 310])  # cal, protein, fat, carbs
    target_fiber = 25
    target_sodium = 2300

    class ExtendedMealPlan(Problem):
        def __init__(self):
            super().__init__(n_var=n, n_obj=6, n_constr=0, xl=np.zeros(n), xu=np.full(n, 500))

        def _evaluate(self, X, out, *args, **kwargs):
            q = X / 100.0
            totals = np.column_stack([
                q @ arrays['CALS'],
                q @ arrays['PRO'],
                q @ arrays['FAT'],
                q @ arrays['CARB'],
            ])
            dev = np.abs(totals - targets_macro) / targets_macro
            f1 = dev.sum(axis=1)
            f2 = X.sum(axis=1)
            f3 = np.maximum(q @ arrays['SODIUM'] - target_sodium, 0) / target_sodium
            f4 = np.maximum(target_fiber - (q @ arrays['FIBER']), 0) / target_fiber
            f5 = (X / 1000) @ arrays['FP']

            micro_totals = np.column_stack([q @ arrays['MICRO'][k] for k in RDA.keys()])
            rdas = np.array(list(RDA.values()))
            completeness = micro_totals / rdas
            deficiency = np.maximum(1 - completeness, 0)
            f6 = deficiency.mean(axis=1)

            out['F'] = np.column_stack([f1, f2, f3, f4, f5, f6])

    problem = ExtendedMealPlan()
    algorithm = NSGA2(pop_size=pop_size)
    termination = get_termination('n_gen', n_gen)
    result = minimize(problem, algorithm, termination, seed=42, verbose=False)

    result.arrays = arrays
    return result
