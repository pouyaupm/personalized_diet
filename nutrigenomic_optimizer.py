import numpy as np
import pandas as pd
from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.termination import get_termination
from pymoo.optimize import minimize
from typing import Dict, List, Any, Optional
import json

class NutrigenomicNutritionProblem(Problem):
    """Enhanced nutrition optimization problem with genotype-aware adjustments"""
    
    def __init__(self, food_data: pd.DataFrame, macro_targets: Dict[str, float], 
                 genotype_adjustments: Optional[Dict[str, Any]] = None):
        """
        Initialize the nutrigenomic nutrition optimization problem
        
        Args:
            food_data: DataFrame with food nutrients
            macro_targets: Target calories, protein, fat, carbs
            genotype_adjustments: Genotype-based nutrition adjustments
        """
        self.food_data = food_data
        self.macro_targets = macro_targets
        self.genotype_adjustments = genotype_adjustments or self._get_default_adjustments()
        
        # Extract nutrient arrays
        self.nutrient_arrays = self._extract_nutrients()
        
        # Number of foods
        self.n_foods = len(food_data)
        
        # Define problem dimensions
        n_objectives = 8  # 8 objectives as in original
        n_variables = self.n_foods
        
        # Variable bounds (food quantities in grams)
        xl = np.zeros(n_variables)  # Minimum 0g of each food
        xu = np.ones(n_variables) * 1000  # Maximum 1000g of each food
        
        super().__init__(
            n_var=n_variables,
            n_obj=n_objectives,
            n_constr=0,
            xl=xl,
            xu=xu,
            type_var=np.double
        )
        
        # RDA values for micronutrients
        self.RDA_VALUES = {
            'protein': 50, 'fiber': 25, 'calcium': 1000, 'iron': 18, 'magnesium': 400,
            'potassium': 3500, 'zinc': 11, 'vitamin_a': 900, 'vitamin_c': 90,
            'vitamin_e': 15, 'choline': 550
        }
        
        # Apply genotype adjustments to RDA values
        self._apply_genotype_adjustments()
    
    def _get_default_adjustments(self) -> Dict[str, Any]:
        """Default genotype adjustments (wild-type)"""
        return {
            "vitamin_a_conversion_factor": 12,  # default WT
            "sat_fat_penalty_multiplier": 1.0,
            "epa_dha_min_mg": 0,
            "fiber_target_bonus_g": 0,
            "added_sugar_max_delta_g": 0,
            "applied_rules": []
        }
    
    def _extract_nutrients(self) -> Dict[str, np.ndarray]:
        """Extract nutrient arrays from food data"""
        nutrients = {}
        
        # Map food data columns to nutrient names
        column_mapping = {
            'Data.Protein': 'protein',
            'Data.Carbohydrate': 'carbs',
            'Data.Fat.Total Lipid': 'fat',
            'Data.Fiber': 'fiber',
            'Data.Sugar Total': 'sugar',
            'Data.Major Minerals.Sodium': 'sodium',
            'Data.Major Minerals.Potassium': 'potassium',
            'Data.Major Minerals.Calcium': 'calcium',
            'Data.Major Minerals.Iron': 'iron',
            'Data.Alpha Carotene': 'alpha_carotene',
            'Data.Beta Carotene': 'beta_carotene',
            'Data.Vitamins.Vitamin E': 'vitamin_e',
            'Data.Lycopene': 'lycopene',
            'Data.Fat.Saturated Fat': 'saturated_fat',
            'Data.Fat.Monosaturated Fat': 'monounsaturated_fat',
            'Data.Fat.Polysaturated Fat': 'polyunsaturated_fat',
            'Data.Major Minerals.Magnesium': 'magnesium',
            'Data.Major Minerals.Phosphorus': 'phosphorus',
            'Data.Major Minerals.Zinc': 'zinc',
            'Data.Major Minerals.Copper': 'copper',
            'Data.Selenium': 'selenium',
            'Data.Vitamins.Vitamin A - RAE': 'vitamin_a',
            'Data.Vitamins.Vitamin B6': 'vitamin_b6',
            'Data.Vitamins.Vitamin B12': 'vitamin_b12',
            'Data.Vitamins.Vitamin K': 'vitamin_k',
            'Data.Thiamin': 'thiamin',
            'Data.Riboflavin': 'riboflavin',
            'Data.Niacin': 'niacin',
            'Data.Choline': 'choline',
            'Data.Water': 'water'
        }
        
        # Extract nutrients that exist in the data
        for col, nutrient_name in column_mapping.items():
            if col in self.food_data.columns:
                # Convert to numeric, fill NaN with 0
                values = pd.to_numeric(self.food_data[col], errors='coerce').fillna(0).values
                nutrients[nutrient_name] = values
        
        # Add enriched nutrients if available
        if 'Folate_DFE_ug' in self.food_data.columns:
            nutrients['folate_dfe'] = pd.to_numeric(self.food_data['Folate_DFE_ug'], errors='coerce').fillna(0).values
        
        if 'EPA_g' in self.food_data.columns:
            nutrients['epa'] = pd.to_numeric(self.food_data['EPA_g'], errors='coerce').fillna(0).values
        
        if 'DHA_g' in self.food_data.columns:
            nutrients['dha'] = pd.to_numeric(self.food_data['DHA_g'], errors='coerce').fillna(0).values
        
        return nutrients
    
    def _apply_genotype_adjustments(self):
        """Apply genotype-based adjustments to targets and penalties"""
        # Adjust fiber target based on TCF7L2
        if 'fiber' in self.RDA_VALUES:
            self.RDA_VALUES['fiber'] += self.genotype_adjustments.get('fiber_target_bonus_g', 0)
        
        # Store adjustments for use in objective calculation
        self.vitamin_a_conversion_factor = self.genotype_adjustments.get('vitamin_a_conversion_factor', 12)
        self.sat_fat_penalty_multiplier = self.genotype_adjustments.get('sat_fat_penalty_multiplier', 1.0)
        self.epa_dha_min_mg = self.genotype_adjustments.get('epa_dha_min_mg', 0)
        self.added_sugar_max_delta_g = self.genotype_adjustments.get('added_sugar_max_delta_g', 0)
    
    def _evaluate(self, X, out, *args, **kwargs):
        """Evaluate objectives for all solutions"""
        n_solutions = X.shape[0]
        F = np.zeros((n_solutions, self.n_obj))
        
        for i in range(n_solutions):
            F[i, :] = self._evaluate_single_solution(X[i, :])
        
        out["F"] = F
    
    def _evaluate_single_solution(self, x: np.ndarray) -> np.ndarray:
        """Evaluate objectives for a single solution"""
        # Convert to quantities (grams per 100g)
        q = x / 100.0
        
        # Calculate macronutrients
        calories = self._calculate_calories(q)
        protein = q @ self.nutrient_arrays['protein']
        fat = q @ self.nutrient_arrays['fat']
        carbs = q @ self.nutrient_arrays['carbs']
        
        # Objective 1: Macro Deviation (minimize)
        macro_deviation = self._calculate_macro_deviation(calories, protein, fat, carbs)
        
        # Objective 2: Micronutrient Completeness (maximize, so return negative)
        micronutrient_score = self._calculate_micronutrient_completeness(q)
        
        # Objective 3: Antioxidant Diversity (maximize, so return negative)
        antioxidant_score = self._calculate_antioxidant_diversity(q)
        
        # Objective 4: Sugar-Fiber Ratio (minimize)
        sugar_fiber_penalty = self._calculate_sugar_fiber_penalty(q)
        
        # Objective 5: Fat Quality (maximize, so return negative)
        fat_quality_score = self._calculate_fat_quality(q)
        
        # Objective 6: Electrolyte Balance (minimize)
        electrolyte_penalty = self._calculate_electrolyte_penalty(q)
        
        # Objective 7: Food Diversity (maximize, so return negative)
        diversity_score = self._calculate_food_diversity(x)
        
        # Objective 8: Total Weight (minimize)
        total_weight = np.sum(x)
        
        return np.array([
            macro_deviation,
            -micronutrient_score,  # Negative for maximization
            -antioxidant_score,    # Negative for maximization
            sugar_fiber_penalty,
            -fat_quality_score,    # Negative for maximization
            electrolyte_penalty,
            -diversity_score,      # Negative for maximization
            total_weight
        ])
    
    def _calculate_calories(self, q: np.ndarray) -> float:
        """Calculate total calories"""
        protein_cals = q @ self.nutrient_arrays['protein'] * 4
        fat_cals = q @ self.nutrient_arrays['fat'] * 9
        carb_cals = q @ self.nutrient_arrays['carbs'] * 4
        return protein_cals + fat_cals + carb_cals
    
    def _calculate_macro_deviation(self, calories: float, protein: float, fat: float, carbs: float) -> float:
        """Calculate deviation from macro targets"""
        cal_dev = abs(calories - self.macro_targets['calories']) / self.macro_targets['calories']
        pro_dev = abs(protein - self.macro_targets['protein']) / self.macro_targets['protein']
        fat_dev = abs(fat - self.macro_targets['fat']) / self.macro_targets['fat']
        carb_dev = abs(carbs - self.macro_targets['carbs']) / self.macro_targets['carbs']
        
        return (cal_dev + pro_dev + fat_dev + carb_dev) / 4
    
    def _calculate_micronutrient_completeness(self, q: np.ndarray) -> float:
        """Calculate micronutrient completeness score with genotype adjustments"""
        total_score = 0
        count = 0
        
        for nutrient, rda in self.RDA_VALUES.items():
            if nutrient in self.nutrient_arrays:
                intake = q @ self.nutrient_arrays[nutrient]
                
                # Special handling for vitamin A with genotype adjustment
                if nutrient == 'vitamin_a':
                    # Calculate effective vitamin A with genotype-adjusted conversion
                    retinol = q @ self.nutrient_arrays['vitamin_a']
                    beta_carotene = q @ self.nutrient_arrays['beta_carotene']
                    effective_vit_a = retinol + (beta_carotene / self.vitamin_a_conversion_factor)
                    intake = effective_vit_a
                
                # Calculate adequacy percentage
                adequacy = min(1.0, intake / rda) if rda > 0 else 0
                total_score += adequacy
                count += 1
        
        return total_score / count if count > 0 else 0
    
    def _calculate_antioxidant_diversity(self, q: np.ndarray) -> float:
        """Calculate antioxidant diversity score"""
        antioxidants = ['alpha_carotene', 'beta_carotene', 'vitamin_c', 'vitamin_e', 'lycopene']
        total_antioxidants = 0
        diversity_score = 0
        
        for antioxidant in antioxidants:
            if antioxidant in self.nutrient_arrays:
                amount = q @ self.nutrient_arrays[antioxidant]
                total_antioxidants += amount
                if amount > 0:
                    diversity_score += 1
        
        # Combine total amount and diversity
        return (total_antioxidants / 1000) * (diversity_score / len(antioxidants))
    
    def _calculate_sugar_fiber_penalty(self, q: np.ndarray) -> float:
        """Calculate sugar-fiber ratio penalty with genotype adjustments"""
        total_sugar = q @ self.nutrient_arrays['sugar']
        total_fiber = q @ self.nutrient_arrays['fiber']
        
        # Apply TCF7L2 adjustment to sugar cap
        adjusted_sugar_cap = 50 + self.added_sugar_max_delta_g  # Base cap + adjustment
        
        sugar_penalty = max(0, total_sugar - adjusted_sugar_cap)
        fiber_penalty = max(0, self.RDA_VALUES['fiber'] - total_fiber)
        
        ratio_penalty = (total_sugar / max(total_fiber, 1)) - 2  # Penalty if ratio > 2
        
        return sugar_penalty + fiber_penalty + max(0, ratio_penalty)
    
    def _calculate_fat_quality(self, q: np.ndarray) -> float:
        """Calculate fat quality score with APOE genotype adjustment"""
        saturated = q @ self.nutrient_arrays['saturated_fat']
        mono = q @ self.nutrient_arrays['monounsaturated_fat']
        poly = q @ self.nutrient_arrays['polyunsaturated_fat']
        total_fat = saturated + mono + poly
        
        if total_fat == 0:
            return 0
        
        # Calculate fat ratios
        sat_ratio = saturated / total_fat
        mono_ratio = mono / total_fat
        poly_ratio = poly / total_fat
        
        # Mediterranean-style fat quality score
        sat_penalty = max(0, sat_ratio - 0.1) * self.sat_fat_penalty_multiplier  # Apply APOE adjustment
        mono_bonus = min(1, mono_ratio / 0.6)
        poly_bonus = min(1, poly_ratio / 0.3)
        
        # EPA/DHA bonus (FADS1 adjustment)
        epa_dha_bonus = 0
        if 'epa' in self.nutrient_arrays and 'dha' in self.nutrient_arrays:
            epa = q @ self.nutrient_arrays['epa']
            dha = q @ self.nutrient_arrays['dha']
            total_epa_dha = (epa + dha) * 1000  # Convert to mg
            if total_epa_dha >= self.epa_dha_min_mg:
                epa_dha_bonus = 0.2
        
        return (1 - sat_penalty) + mono_bonus + poly_bonus + epa_dha_bonus
    
    def _calculate_electrolyte_penalty(self, q: np.ndarray) -> float:
        """Calculate electrolyte balance penalty"""
        sodium = q @ self.nutrient_arrays['sodium']
        potassium = q @ self.nutrient_arrays['potassium']
        
        if potassium == 0:
            return 1000  # High penalty if no potassium
        
        ratio = sodium / potassium
        target_ratio = 0.5  # Ideal Na:K ratio
        
        return abs(ratio - target_ratio)
    
    def _calculate_food_diversity(self, x: np.ndarray) -> float:
        """Calculate food diversity score"""
        # Count foods with significant amounts (>10g)
        significant_foods = np.sum(x > 10)
        return min(1.0, significant_foods / 20)  # Normalize to 0-1

def run_nutrigenomic_optimization(food_data: pd.DataFrame, macro_targets: Dict[str, float], 
                                genotype_adjustments: Optional[Dict[str, Any]] = None,
                                population_size: int = 100, generations: int = 200) -> Dict[str, Any]:
    """Run nutrigenomic nutrition optimization"""
    
    print("Initializing Nutrigenomic Nutrition Problem...")
    problem = NutrigenomicNutritionProblem(food_data, macro_targets, genotype_adjustments)
    
    print(f"Problem initialized with {problem.n_foods} foods and {problem.n_obj} objectives")
    if genotype_adjustments and genotype_adjustments.get('applied_rules'):
        print("Applied genotype rules:")
        for rule in genotype_adjustments['applied_rules']:
            print(f"  - {rule['gene']}: {rule['note']}")
    
    # Setup optimization algorithm
    algorithm = NSGA2(pop_size=population_size)
    termination = get_termination('n_gen', generations)
    
    print(f"Starting optimization with population size {population_size} for {generations} generations...")
    
    # Run optimization
    result = minimize(problem, algorithm, termination, seed=42, verbose=True)
    
    print(f"Optimization completed! Found {len(result.X)} Pareto-optimal solutions.")
    
    return {
        'X': result.X,  # Decision variables (food quantities)
        'F': result.F,  # Objective values
        'problem': problem,
        'genotype_adjustments': genotype_adjustments
    }

if __name__ == "__main__":
    # Example usage
    print("Nutrigenomic Nutrition Optimizer")
    print("=================================")
    
    # Load sample food data
    try:
        food_data = pd.read_csv('data/food.csv')
        print(f"Loaded {len(food_data)} foods from data/food.csv")
    except FileNotFoundError:
        print("Warning: data/food.csv not found. Using dummy data.")
        # Create dummy food data for testing
        N = 100
        food_data = pd.DataFrame({
            'Description': [f'Food {i}' for i in range(N)],
            'Category': ['Fruits', 'Vegetables', 'Grains', 'Proteins', 'Dairy'] * (N // 5),
            'Data.Protein': np.random.uniform(0, 30, N),
            'Data.Carbohydrate': np.random.uniform(0, 80, N),
            'Data.Fat.Total Lipid': np.random.uniform(0, 20, N),
            'Data.Fiber': np.random.uniform(0, 15, N),
            'Data.Sugar Total': np.random.uniform(0, 50, N),
            'Data.Major Minerals.Sodium': np.random.uniform(0, 1000, N),
            'Data.Major Minerals.Potassium': np.random.uniform(0, 500, N),
            'Data.Major Minerals.Calcium': np.random.uniform(0, 300, N),
            'Data.Major Minerals.Iron': np.random.uniform(0, 5, N),
            'Data.Alpha Carotene': np.random.uniform(0, 1000, N),
            'Data.Beta Carotene': np.random.uniform(0, 5000, N),
            'Data.Vitamins.Vitamin E': np.random.uniform(0, 10, N),
            'Data.Lycopene': np.random.uniform(0, 2000, N),
            'Data.Fat.Saturated Fat': np.random.uniform(0, 10, N),
            'Data.Fat.Monosaturated Fat': np.random.uniform(0, 15, N),
            'Data.Fat.Polysaturated Fat': np.random.uniform(0, 8, N),
            'Data.Major Minerals.Magnesium': np.random.uniform(0, 100, N),
            'Data.Major Minerals.Phosphorus': np.random.uniform(0, 200, N),
            'Data.Major Minerals.Zinc': np.random.uniform(0, 3, N),
            'Data.Major Minerals.Copper': np.random.uniform(0, 1, N),
            'Data.Selenium': np.random.uniform(0, 50, N),
            'Data.Vitamins.Vitamin A - RAE': np.random.uniform(0, 500, N),
            'Data.Vitamins.Vitamin B6': np.random.uniform(0, 2, N),
            'Data.Vitamins.Vitamin B12': np.random.uniform(0, 5, N),
            'Data.Vitamins.Vitamin K': np.random.uniform(0, 200, N),
            'Data.Thiamin': np.random.uniform(0, 2, N),
            'Data.Riboflavin': np.random.uniform(0, 2, N),
            'Data.Niacin': np.random.uniform(0, 20, N),
            'Data.Choline': np.random.uniform(0, 100, N),
            'Data.Water': np.random.uniform(0, 95, N)
        })
    
    # Define macro targets
    macro_targets = {
        'calories': 2000,
        'protein': 50,
        'fat': 70,
        'carbs': 310
    }
    
    # Example genotype adjustments (BCMO1 variant carrier)
    genotype_adjustments = {
        "vitamin_a_conversion_factor": 24,  # BCMO1 variant
        "sat_fat_penalty_multiplier": 1.0,
        "epa_dha_min_mg": 0,
        "fiber_target_bonus_g": 0,
        "added_sugar_max_delta_g": 0,
        "applied_rules": [
            {"gene": "BCMO1", "note": "WT=12; carriers use higher factor (24–36) to convert beta-carotene to retinol equivalents."}
        ]
    }
    
    # Run optimization
    result = run_nutrigenomic_optimization(
        food_data, 
        macro_targets, 
        genotype_adjustments,
        population_size=50,  # Smaller for testing
        generations=50       # Smaller for testing
    )
    
    print(f"\nOptimization Results:")
    print(f"Number of solutions: {len(result['X'])}")
    print(f"Objective dimensions: {result['F'].shape[1]}")
    print(f"Best macro deviation: {np.min(result['F'][:, 0]):.4f}")
    print(f"Best micronutrient score: {-np.min(result['F'][:, 1]):.4f}") 