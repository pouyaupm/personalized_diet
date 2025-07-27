import os
import urllib.request
import pandas as pd
import numpy as np
from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.termination import get_termination
from pymoo.optimize import minimize
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Rectangle
import warnings
warnings.filterwarnings('ignore')

"""
Advanced Micronutrient Optimization System
==========================================

Features:
1. Micronutrient Completeness Score (15+ nutrients)
2. Antioxidant Power Optimization
3. Sugar vs. Fiber Intelligence
4. Fat Quality Optimization
5. Electrolyte Balance Optimization
6. Food Category Diversity
7. Water Content Strategy
8. Choline Brain Health
9. Advanced Visualizations

Objectives:
1. Minimize macro deviation
2. Maximize micronutrient completeness score
3. Maximize antioxidant diversity score
4. Optimize sugar-to-fiber ratio
5. Optimize fat quality ratio
6. Optimize electrolyte balance
7. Maximize food category diversity
8. Minimize total weight
"""

# Setup and data loading
DATA_DIR = "data"
FOODS_CSV = os.path.join(DATA_DIR, "food.csv")
USDA_URL = "https://corgis-edu.github.io/corgis/datasets/csv/food/food.csv"

os.makedirs(DATA_DIR, exist_ok=True)
if not os.path.exists(FOODS_CSV):
    print("Downloading USDA data...")
    urllib.request.urlretrieve(USDA_URL, FOODS_CSV)

# Load and clean data
df = pd.read_csv(FOODS_CSV)
df.columns = [c.replace(" ", "_").replace(".", "_") for c in df.columns]

# Define comprehensive nutrient mapping
NUTRIENT_MAPPING = {
    # Macronutrients
    'protein': 'Data_Protein',
    'carbs': 'Data_Carbohydrate', 
    'fat': 'Data_Fat_Total_Lipid',
    'fiber': 'Data_Fiber',
    'sugar': 'Data_Sugar_Total',
    'water': 'Data_Water',
    'cholesterol': 'Data_Cholesterol',
    'choline': 'Data_Choline',
    
    # Fat types
    'saturated_fat': 'Data_Fat_Saturated_Fat',
    'monounsaturated_fat': 'Data_Fat_Monosaturated_Fat',
    'polyunsaturated_fat': 'Data_Fat_Polysaturated_Fat',
    
    # Major minerals
    'calcium': 'Data_Major_Minerals_Calcium',
    'iron': 'Data_Major_Minerals_Iron',
    'magnesium': 'Data_Major_Minerals_Magnesium',
    'phosphorus': 'Data_Major_Minerals_Phosphorus',
    'potassium': 'Data_Major_Minerals_Potassium',
    'sodium': 'Data_Major_Minerals_Sodium',
    'zinc': 'Data_Major_Minerals_Zinc',
    'copper': 'Data_Major_Minerals_Copper',
    'selenium': 'Data_Selenium',
    
    # Vitamins
    'vitamin_a': 'Data_Vitamins_Vitamin_A___RAE',
    'vitamin_b6': 'Data_Vitamins_Vitamin_B6',
    'vitamin_b12': 'Data_Vitamins_Vitamin_B12',
    'vitamin_c': 'Data_Vitamins_Vitamin_C',
    'vitamin_e': 'Data_Vitamins_Vitamin_E',
    'vitamin_k': 'Data_Vitamins_Vitamin_K',
    'thiamin': 'Data_Thiamin',
    'riboflavin': 'Data_Riboflavin',
    'niacin': 'Data_Niacin',
    'retinol': 'Data_Retinol',
    
    # Antioxidants
    'alpha_carotene': 'Data_Alpha_Carotene',
    'beta_carotene': 'Data_Beta_Carotene',
    'beta_cryptoxanthin': 'Data_Beta_Cryptoxanthin',
    'lutein_zeaxanthin': 'Data_Lutein_and_Zeaxanthin',
    'lycopene': 'Data_Lycopene'
}

# RDA values (per day) for adults
RDA_VALUES = {
    'protein': 50,        # g
    'fiber': 25,          # g
    'calcium': 1000,      # mg
    'iron': 18,           # mg
    'magnesium': 400,     # mg
    'phosphorus': 700,    # mg
    'potassium': 3500,    # mg
    'zinc': 11,           # mg
    'copper': 0.9,        # mg
    'selenium': 55,       # μg
    'vitamin_a': 900,     # μg RAE
    'vitamin_b6': 1.3,    # mg
    'vitamin_b12': 2.4,   # μg
    'vitamin_c': 90,      # mg
    'vitamin_e': 15,      # mg
    'vitamin_k': 120,     # μg
    'thiamin': 1.2,       # mg
    'riboflavin': 1.3,    # mg
    'niacin': 16,         # mg
    'choline': 550,       # mg
}

# Clean and prepare data
required_cols = [NUTRIENT_MAPPING[k] for k in ['protein', 'carbs', 'fat'] if NUTRIENT_MAPPING[k] in df.columns]
df_clean = df.dropna(subset=required_cols)

# Fill missing values with 0 for optional nutrients
for nutrient, col in NUTRIENT_MAPPING.items():
    if col not in df_clean.columns:
        df_clean[col] = 0
        print(f"Warning: {col} not found, using zeros")
    else:
        df_clean[col] = df_clean[col].fillna(0)

# Calculate calories
df_clean['calories'] = (
    4 * df_clean[NUTRIENT_MAPPING['protein']] +
    4 * df_clean[NUTRIENT_MAPPING['carbs']] +
    9 * df_clean[NUTRIENT_MAPPING['fat']]
)

# Sample for performance
MAX_FOODS = 300
df_sample = df_clean.sample(n=min(len(df_clean), MAX_FOODS), random_state=42).reset_index(drop=True)
N = len(df_sample)

# Extract nutrient arrays
nutrient_arrays = {}
for nutrient, col in NUTRIENT_MAPPING.items():
    nutrient_arrays[nutrient] = df_sample[col].to_numpy()

# Get food categories and descriptions
categories = df_sample['Category'].to_list()
descriptions = df_sample['Description'].to_list()
unique_categories = list(set(categories))
category_indices = {cat: i for i, cat in enumerate(unique_categories)}

# Daily targets
MACRO_TARGETS = np.array([2000, 50, 70, 310])  # calories, protein, fat, carbs
SODIUM_LIMIT = 2300  # mg
SUGAR_LIMIT = 50     # g

class AdvancedNutritionProblem(Problem):
    def __init__(self):
        super().__init__(n_var=N, n_obj=8, n_constr=0,
                         xl=np.zeros(N), xu=np.full(N, 500))
        
    def calculate_micronutrient_completeness(self, quantities):
        """Calculate completeness score for micronutrients"""
        q = quantities / 100.0
        scores = []
        
        for nutrient in RDA_VALUES:
            if nutrient in nutrient_arrays:
                intake = q @ nutrient_arrays[nutrient]
                rda = RDA_VALUES[nutrient]
                # Score is min(intake/RDA, 1.0) to avoid over-supplementation rewards
                score = min(intake / rda, 1.0) if rda > 0 else 0
                scores.append(score)
        
        return np.mean(scores) if scores else 0
    
    def calculate_antioxidant_score(self, quantities):
        """Calculate antioxidant diversity and power score"""
        q = quantities / 100.0
        antioxidants = ['alpha_carotene', 'beta_carotene', 'beta_cryptoxanthin', 
                       'lutein_zeaxanthin', 'lycopene', 'vitamin_c', 'vitamin_e', 'selenium']
        
        scores = []
        for antioxidant in antioxidants:
            if antioxidant in nutrient_arrays:
                intake = q @ nutrient_arrays[antioxidant]
                # Normalize by percentile to handle different units
                if intake > 0:
                    scores.append(min(intake / np.percentile(nutrient_arrays[antioxidant], 75), 1.0))
        
        diversity_bonus = len([s for s in scores if s > 0.1]) / len(antioxidants)
        return (np.mean(scores) if scores else 0) * (1 + diversity_bonus)
    
    def calculate_sugar_fiber_ratio(self, quantities):
        """Optimize sugar-to-fiber ratio"""
        q = quantities / 100.0
        total_sugar = q @ nutrient_arrays['sugar']
        total_fiber = q @ nutrient_arrays['fiber']
        
        # Penalize high sugar unless proportional fiber
        if total_fiber > 0:
            ratio = total_sugar / total_fiber
            # Good ratio is 2:1 or less (sugar:fiber)
            penalty = max(0, ratio - 2) / 10
        else:
            penalty = total_sugar / 50  # Raw sugar penalty if no fiber
        
        return penalty
    
    def calculate_fat_quality_score(self, quantities):
        """Calculate Mediterranean-style fat quality score"""
        q = quantities / 100.0
        saturated = q @ nutrient_arrays['saturated_fat']
        mono = q @ nutrient_arrays['monounsaturated_fat']
        poly = q @ nutrient_arrays['polyunsaturated_fat']
        
        total_fat = saturated + mono + poly
        if total_fat > 0:
            # Mediterranean ratio: high mono, moderate poly, low saturated
            mono_ratio = mono / total_fat
            poly_ratio = poly / total_fat
            sat_ratio = saturated / total_fat
            
            # Ideal: 50% mono, 30% poly, 20% saturated
            score = (
                min(mono_ratio / 0.5, 1.0) * 0.5 +
                min(poly_ratio / 0.3, 1.0) * 0.3 +
                max(0, 1 - sat_ratio / 0.2) * 0.2
            )
            return score
        return 0
    
    def calculate_electrolyte_balance(self, quantities):
        """Calculate electrolyte balance score (sodium:potassium ratio)"""
        q = quantities / 100.0
        sodium = q @ nutrient_arrays['sodium']
        potassium = q @ nutrient_arrays['potassium']
        
        if potassium > 0:
            # Ideal sodium:potassium ratio is 1:2 or less
            ratio = sodium / potassium
            penalty = max(0, ratio - 0.5) * 2  # Penalty for ratios > 1:2
        else:
            penalty = sodium / SODIUM_LIMIT
        
        return penalty
    
    def calculate_category_diversity(self, quantities):
        """Calculate food category diversity score"""
        # Count how many categories are represented with >10g
        category_counts = {}
        for i, cat in enumerate(categories):
            if quantities[i] > 10:  # Only count significant amounts
                category_counts[cat] = category_counts.get(cat, 0) + quantities[i]
        
        # Diversity score based on Shannon entropy
        total_weight = sum(category_counts.values())
        if total_weight > 0:
            proportions = [w/total_weight for w in category_counts.values()]
            entropy = -sum(p * np.log(p) for p in proportions if p > 0)
            max_entropy = np.log(len(unique_categories))
            return entropy / max_entropy if max_entropy > 0 else 0
        return 0
    
    def calculate_hydration_score(self, quantities):
        """Calculate hydration from food water content"""
        q = quantities / 100.0
        total_water = q @ nutrient_arrays['water']
        # Target: 500ml from food (rest from drinking)
        return min(total_water / 500, 1.0)

    def _evaluate(self, X, out, *args, **kwargs):
        batch_size = X.shape[0]
        objectives = np.zeros((batch_size, 8))
        
        for i in range(batch_size):
            quantities = X[i]
            q = quantities / 100.0
            
            # Calculate totals
            totals = np.array([
                q @ nutrient_arrays['protein'] * 4 + q @ nutrient_arrays['carbs'] * 4 + q @ nutrient_arrays['fat'] * 9,  # calories
                q @ nutrient_arrays['protein'],
                q @ nutrient_arrays['fat'],
                q @ nutrient_arrays['carbs']
            ])
            
            # Objective 1: Macro deviation (minimize)
            macro_dev = np.sum(np.abs(totals - MACRO_TARGETS) / MACRO_TARGETS)
            objectives[i, 0] = macro_dev
            
            # Objective 2: Micronutrient completeness (maximize -> minimize negative)
            micronutrient_score = self.calculate_micronutrient_completeness(quantities)
            objectives[i, 1] = -micronutrient_score
            
            # Objective 3: Antioxidant score (maximize -> minimize negative)
            antioxidant_score = self.calculate_antioxidant_score(quantities)
            objectives[i, 2] = -antioxidant_score
            
            # Objective 4: Sugar-fiber ratio penalty (minimize)
            sugar_fiber_penalty = self.calculate_sugar_fiber_ratio(quantities)
            objectives[i, 3] = sugar_fiber_penalty
            
            # Objective 5: Fat quality (maximize -> minimize negative)
            fat_quality = self.calculate_fat_quality_score(quantities)
            objectives[i, 4] = -fat_quality
            
            # Objective 6: Electrolyte balance penalty (minimize)
            electrolyte_penalty = self.calculate_electrolyte_balance(quantities)
            objectives[i, 5] = electrolyte_penalty
            
            # Objective 7: Category diversity (maximize -> minimize negative)
            diversity_score = self.calculate_category_diversity(quantities)
            objectives[i, 6] = -diversity_score
            
            # Objective 8: Total weight (minimize)
            total_weight = np.sum(quantities)
            objectives[i, 7] = total_weight / 1000  # Scale to kg
        
        out['F'] = objectives

def analyze_solution(solution_idx, X, F):
    """Analyze a specific solution in detail"""
    quantities = X[solution_idx]
    q = quantities / 100.0
    
    print(f"\n=== SOLUTION {solution_idx + 1} ANALYSIS ===")
    
    # Macronutrients
    calories = q @ nutrient_arrays['protein'] * 4 + q @ nutrient_arrays['carbs'] * 4 + q @ nutrient_arrays['fat'] * 9
    protein = q @ nutrient_arrays['protein']
    fat = q @ nutrient_arrays['fat']
    carbs = q @ nutrient_arrays['carbs']
    
    print(f"Macronutrients:")
    print(f"  Calories: {calories:.0f} (target: 2000)")
    print(f"  Protein:  {protein:.1f}g (target: 50g)")
    print(f"  Fat:      {fat:.1f}g (target: 70g)")
    print(f"  Carbs:    {carbs:.1f}g (target: 310g)")
    
    # Micronutrients analysis
    print(f"\nMicronutrient Completeness:")
    for nutrient in sorted(RDA_VALUES.keys()):
        if nutrient in nutrient_arrays:
            intake = q @ nutrient_arrays[nutrient]
            rda = RDA_VALUES[nutrient]
            percentage = (intake / rda) * 100 if rda > 0 else 0
            status = "✓" if percentage >= 100 else "⚠" if percentage >= 75 else "✗"
            print(f"  {nutrient:15s}: {intake:6.1f} ({percentage:5.1f}% RDA) {status}")
    
    # Food breakdown
    print(f"\nFood Composition (>10g):")
    food_data = [(quantities[i], descriptions[i], categories[i]) for i in range(len(quantities)) if quantities[i] > 10]
    food_data.sort(reverse=True)
    
    for amount, desc, cat in food_data[:15]:
        print(f"  {amount:3.0f}g - {desc[:40]:40s} [{cat}]")
    
    print(f"\nObjective Scores:")
    print(f"  Macro deviation:      {F[solution_idx, 0]:.3f}")
    print(f"  Micronutrient score:  {-F[solution_idx, 1]:.3f}")
    print(f"  Antioxidant score:    {-F[solution_idx, 2]:.3f}")
    print(f"  Sugar/fiber penalty:  {F[solution_idx, 3]:.3f}")
    print(f"  Fat quality score:    {-F[solution_idx, 4]:.3f}")
    print(f"  Electrolyte penalty:  {F[solution_idx, 5]:.3f}")
    print(f"  Diversity score:      {-F[solution_idx, 6]:.3f}")
    print(f"  Total weight:         {F[solution_idx, 7]:.1f} kg")

def create_advanced_visualizations(X, F):
    """Create comprehensive visualization dashboard"""
    fig = plt.figure(figsize=(20, 16))
    
    # 1. Pareto Front 3D: Nutrition vs Antioxidants vs Diversity
    ax1 = fig.add_subplot(3, 4, 1, projection='3d')
    scatter = ax1.scatter(-F[:, 1], -F[:, 2], -F[:, 6], 
                         c=F[:, 0], cmap='viridis', alpha=0.6)
    ax1.set_xlabel('Micronutrient Score')
    ax1.set_ylabel('Antioxidant Score')
    ax1.set_zlabel('Diversity Score')
    ax1.set_title('3D Pareto Front\n(color = macro deviation)')
    plt.colorbar(scatter, ax=ax1, shrink=0.5)
    
    # 2. Micronutrient Radar Chart for best solution
    ax2 = fig.add_subplot(3, 4, 2, projection='polar')
    best_idx = np.argmax(-F[:, 1])  # Best micronutrient score
    q_best = X[best_idx] / 100.0
    
    nutrients = list(RDA_VALUES.keys())[:8]  # Top 8 for visibility
    values = []
    for nutrient in nutrients:
        if nutrient in nutrient_arrays:
            intake = q_best @ nutrient_arrays[nutrient]
            rda = RDA_VALUES[nutrient]
            values.append(min(intake / rda, 2.0))  # Cap at 200%
        else:
            values.append(0)
    
    angles = np.linspace(0, 2 * np.pi, len(nutrients), endpoint=False)
    values += values[:1]  # Close the circle
    angles = np.concatenate([angles, [angles[0]]])
    
    ax2.plot(angles, values, 'o-', linewidth=2, color='red')
    ax2.fill(angles, values, alpha=0.25, color='red')
    ax2.set_xticks(angles[:-1])
    ax2.set_xticklabels([n.replace('_', ' ').title() for n in nutrients])
    ax2.set_ylim(0, 2)
    ax2.set_title('Micronutrient Profile\n(Best Solution)')
    ax2.grid(True)
    
    # 3. Fat Quality Distribution
    ax3 = fig.add_subplot(3, 4, 3)
    fat_scores = -F[:, 4]
    ax3.hist(fat_scores, bins=20, alpha=0.7, color='orange', edgecolor='black')
    ax3.set_xlabel('Fat Quality Score')
    ax3.set_ylabel('Frequency')
    ax3.set_title('Fat Quality Score Distribution')
    ax3.grid(True, alpha=0.3)
    
    # 4. Sugar vs Fiber Scatter
    ax4 = fig.add_subplot(3, 4, 4)
    sugar_totals = []
    fiber_totals = []
    for i in range(len(X)):
        q = X[i] / 100.0
        sugar_totals.append(q @ nutrient_arrays['sugar'])
        fiber_totals.append(q @ nutrient_arrays['fiber'])
    
    scatter = ax4.scatter(fiber_totals, sugar_totals, c=F[:, 3], cmap='RdYlBu_r', alpha=0.6)
    ax4.set_xlabel('Fiber (g)')
    ax4.set_ylabel('Sugar (g)')
    ax4.set_title('Sugar vs Fiber\n(color = penalty)')
    ax4.plot([0, 50], [0, 100], 'r--', alpha=0.5, label='2:1 ratio')
    ax4.legend()
    plt.colorbar(scatter, ax=ax4)
    
    # 5. Electrolyte Balance
    ax5 = fig.add_subplot(3, 4, 5)
    sodium_totals = []
    potassium_totals = []
    for i in range(len(X)):
        q = X[i] / 100.0
        sodium_totals.append(q @ nutrient_arrays['sodium'])
        potassium_totals.append(q @ nutrient_arrays['potassium'])
    
    ratios = [s/p if p > 0 else 0 for s, p in zip(sodium_totals, potassium_totals)]
    ax5.hist(ratios, bins=20, alpha=0.7, color='purple', edgecolor='black')
    ax5.axvline(x=0.5, color='red', linestyle='--', label='Ideal ratio (1:2)')
    ax5.set_xlabel('Sodium:Potassium Ratio')
    ax5.set_ylabel('Frequency')
    ax5.set_title('Electrolyte Balance Distribution')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    # 6. Category Diversity
    ax6 = fig.add_subplot(3, 4, 6)
    diversity_scores = -F[:, 6]
    ax6.hist(diversity_scores, bins=20, alpha=0.7, color='green', edgecolor='black')
    ax6.set_xlabel('Diversity Score')
    ax6.set_ylabel('Frequency')
    ax6.set_title('Food Category Diversity')
    ax6.grid(True, alpha=0.3)
    
    # 7. Objective Correlations Heatmap
    ax7 = fig.add_subplot(3, 4, 7)
    obj_labels = ['Macro Dev', 'Micro Score', 'Antioxidant', 'Sugar/Fiber', 
                  'Fat Quality', 'Electrolyte', 'Diversity', 'Weight']
    corr_matrix = np.corrcoef(F.T)
    im = ax7.imshow(corr_matrix, cmap='RdBu_r', vmin=-1, vmax=1)
    ax7.set_xticks(range(len(obj_labels)))
    ax7.set_yticks(range(len(obj_labels)))
    ax7.set_xticklabels(obj_labels, rotation=45, ha='right')
    ax7.set_yticklabels(obj_labels)
    ax7.set_title('Objective Correlations')
    
    # Add correlation values
    for i in range(len(obj_labels)):
        for j in range(len(obj_labels)):
            text = ax7.text(j, i, f'{corr_matrix[i, j]:.2f}',
                           ha="center", va="center", color="black" if abs(corr_matrix[i, j]) < 0.5 else "white")
    
    plt.colorbar(im, ax=ax7)
    
    # 8. Antioxidant Breakdown for best solution
    ax8 = fig.add_subplot(3, 4, 8)
    antioxidants = ['alpha_carotene', 'beta_carotene', 'vitamin_c', 'vitamin_e', 'lycopene']
    antioxidant_values = []
    best_antioxidant_idx = np.argmax(-F[:, 2])
    q_best_antiox = X[best_antioxidant_idx] / 100.0
    
    for antioxidant in antioxidants:
        if antioxidant in nutrient_arrays:
            value = q_best_antiox @ nutrient_arrays[antioxidant]
            antioxidant_values.append(value)
        else:
            antioxidant_values.append(0)
    
    bars = ax8.bar([a.replace('_', ' ').title() for a in antioxidants], antioxidant_values, color='coral')
    ax8.set_ylabel('Amount')
    ax8.set_title('Antioxidant Profile\n(Best Antioxidant Solution)')
    ax8.tick_params(axis='x', rotation=45)
    
    # 9. Weight vs Quality Trade-off
    ax9 = fig.add_subplot(3, 4, 9)
    quality_score = -F[:, 1] + -F[:, 2] + -F[:, 4] + -F[:, 6]  # Combined quality
    weights = F[:, 7]
    scatter = ax9.scatter(weights, quality_score, c=F[:, 0], cmap='viridis', alpha=0.6)
    ax9.set_xlabel('Total Weight (kg)')
    ax9.set_ylabel('Combined Quality Score')
    ax9.set_title('Weight vs Quality Trade-off')
    plt.colorbar(scatter, ax=ax9)
    
    # 10. Top Foods by Category
    ax10 = fig.add_subplot(3, 4, 10)
    best_overall_idx = np.argmin(F[:, 0])  # Best macro fit
    quantities_best = X[best_overall_idx]
    
    category_weights = {}
    for i, cat in enumerate(categories):
        if quantities_best[i] > 5:  # Only significant amounts
            category_weights[cat] = category_weights.get(cat, 0) + quantities_best[i]
    
    if category_weights:
        cats, weights = zip(*sorted(category_weights.items(), key=lambda x: x[1], reverse=True)[:8])
        bars = ax10.barh(range(len(cats)), weights, color='skyblue')
        ax10.set_yticks(range(len(cats)))
        ax10.set_yticklabels(cats)
        ax10.set_xlabel('Weight (g)')
        ax10.set_title('Food Categories\n(Best Overall Solution)')
    
    # 11. Nutrient Density Plot
    ax11 = fig.add_subplot(3, 4, 11)
    # Calculate nutrient density (micronutrients per calorie)
    densities = []
    calories_per_solution = []
    for i in range(len(X)):
        q = X[i] / 100.0
        cals = q @ nutrient_arrays['protein'] * 4 + q @ nutrient_arrays['carbs'] * 4 + q @ nutrient_arrays['fat'] * 9
        calories_per_solution.append(cals)
        if cals > 0:
            density = -F[i, 1] / (cals / 1000)  # Micronutrient score per 1000 calories
            densities.append(density)
        else:
            densities.append(0)
    
    ax11.scatter(calories_per_solution, densities, c=F[:, 0], cmap='viridis', alpha=0.6)
    ax11.set_xlabel('Total Calories')
    ax11.set_ylabel('Nutrient Density\n(per 1000 cal)')
    ax11.set_title('Nutrient Density vs Calories')
    
    # 12. Solution Rankings
    ax12 = fig.add_subplot(3, 4, 12)
    # Rank solutions by different criteria
    criteria = ['Micro Score', 'Antioxidant', 'Fat Quality', 'Diversity']
    rankings = np.zeros((len(X), len(criteria)))
    
    for i, (obj_idx, name) in enumerate([(1, 'Micro Score'), (2, 'Antioxidant'), 
                                        (4, 'Fat Quality'), (6, 'Diversity')]):
        rankings[:, i] = np.argsort(np.argsort(-F[:, obj_idx]))  # Rank (higher is better)
    
    # Show top 10 solutions
    top_indices = np.argsort(np.mean(rankings, axis=1))[:10]
    im = ax12.imshow(rankings[top_indices].T, cmap='RdYlGn_r', aspect='auto')
    ax12.set_xticks(range(len(top_indices)))
    ax12.set_xticklabels([f'Sol {i+1}' for i in top_indices])
    ax12.set_yticks(range(len(criteria)))
    ax12.set_yticklabels(criteria)
    ax12.set_title('Solution Rankings\n(Top 10 Overall)')
    plt.colorbar(im, ax=ax12)
    
    plt.tight_layout()
    plt.show()

# Run optimization
if __name__ == '__main__':
    print("Starting Advanced Nutrition Optimization...")
    print(f"Loaded {N} foods with {len(NUTRIENT_MAPPING)} nutrients")
    print(f"Tracking {len(RDA_VALUES)} micronutrients for completeness scoring")
    
    problem = AdvancedNutritionProblem()
    algorithm = NSGA2(pop_size=200)
    termination = get_termination('n_gen', 500)
    
    result = minimize(problem, algorithm, termination, seed=42, verbose=True)
    
    print(f"\nOptimization completed!")
    print(f"Found {result.X.shape[0]} Pareto-optimal solutions")
    
    # Analyze top solutions
    best_indices = [
        np.argmin(result.F[:, 0]),   # Best macro fit
        np.argmax(-result.F[:, 1]),  # Best micronutrient
        np.argmax(-result.F[:, 2]),  # Best antioxidant
        np.argmax(-result.F[:, 4]),  # Best fat quality
        np.argmax(-result.F[:, 6]),  # Best diversity
    ]
    
    solution_names = ['Best Macro', 'Best Micronutrient', 'Best Antioxidant', 
                     'Best Fat Quality', 'Best Diversity']
    
    for name, idx in zip(solution_names, best_indices):
        print(f"\n{'='*50}")
        print(f"{name.upper()} SOLUTION")
        analyze_solution(idx, result.X, result.F)
    
    # Create visualizations
    print("\nGenerating advanced visualizations...")
    create_advanced_visualizations(result.X, result.F)
    
    print("\n" + "="*60)
    print("OPTIMIZATION SUMMARY")
    print("="*60)
    print(f"Total solutions: {len(result.X)}")
    print(f"Best micronutrient completeness: {-np.min(result.F[:, 1]):.3f}")
    print(f"Best antioxidant score: {-np.min(result.F[:, 2]):.3f}")
    print(f"Best fat quality score: {-np.min(result.F[:, 4]):.3f}")
    print(f"Best diversity score: {-np.min(result.F[:, 6]):.3f}")
    print(f"Average macro deviation: {np.mean(result.F[:, 0]):.3f}")
    print("="*60)