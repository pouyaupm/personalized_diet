#!/usr/bin/env python3
"""
Nutrigenomic Day-Planner Pipeline
==================================

Complete pipeline for genotype-aware nutrition optimization:
1. Parse user DNA data (23andMe/Ancestry format)
2. Apply genotype rules to generate nutrition adjustments
3. Enrich food database with FDC API nutrients
4. Run genotype-aware multi-objective optimization
5. Generate personalized nutrition recommendations

Usage:
    python nutrigenomic_pipeline.py --dna user_23andme.txt --calories 2000
"""

import argparse
import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional

# Import our modules
from genotype_parser import GenotypeParser, parse_dna_file
from fdc_api import FDCApi
from nutrigenomic_optimizer import run_nutrigenomic_optimization

class NutrigenomicPipeline:
    """Complete pipeline for genotype-aware nutrition optimization"""
    
    def __init__(self, fdc_api_key: Optional[str] = None):
        """Initialize the pipeline"""
        self.fdc_api_key = fdc_api_key
        self.parser = GenotypeParser()
        
        # Load food data
        self.food_data = self._load_food_data()
        
        # Initialize FDC API if key provided
        self.fdc_api = None
        if self.fdc_api_key:
            try:
                self.fdc_api = FDCApi(self.fdc_api_key)
                print("✓ FDC API initialized successfully")
            except Exception as e:
                print(f"⚠ FDC API initialization failed: {e}")
                print("Continuing without FDC enrichment...")
    
    def _load_food_data(self) -> pd.DataFrame:
        """Load food database"""
        try:
            food_data = pd.read_csv('data/food.csv')
            print(f"✓ Loaded {len(food_data)} foods from data/food.csv")
            return food_data
        except FileNotFoundError:
            print("⚠ data/food.csv not found. Creating sample data...")
            return self._create_sample_food_data()
    
    def _create_sample_food_data(self) -> pd.DataFrame:
        """Create sample food data for testing"""
        N = 100
        categories = ['Fruits', 'Vegetables', 'Grains', 'Proteins', 'Dairy', 'Nuts', 'Oils', 'Beverages']
        
        data = {
            'Category': [categories[i % len(categories)] for i in range(N)],
            'Description': [f'Sample {categories[i % len(categories)]} Item {i+1}' for i in range(N)],
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
        }
        
        return pd.DataFrame(data)
    
    def parse_dna(self, dna_file: str) -> Dict[str, Any]:
        """Parse DNA file and return genotype analysis"""
        print(f"\n🔬 Parsing DNA file: {dna_file}")
        
        if not os.path.exists(dna_file):
            print(f"⚠ DNA file not found: {dna_file}")
            print("Using sample genotype data for demonstration...")
            return self._create_sample_genotype_data()
        
        try:
            result = parse_dna_file(dna_file)
            print(f"✓ Parsed {result['summary']['total_snps']} SNPs")
            
            # Show relevant SNPs found
            if result['summary']['relevant_snps']:
                print("Relevant SNPs found:")
                for rsid, info in result['summary']['relevant_snps'].items():
                    print(f"  - {rsid} ({info['gene']}): {info['genotype']}")
            
            # Show applied rules
            if result['adjustments']['applied_rules']:
                print("Applied genotype rules:")
                for rule in result['adjustments']['applied_rules']:
                    print(f"  - {rule['gene']}: {rule['note']}")
            else:
                print("No genotype rules applied (wild-type or SNPs not found)")
            
            return result
            
        except Exception as e:
            print(f"❌ Error parsing DNA file: {e}")
            print("Using sample genotype data for demonstration...")
            return self._create_sample_genotype_data()
    
    def _create_sample_genotype_data(self) -> Dict[str, Any]:
        """Create sample genotype data for demonstration"""
        sample_genotypes = {
            "rs12934922": "TT",  # BCMO1 variant
            "rs7501331": "CT",   # BCMO1 variant
            "rs429358": "CC",    # APOE variant
            "rs7412": "CT",      # APOE variant
            "rs174546": "TT",    # FADS1 variant
            "rs7903146": "CT"    # TCF7L2 variant
        }
        
        adjustments = self.parser.apply_rules(sample_genotypes)
        summary = self.parser.get_genotype_summary(sample_genotypes)
        
        print("Using sample genotype data with variants:")
        for rsid, genotype in sample_genotypes.items():
            print(f"  - {rsid}: {genotype}")
        
        return {
            "genotypes": sample_genotypes,
            "adjustments": adjustments,
            "summary": summary
        }
    
    def enrich_food_data(self, force_reload: bool = False) -> pd.DataFrame:
        """Enrich food data with FDC nutrients"""
        if not self.fdc_api:
            print("⚠ FDC API not available. Using base food data.")
            return self.food_data
        
        enriched_file = "data/food_enriched.csv"
        
        if not force_reload and os.path.exists(enriched_file):
            print(f"✓ Loading enriched food data from {enriched_file}")
            return pd.read_csv(enriched_file)
        
        print("\n🌐 Enriching food data with FDC API...")
        print("This may take several minutes for large datasets...")
        
        try:
            enriched_data = self.fdc_api.enrich_food_data(self.food_data)
            
            # Save enriched data
            enriched_data.to_csv(enriched_file, index=False)
            print(f"✓ Saved enriched food data to {enriched_file}")
            
            # Show enrichment statistics
            epa_count = enriched_data['EPA_g'].notna().sum()
            dha_count = enriched_data['DHA_g'].notna().sum()
            folate_count = enriched_data['Folate_DFE_ug'].notna().sum()
            
            print(f"Enrichment results:")
            print(f"  - EPA data: {epa_count}/{len(enriched_data)} foods")
            print(f"  - DHA data: {dha_count}/{len(enriched_data)} foods")
            print(f"  - Folate DFE data: {folate_count}/{len(enriched_data)} foods")
            
            return enriched_data
            
        except Exception as e:
            print(f"❌ Error enriching food data: {e}")
            print("Using base food data...")
            return self.food_data
    
    def run_optimization(self, macro_targets: Dict[str, float], 
                        genotype_adjustments: Dict[str, Any],
                        population_size: int = 100, 
                        generations: int = 200) -> Dict[str, Any]:
        """Run genotype-aware nutrition optimization"""
        print(f"\n🎯 Running nutrigenomic optimization...")
        print(f"Macro targets: {macro_targets}")
        print(f"Population size: {population_size}, Generations: {generations}")
        
        try:
            result = run_nutrigenomic_optimization(
                self.food_data,
                macro_targets,
                genotype_adjustments,
                population_size,
                generations
            )
            
            print(f"✓ Optimization completed successfully!")
            print(f"Found {len(result['X'])} Pareto-optimal solutions")
            
            return result
            
        except Exception as e:
            print(f"❌ Optimization failed: {e}")
            raise
    
    def analyze_results(self, optimization_result: Dict[str, Any], 
                       genotype_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze optimization results and generate recommendations"""
        print(f"\n📊 Analyzing optimization results...")
        
        X = optimization_result['X']
        F = optimization_result['F']
        
        # Find knee point (solution with best overall performance)
        # Simple approach: minimize sum of normalized objectives
        F_normalized = (F - F.min(axis=0)) / (F.max(axis=0) - F.min(axis=0) + 1e-8)
        knee_idx = np.argmin(np.sum(F_normalized, axis=1))
        
        # Get knee point solution
        knee_solution = X[knee_idx]
        knee_objectives = F[knee_idx]
        
        # Analyze food composition
        food_analysis = self._analyze_food_composition(knee_solution)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            knee_solution, knee_objectives, genotype_summary
        )
        
        analysis = {
            'knee_point': {
                'solution_idx': int(knee_idx),
                'objectives': knee_objectives.tolist(),
                'food_quantities': knee_solution.tolist()
            },
            'food_analysis': food_analysis,
            'recommendations': recommendations,
            'genotype_summary': genotype_summary,
            'all_solutions': {
                'X': X.tolist(),
                'F': F.tolist()
            }
        }
        
        return analysis
    
    def _analyze_food_composition(self, solution: np.ndarray) -> Dict[str, Any]:
        """Analyze the food composition of a solution"""
        significant_foods = []
        
        for i, amount in enumerate(solution):
            if amount > 10:  # Only include foods with >10g
                food_info = {
                    'index': i,
                    'name': self.food_data.iloc[i]['Description'],
                    'category': self.food_data.iloc[i]['Category'],
                    'amount_g': float(amount)
                }
                significant_foods.append(food_info)
        
        # Sort by amount
        significant_foods.sort(key=lambda x: x['amount_g'], reverse=True)
        
        # Category breakdown
        category_totals = {}
        for food in significant_foods:
            category = food['category']
            if category not in category_totals:
                category_totals[category] = 0
            category_totals[category] += food['amount_g']
        
        return {
            'significant_foods': significant_foods[:10],  # Top 10 foods
            'category_breakdown': category_totals,
            'total_weight_g': float(np.sum(solution))
        }
    
    def _generate_recommendations(self, solution: np.ndarray, 
                                objectives: np.ndarray,
                                genotype_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized recommendations based on genotype and results"""
        recommendations = {
            'general': [],
            'genotype_specific': [],
            'food_suggestions': []
        }
        
        # General recommendations based on objectives
        if objectives[0] < 0.1:  # Good macro balance
            recommendations['general'].append("Excellent macronutrient balance achieved")
        else:
            recommendations['general'].append("Consider adjusting macronutrient targets")
        
        if -objectives[1] > 0.8:  # Good micronutrient completeness
            recommendations['general'].append("Strong micronutrient coverage")
        else:
            recommendations['general'].append("Focus on micronutrient-rich foods")
        
        # Genotype-specific recommendations
        for gene, info in genotype_summary['gene_summary'].items():
            if info['status'] == 'variant_detected':
                if gene == 'BCMO1':
                    recommendations['genotype_specific'].append(
                        "BCMO1 variant detected: Your body converts beta-carotene to vitamin A less efficiently. "
                        "Consider including more pre-formed vitamin A sources (liver, eggs, dairy)."
                    )
                elif gene == 'APOE':
                    recommendations['genotype_specific'].append(
                        "APOE variant detected: You may be more sensitive to saturated fat. "
                        "Focus on unsaturated fats and limit saturated fat intake."
                    )
                elif gene == 'FADS1':
                    recommendations['genotype_specific'].append(
                        "FADS1 variant detected: Your body may benefit from direct EPA/DHA sources. "
                        "Include fatty fish, algae, or supplements in your diet."
                    )
                elif gene == 'TCF7L2':
                    recommendations['genotype_specific'].append(
                        "TCF7L2 variant detected: Higher fiber intake and lower added sugar may be beneficial. "
                        "Focus on whole grains, legumes, and limit processed foods."
                    )
        
        # Food suggestions based on top foods in solution
        top_foods = self._analyze_food_composition(solution)['significant_foods'][:5]
        for food in top_foods:
            recommendations['food_suggestions'].append(
                f"{food['name']} ({food['category']}): {food['amount_g']:.1f}g"
            )
        
        return recommendations
    
    def save_results(self, analysis: Dict[str, Any], output_file: str = "nutrigenomic_results.json"):
        """Save analysis results to file"""
        try:
            with open(output_file, 'w') as f:
                json.dump(analysis, f, indent=2)
            print(f"✓ Results saved to {output_file}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")
    
    def run_complete_pipeline(self, dna_file: str, macro_targets: Dict[str, float],
                            population_size: int = 100, generations: int = 200,
                            enrich_food_data: bool = True, 
                            output_file: str = "nutrigenomic_results.json") -> Dict[str, Any]:
        """Run the complete nutrigenomic pipeline"""
        print("🧬 Nutrigenomic Day-Planner Pipeline")
        print("=" * 50)
        
        # Step 1: Parse DNA
        genotype_result = self.parse_dna(dna_file)
        
        # Step 2: Enrich food data (optional)
        if enrich_food_data and self.fdc_api:
            self.food_data = self.enrich_food_data()
        
        # Step 3: Run optimization
        optimization_result = self.run_optimization(
            macro_targets,
            genotype_result['adjustments'],
            population_size,
            generations
        )
        
        # Step 4: Analyze results
        analysis = self.analyze_results(optimization_result, genotype_result['summary'])
        
        # Step 5: Save results
        self.save_results(analysis, output_file)
        
        # Step 6: Print summary
        self._print_summary(analysis, output_file)
        
        return analysis
    
    def _print_summary(self, analysis: Dict[str, Any], output_file: str = "nutrigenomic_results.json"):
        """Print a summary of the results"""
        print(f"\n📋 Nutrigenomic Analysis Summary")
        print("=" * 40)
        
        # Genotype summary
        genotype_summary = analysis['genotype_summary']
        print(f"Genotype Analysis:")
        print(f"  - Total SNPs analyzed: {genotype_summary['total_snps']}")
        print(f"  - Relevant SNPs found: {len(genotype_summary['relevant_snps'])}")
        
        for gene, info in genotype_summary['gene_summary'].items():
            status_emoji = "🔴" if info['status'] == 'variant_detected' else "🟢"
            print(f"  - {gene}: {status_emoji} {info['status']}")
        
        # Optimization results
        knee_point = analysis['knee_point']
        print(f"\nOptimization Results:")
        print(f"  - Best solution found: #{knee_point['solution_idx']}")
        print(f"  - Total food weight: {analysis['food_analysis']['total_weight_g']:.1f}g")
        
        # Top foods
        print(f"\nTop Recommended Foods:")
        for i, food in enumerate(analysis['food_analysis']['significant_foods'][:5], 1):
            print(f"  {i}. {food['name']} ({food['category']}): {food['amount_g']:.1f}g")
        
        # Recommendations
        print(f"\nKey Recommendations:")
        for rec in analysis['recommendations']['genotype_specific']:
            print(f"  • {rec}")
        
        print(f"\n✓ Analysis complete! Check {output_file} for detailed results.")

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description="Nutrigenomic Day-Planner Pipeline")
    parser.add_argument("--dna", required=True, help="Path to DNA file (23andMe/Ancestry format)")
    parser.add_argument("--calories", type=int, default=2000, help="Target calories")
    parser.add_argument("--protein", type=int, default=50, help="Target protein (g)")
    parser.add_argument("--fat", type=int, default=70, help="Target fat (g)")
    parser.add_argument("--carbs", type=int, default=310, help="Target carbs (g)")
    parser.add_argument("--fdc-key", help="FDC API key for nutrient enrichment")
    parser.add_argument("--population", type=int, default=100, help="Optimization population size")
    parser.add_argument("--generations", type=int, default=200, help="Optimization generations")
    parser.add_argument("--output", default="nutrigenomic_results.json", help="Output file")
    parser.add_argument("--no-enrich", action="store_true", help="Skip FDC enrichment")
    
    args = parser.parse_args()
    
    # Define macro targets
    macro_targets = {
        'calories': args.calories,
        'protein': args.protein,
        'fat': args.fat,
        'carbs': args.carbs
    }
    
    # Initialize pipeline
    pipeline = NutrigenomicPipeline(args.fdc_key)
    
    # Run complete pipeline
    try:
        analysis = pipeline.run_complete_pipeline(
            args.dna,
            macro_targets,
            args.population,
            args.generations,
            not args.no_enrich,
            args.output
        )
        
        print(f"\n🎉 Pipeline completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 