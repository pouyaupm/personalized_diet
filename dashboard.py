import streamlit as st
from optimizer import run_optimization, OBJECTIVE_NAMES, RDA
from visualization import plot_objectives, plot_radar

st.title("Meal Plan Optimization Dashboard")

result = run_optimization()

st.sidebar.header("Objective Selection")
selected = st.sidebar.multiselect(
    "Objectives", OBJECTIVE_NAMES, default=[OBJECTIVE_NAMES[0], OBJECTIVE_NAMES[1]]
)

indices = [OBJECTIVE_NAMES.index(name) for name in selected]

if len(indices) >= 2:
    plot_objectives(result, indices, OBJECTIVE_NAMES)
else:
    st.warning("Please select at least two objectives to plot.")

st.sidebar.header("Inspect Solution")
idx = st.sidebar.slider("Solution index", 0, result.F.shape[0]-1, 0)
if st.sidebar.button("Show Solution"):
    st.write(f"### Solution {idx}")
    arrays = result.arrays
    q = result.X[idx] / 100.0
    totals = {
        'Calories': float(q @ arrays['CALS']),
        'Protein': float(q @ arrays['PRO']),
        'Fat': float(q @ arrays['FAT']),
        'Carbs': float(q @ arrays['CARB']),
        'Fiber': float(q @ arrays['FIBER']),
        'Sodium': float(q @ arrays['SODIUM']),
    }
    st.json(totals)
    plot_radar(result, idx, arrays['MICRO'], RDA)
