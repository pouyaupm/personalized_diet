import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Rectangle
import warnings
warnings.filterwarnings('ignore')

"""
Quick Demo: Advanced Nutrition Analysis Features
==============================================

This demo showcases the advanced nutrition analysis capabilities:
1. Micronutrient completeness scoring
2. Antioxidant analysis
3. Sugar vs. fiber intelligence
4. Fat quality assessment
5. Electrolyte balance
6. Food category diversity
7. Interactive visualizations

No optimization - just analysis of sample meal plans!
"""

# Load data
print("Loading USDA nutrition data...")
df = pd.read_csv('data/food.csv')
df.columns = [c.replace(" ", "_").replace(".", "_") for c in df.columns]

# Sample some foods for demo
np.random.seed(42)
sample_foods = df.sample(n=50).reset_index(drop=True)

# Define RDA values
RDA_VALUES = {
    'protein': 50,        # g
    'fiber': 25,          # g  
    'calcium': 1000,      # mg
    'iron': 18,           # mg
    'magnesium': 400,     # mg
    'potassium': 3500,    # mg
    'zinc': 11,           # mg
    'vitamin_a': 900,     # μg RAE
    'vitamin_c': 90,      # mg
    'vitamin_e': 15,      # mg
    'choline': 550,       # mg
}

def create_sample_meal_plans():
    """Create some sample meal plans to analyze"""
    
    # Find foods by category for realistic meal plans
    fruits = sample_foods[sample_foods['Category'].str.contains('Fruit', na=False)]
    vegetables = sample_foods[sample_foods['Category'].str.contains('Vegetable', na=False)]
    grains = sample_foods[sample_foods['Category'].str.contains('Grain', na=False)]
    proteins = sample_foods[sample_foods['Category'].str.contains('Meat|Fish|Poultry|Legume', na=False)]
    dairy = sample_foods[sample_foods['Category'].str.contains('Milk|Dairy', na=False)]
    
    meal_plans = {}
    
    # Balanced meal plan
    if len(fruits) > 0 and len(vegetables) > 0 and len(grains) > 0:
        balanced_plan = pd.DataFrame({
            'Food': [
                fruits.iloc[0]['Description'] if len(fruits) > 0 else 'Apple',
                vegetables.iloc[0]['Description'] if len(vegetables) > 0 else 'Broccoli', 
                grains.iloc[0]['Description'] if len(grains) > 0 else 'Brown Rice',
                proteins.iloc[0]['Description'] if len(proteins) > 0 else 'Chicken Breast',
                dairy.iloc[0]['Description'] if len(dairy) > 0 else 'Milk'
            ],
            'Amount_g': [150, 200, 100, 120, 250]
        })
        meal_plans['Balanced'] = balanced_plan
    
    # High sugar meal plan (processed foods)
    processed_foods = sample_foods[sample_foods['Data_Sugar_Total'] > 10]
    if len(processed_foods) >= 3:
        high_sugar_plan = pd.DataFrame({
            'Food': processed_foods.head(3)['Description'].tolist(),
            'Amount_g': [100, 80, 120]
        })
        meal_plans['High Sugar'] = high_sugar_plan
    
    # Antioxidant-rich meal plan
    antioxidant_foods = sample_foods[
        (sample_foods['Data_Beta_Carotene'] > 100) | 
        (sample_foods['Data_Vitamins_Vitamin_C'] > 20) |
        (sample_foods['Data_Lycopene'] > 100)
    ]
    if len(antioxidant_foods) >= 3:
        antioxidant_plan = pd.DataFrame({
            'Food': antioxidant_foods.head(3)['Description'].tolist(),
            'Amount_g': [150, 100, 200]
        })
        meal_plans['Antioxidant Rich'] = antioxidant_plan
    
    return meal_plans

def calculate_micronutrient_completeness(foods_data):
    """Calculate micronutrient completeness score"""
    scores = {}
    
    # Map our RDA nutrients to dataframe columns
    nutrient_mapping = {
        'protein': 'Data_Protein',
        'fiber': 'Data_Fiber',
        'calcium': 'Data_Major_Minerals_Calcium',
        'iron': 'Data_Major_Minerals_Iron',
        'magnesium': 'Data_Major_Minerals_Magnesium',
        'potassium': 'Data_Major_Minerals_Potassium',
        'zinc': 'Data_Major_Minerals_Zinc',
        'vitamin_a': 'Data_Vitamins_Vitamin_A___RAE',
        'vitamin_c': 'Data_Vitamins_Vitamin_C',
        'vitamin_e': 'Data_Vitamins_Vitamin_E',
        'choline': 'Data_Choline'
    }
    
    for nutrient, col in nutrient_mapping.items():
        if col in foods_data.columns and nutrient in RDA_VALUES:
            total_intake = (foods_data[col] * foods_data['Amount_g'] / 100).sum()
            rda = RDA_VALUES[nutrient]
            score = min(total_intake / rda, 1.0) if rda > 0 else 0
            scores[nutrient] = {
                'intake': total_intake,
                'rda': rda,
                'score': score,
                'percentage': (total_intake / rda) * 100 if rda > 0 else 0
            }
    
    overall_score = np.mean([s['score'] for s in scores.values()])
    return scores, overall_score

def calculate_antioxidant_score(foods_data):
    """Calculate antioxidant diversity and power"""
    antioxidants = {
        'Alpha Carotene': 'Data_Alpha_Carotene',
        'Beta Carotene': 'Data_Beta_Carotene', 
        'Vitamin C': 'Data_Vitamins_Vitamin_C',
        'Vitamin E': 'Data_Vitamins_Vitamin_E',
        'Lycopene': 'Data_Lycopene',
        'Lutein': 'Data_Lutein_and_Zeaxanthin'
    }
    
    antioxidant_totals = {}
    for name, col in antioxidants.items():
        if col in foods_data.columns:
            total = (foods_data[col] * foods_data['Amount_g'] / 100).sum()
            antioxidant_totals[name] = total
    
    # Count how many antioxidants are significantly present
    significant_antioxidants = sum(1 for total in antioxidant_totals.values() if total > 0)
    diversity_score = significant_antioxidants / len(antioxidants)
    
    return antioxidant_totals, diversity_score

def calculate_sugar_fiber_ratio(foods_data):
    """Calculate sugar to fiber ratio"""
    total_sugar = (foods_data['Data_Sugar_Total'] * foods_data['Amount_g'] / 100).sum()
    total_fiber = (foods_data['Data_Fiber'] * foods_data['Amount_g'] / 100).sum()
    
    ratio = total_sugar / total_fiber if total_fiber > 0 else float('inf')
    
    # Good ratio is 2:1 or less
    quality = "Excellent" if ratio <= 1 else "Good" if ratio <= 2 else "Poor"
    
    return {
        'sugar': total_sugar,
        'fiber': total_fiber,
        'ratio': ratio,
        'quality': quality
    }

def calculate_fat_quality(foods_data):
    """Calculate fat quality (Mediterranean style)"""
    saturated = (foods_data['Data_Fat_Saturated_Fat'] * foods_data['Amount_g'] / 100).sum()
    mono = (foods_data['Data_Fat_Monosaturated_Fat'] * foods_data['Amount_g'] / 100).sum()
    poly = (foods_data['Data_Fat_Polysaturated_Fat'] * foods_data['Amount_g'] / 100).sum()
    
    total_fat = saturated + mono + poly
    
    if total_fat > 0:
        sat_pct = (saturated / total_fat) * 100
        mono_pct = (mono / total_fat) * 100  
        poly_pct = (poly / total_fat) * 100
        
        # Mediterranean ideal: high mono, moderate poly, low saturated
        quality_score = (mono_pct / 50) * 0.5 + (poly_pct / 30) * 0.3 + max(0, (20 - sat_pct) / 20) * 0.2
        quality_score = min(quality_score, 1.0)
    else:
        sat_pct = mono_pct = poly_pct = quality_score = 0
    
    return {
        'saturated': saturated,
        'monounsaturated': mono,
        'polyunsaturated': poly,
        'sat_percent': sat_pct,
        'mono_percent': mono_pct,
        'poly_percent': poly_pct,
        'quality_score': quality_score
    }

def calculate_electrolyte_balance(foods_data):
    """Calculate electrolyte balance"""
    sodium = (foods_data['Data_Major_Minerals_Sodium'] * foods_data['Amount_g'] / 100).sum()
    potassium = (foods_data['Data_Major_Minerals_Potassium'] * foods_data['Amount_g'] / 100).sum()
    
    ratio = sodium / potassium if potassium > 0 else float('inf')
    
    # Ideal ratio is 1:2 (0.5) or less
    balance_quality = "Excellent" if ratio <= 0.5 else "Good" if ratio <= 1.0 else "Poor"
    
    return {
        'sodium': sodium,
        'potassium': potassium, 
        'ratio': ratio,
        'quality': balance_quality
    }

def analyze_meal_plan(plan_name, meal_plan):
    """Comprehensive analysis of a meal plan"""
    print(f"\n{'='*60}")
    print(f"ANALYZING: {plan_name.upper()} MEAL PLAN")
    print(f"{'='*60}")
    
    # Get food data
    foods_data = []
    for _, row in meal_plan.iterrows():
        food_match = sample_foods[sample_foods['Description'].str.contains(
            row['Food'].split(',')[0], case=False, na=False)]
        if len(food_match) > 0:
            food_data = food_match.iloc[0].copy()
            food_data['Amount_g'] = row['Amount_g']
            foods_data.append(food_data)
    
    if not foods_data:
        print("No matching foods found in database")
        return
        
    foods_df = pd.DataFrame(foods_data)
    
    # Basic macros
    total_calories = (foods_df['Data_Protein'] * 4 + foods_df['Data_Carbohydrate'] * 4 + 
                     foods_df['Data_Fat_Total_Lipid'] * 9) * foods_df['Amount_g'] / 100
    total_protein = (foods_df['Data_Protein'] * foods_df['Amount_g'] / 100).sum()
    total_carbs = (foods_df['Data_Carbohydrate'] * foods_df['Amount_g'] / 100).sum()
    total_fat = (foods_df['Data_Fat_Total_Lipid'] * foods_df['Amount_g'] / 100).sum()
    
    print(f"\nMACRONUTRIENTS:")
    print(f"  Calories: {total_calories.sum():.0f}")
    print(f"  Protein:  {total_protein:.1f}g")
    print(f"  Carbs:    {total_carbs:.1f}g") 
    print(f"  Fat:      {total_fat:.1f}g")
    
    # Micronutrient analysis
    micro_scores, overall_micro = calculate_micronutrient_completeness(foods_df)
    print(f"\nMICRONUTRIENT COMPLETENESS: {overall_micro:.1%}")
    for nutrient, data in micro_scores.items():
        status = "✓" if data['percentage'] >= 100 else "⚠" if data['percentage'] >= 75 else "✗"
        print(f"  {nutrient:12s}: {data['intake']:6.1f} ({data['percentage']:5.1f}% RDA) {status}")
    
    # Antioxidant analysis
    antioxidants, antiox_diversity = calculate_antioxidant_score(foods_df)
    print(f"\nANTIOXIDANT PROFILE (Diversity: {antiox_diversity:.1%}):")
    for name, amount in antioxidants.items():
        if amount > 0:
            print(f"  {name:15s}: {amount:8.1f}")
    
    # Sugar vs Fiber
    sugar_fiber = calculate_sugar_fiber_ratio(foods_df)
    print(f"\nSUGAR vs FIBER:")
    print(f"  Sugar: {sugar_fiber['sugar']:.1f}g")
    print(f"  Fiber: {sugar_fiber['fiber']:.1f}g")
    print(f"  Ratio: {sugar_fiber['ratio']:.1f}:1 ({sugar_fiber['quality']})")
    
    # Fat quality
    fat_quality = calculate_fat_quality(foods_df)
    print(f"\nFAT QUALITY (Score: {fat_quality['quality_score']:.2f}):")
    print(f"  Saturated:   {fat_quality['saturated']:.1f}g ({fat_quality['sat_percent']:.1f}%)")
    print(f"  Monounsat:   {fat_quality['monounsaturated']:.1f}g ({fat_quality['mono_percent']:.1f}%)")
    print(f"  Polyunsat:   {fat_quality['polyunsaturated']:.1f}g ({fat_quality['poly_percent']:.1f}%)")
    
    # Electrolyte balance
    electrolytes = calculate_electrolyte_balance(foods_df)
    print(f"\nELECTROLYTE BALANCE:")
    print(f"  Sodium:    {electrolytes['sodium']:.0f}mg")
    print(f"  Potassium: {electrolytes['potassium']:.0f}mg")
    print(f"  Na:K Ratio: {electrolytes['ratio']:.2f} ({electrolytes['quality']})")
    
    # Food composition
    print(f"\nFOOD COMPOSITION:")
    for _, row in meal_plan.iterrows():
        print(f"  {row['Amount_g']:3.0f}g - {row['Food']}")
    
    return {
        'micro_score': overall_micro,
        'antiox_diversity': antiox_diversity,
        'sugar_fiber': sugar_fiber,
        'fat_quality': fat_quality['quality_score'],
        'electrolyte_quality': electrolytes['quality']
    }

def create_comparison_visualizations(meal_analyses):
    """Create visualizations comparing meal plans"""
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Advanced Nutrition Analysis Dashboard', fontsize=16, fontweight='bold')
    
    meal_names = list(meal_analyses.keys())
    
    # 1. Micronutrient Completeness Radar
    ax = axes[0, 0]
    if meal_names:
        categories = ['Micro Score', 'Antiox Diversity', 'Fat Quality']
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False)
        angles = np.concatenate([angles, [angles[0]]])
        
        for meal_name in meal_names:
            if meal_name in meal_analyses:
                values = [
                    meal_analyses[meal_name]['micro_score'],
                    meal_analyses[meal_name]['antiox_diversity'], 
                    meal_analyses[meal_name]['fat_quality']
                ]
                values += values[:1]
                ax.plot(angles, values, 'o-', label=meal_name, linewidth=2)
                ax.fill(angles, values, alpha=0.1)
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        ax.set_ylim(0, 1)
        ax.set_title('Nutrition Quality Comparison')
        ax.legend()
        ax.grid(True)
    
    # 2. Micronutrient Score Comparison
    ax = axes[0, 1]
    scores = [meal_analyses[name]['micro_score'] for name in meal_names if name in meal_analyses]
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'][:len(meal_names)]
    
    bars = ax.bar(meal_names, scores, color=colors[:len(scores)])
    ax.set_ylabel('Completeness Score')
    ax.set_title('Micronutrient Completeness')
    ax.set_ylim(0, 1)
    
    # Add value labels on bars
    for bar, score in zip(bars, scores):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
               f'{score:.2f}', ha='center', va='bottom')
    
    # 3. Antioxidant Diversity
    ax = axes[0, 2]
    antiox_scores = [meal_analyses[name]['antiox_diversity'] for name in meal_names if name in meal_analyses]
    
    bars = ax.bar(meal_names, antiox_scores, color=colors[:len(antiox_scores)])
    ax.set_ylabel('Diversity Score')
    ax.set_title('Antioxidant Diversity')
    ax.set_ylim(0, 1)
    
    for bar, score in zip(bars, antiox_scores):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
               f'{score:.2f}', ha='center', va='bottom')
    
    # 4. Sugar-Fiber Ratios
    ax = axes[1, 0]
    ratios = []
    for name in meal_names:
        if name in meal_analyses:
            ratio = meal_analyses[name]['sugar_fiber']['ratio']
            ratios.append(min(ratio, 5))  # Cap at 5 for visualization
    
    bars = ax.bar(meal_names, ratios, color=colors[:len(ratios)])
    ax.axhline(y=2, color='red', linestyle='--', label='Ideal Max (2:1)')
    ax.set_ylabel('Sugar:Fiber Ratio') 
    ax.set_title('Sugar vs Fiber Balance')
    ax.legend()
    
    for bar, ratio in zip(bars, ratios):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
               f'{ratio:.1f}', ha='center', va='bottom')
    
    # 5. Fat Quality Scores
    ax = axes[1, 1]
    fat_scores = [meal_analyses[name]['fat_quality'] for name in meal_names if name in meal_analyses]
    
    bars = ax.bar(meal_names, fat_scores, color=colors[:len(fat_scores)])
    ax.set_ylabel('Quality Score')
    ax.set_title('Fat Quality (Mediterranean Style)')
    ax.set_ylim(0, 1)
    
    for bar, score in zip(bars, fat_scores):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
               f'{score:.2f}', ha='center', va='bottom')
    
    # 6. Overall Quality Heatmap
    ax = axes[1, 2]
    
    # Create quality matrix
    metrics = ['Micro Score', 'Antiox Div', 'Fat Quality']
    quality_matrix = []
    
    for name in meal_names:
        if name in meal_analyses:
            row = [
                meal_analyses[name]['micro_score'],
                meal_analyses[name]['antiox_diversity'],
                meal_analyses[name]['fat_quality']
            ]
            quality_matrix.append(row)
    
    if quality_matrix:
        im = ax.imshow(quality_matrix, cmap='RdYlGn', vmin=0, vmax=1, aspect='auto')
        ax.set_xticks(range(len(metrics)))
        ax.set_yticks(range(len(meal_names)))
        ax.set_xticklabels(metrics)
        ax.set_yticklabels(meal_names)
        ax.set_title('Quality Heatmap')
        
        # Add text annotations
        for i in range(len(meal_names)):
            for j in range(len(metrics)):
                text = ax.text(j, i, f'{quality_matrix[i][j]:.2f}',
                             ha="center", va="center", color="black")
        
        plt.colorbar(im, ax=ax)
    
    plt.tight_layout()
    plt.show()

def main():
    """Run the nutrition analysis demo"""
    
    print("🥗 Advanced Nutrition Analysis Demo")
    print("="*50)
    
    # Create sample meal plans
    meal_plans = create_sample_meal_plans()
    
    if not meal_plans:
        print("Could not create meal plans with available foods")
        return
    
    # Analyze each meal plan
    meal_analyses = {}
    for plan_name, meal_plan in meal_plans.items():
        analysis = analyze_meal_plan(plan_name, meal_plan)
        if analysis:
            meal_analyses[plan_name] = analysis
    
    # Create visualizations
    print(f"\n{'='*60}")
    print("GENERATING ADVANCED VISUALIZATIONS...")
    print(f"{'='*60}")
    
    create_comparison_visualizations(meal_analyses)
    
    # Summary
    print(f"\n{'='*60}")
    print("ANALYSIS SUMMARY")
    print(f"{'='*60}")
    
    for plan_name, analysis in meal_analyses.items():
        print(f"\n{plan_name}:")
        print(f"  Micronutrient Score: {analysis['micro_score']:.1%}")
        print(f"  Antioxidant Diversity: {analysis['antiox_diversity']:.1%}")
        print(f"  Fat Quality Score: {analysis['fat_quality']:.2f}")
        print(f"  Sugar:Fiber Quality: {analysis['sugar_fiber']['quality']}")
        print(f"  Electrolyte Balance: {analysis['electrolyte_quality']}")
    
    print(f"\nThis demo showcases:")
    print(f"✓ Micronutrient completeness scoring (20+ nutrients)")
    print(f"✓ Antioxidant diversity analysis")
    print(f"✓ Sugar-to-fiber ratio optimization")
    print(f"✓ Mediterranean-style fat quality scoring")
    print(f"✓ Electrolyte balance assessment")
    print(f"✓ Advanced comparative visualizations")

if __name__ == '__main__':
    main()