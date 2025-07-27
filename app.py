import os
import json
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, jsonify, session
from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.termination import get_termination
from pymoo.optimize import minimize
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly
from datetime import datetime
import uuid

# Import our nutrition optimization system
import sys
sys.path.append('.')
from advanced_nutrition_optimizer import AdvancedNutritionProblem, nutrient_arrays, categories, descriptions, RDA_VALUES

app = Flask(__name__)
app.secret_key = 'nutrition_optimizer_secret_key_2024'

# Global variables to store optimization results
optimization_results = {}

class NutritionUI:
    def __init__(self):
        self.objective_names = [
            "Macro Deviation",
            "Micronutrient Completeness", 
            "Antioxidant Diversity",
            "Sugar-Fiber Ratio",
            "Fat Quality",
            "Electrolyte Balance", 
            "Food Diversity",
            "Total Weight"
        ]
        
        self.objective_descriptions = {
            "Macro Deviation": "Minimizes deviation from calorie, protein, fat, and carb targets",
            "Micronutrient Completeness": "Maximizes achievement of RDA targets for 20+ essential nutrients",
            "Antioxidant Diversity": "Maximizes variety and total antioxidant power across different families",
            "Sugar-Fiber Ratio": "Optimizes sugar-to-fiber ratio, favoring whole foods over processed",
            "Fat Quality": "Maximizes Mediterranean-style fat quality ratios",
            "Electrolyte Balance": "Optimizes sodium:potassium ratio for blood pressure health",
            "Food Diversity": "Maximizes variety across different food categories",
            "Total Weight": "Minimizes total food weight for practical portion sizes"
        }
        
        self.objective_units = {
            "Macro Deviation": "ratio",
            "Micronutrient Completeness": "score (0-1)",
            "Antioxidant Diversity": "score (0-1)", 
            "Sugar-Fiber Ratio": "penalty",
            "Fat Quality": "score (0-1)",
            "Electrolyte Balance": "penalty",
            "Food Diversity": "score (0-1)",
            "Total Weight": "kg"
        }

nutrition_ui = NutritionUI()

@app.route('/')
def index():
    return render_template('index.html', 
                         objective_names=nutrition_ui.objective_names,
                         objective_descriptions=nutrition_ui.objective_descriptions)

@app.route('/optimize', methods=['POST'])
def optimize():
    try:
        data = request.get_json()
        
        # Get user preferences
        macro_targets = {
            'calories': data.get('calories', 2000),
            'protein': data.get('protein', 50),
            'fat': data.get('fat', 70),
            'carbs': data.get('carbs', 310)
        }
        
        selected_objectives = data.get('objectives', list(range(8)))
        population_size = data.get('population_size', 100)
        generations = data.get('generations', 200)
        
        # Store session data
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        session['macro_targets'] = macro_targets
        session['selected_objectives'] = selected_objectives
        
        # Run optimization
        print(f"Starting optimization with {len(selected_objectives)} objectives...")
        
        problem = AdvancedNutritionProblem()
        algorithm = NSGA2(pop_size=population_size)
        termination = get_termination('n_gen', generations)
        
        result = minimize(problem, algorithm, termination, seed=42, verbose=False)
        
        # Store results
        optimization_results[session_id] = {
            'X': result.X,
            'F': result.F,
            'macro_targets': macro_targets,
            'selected_objectives': selected_objectives,
            'timestamp': datetime.now().isoformat()
        }
        
        # Prepare response
        n_solutions = len(result.X)
        objective_stats = []
        
        for i, obj_name in enumerate(nutrition_ui.objective_names):
            if i in selected_objectives:
                values = result.F[:, i]
                # Convert maximization objectives (negative values) to positive for display
                if i in [1, 2, 4, 6]:  # Maximization objectives
                    values = -values
                
                objective_stats.append({
                    'name': obj_name,
                    'min': float(np.min(values)),
                    'max': float(np.max(values)),
                    'mean': float(np.mean(values)),
                    'unit': nutrition_ui.objective_units[obj_name]
                })
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'n_solutions': n_solutions,
            'objective_stats': objective_stats,
            'message': f'Optimization completed! Found {n_solutions} Pareto-optimal solutions.'
        })
        
    except Exception as e:
        print(f"Optimization error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/visualize', methods=['POST'])
def visualize():
    try:
        data = request.get_json()
        session_id = session.get('session_id')
        
        if session_id not in optimization_results:
            return jsonify({'success': False, 'error': 'No optimization results found'})
        
        results = optimization_results[session_id]
        selected_viz_objectives = data.get('objectives', [0, 1])
        chart_type = data.get('chart_type', 'auto')
        
        # Generate visualization based on number of objectives
        if len(selected_viz_objectives) == 2:
            plot_json = create_2d_scatter(results, selected_viz_objectives)
        elif len(selected_viz_objectives) == 3:
            plot_json = create_3d_scatter(results, selected_viz_objectives)
        elif len(selected_viz_objectives) > 3:
            if chart_type == 'parallel':
                plot_json = create_parallel_coordinates(results, selected_viz_objectives)
            else:
                plot_json = create_radar_chart(results, selected_viz_objectives)
        else:
            return jsonify({'success': False, 'error': 'Please select at least 2 objectives'})
        
        return jsonify({
            'success': True,
            'plot_json': plot_json,
            'chart_type': chart_type
        })
        
    except Exception as e:
        print(f"Visualization error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/solutions')
def solutions():
    session_id = session.get('session_id')
    if session_id not in optimization_results:
        return render_template('solutions.html', solutions=[])
    
    results = optimization_results[session_id]
    X, F = results['X'], results['F']
    selected_objectives = results['selected_objectives']
    
    # Prepare solutions data
    solutions_data = []
    for i in range(len(X)):
        solution = {
            'id': i,
            'weights': X[i].tolist(),
            'objectives': {}
        }
        
        for j, obj_idx in enumerate(selected_objectives):
            obj_name = nutrition_ui.objective_names[obj_idx]
            value = F[i, obj_idx]
            
            # Convert maximization objectives for display
            if obj_idx in [1, 2, 4, 6]:
                value = -value
            
            solution['objectives'][obj_name] = {
                'value': float(value),
                'unit': nutrition_ui.objective_units[obj_name]
            }
        
        solutions_data.append(solution)
    
    return render_template('solutions.html', 
                         solutions=solutions_data,
                         objective_names=[nutrition_ui.objective_names[i] for i in selected_objectives])

@app.route('/solution/<int:solution_id>')
def solution_detail(solution_id):
    session_id = session.get('session_id')
    if session_id not in optimization_results:
        return jsonify({'error': 'No optimization results found'})
    
    results = optimization_results[session_id]
    X, F = results['X'], results['F']
    
    if solution_id >= len(X):
        return jsonify({'error': 'Solution not found'})
    
    # Get solution data
    quantities = X[solution_id]
    q = quantities / 100.0
    
    # Calculate detailed analysis
    analysis = analyze_solution_detailed(quantities, q)
    
    return jsonify({
        'success': True,
        'analysis': analysis,
        'solution_id': solution_id
    })

def analyze_solution_detailed(quantities, q):
    """Detailed analysis of a specific solution"""
    
    # Macronutrients
    calories = q @ nutrient_arrays['protein'] * 4 + q @ nutrient_arrays['carbs'] * 4 + q @ nutrient_arrays['fat'] * 9
    protein = q @ nutrient_arrays['protein']
    fat = q @ nutrient_arrays['fat']
    carbs = q @ nutrient_arrays['carbs']
    
    macros = {
        'calories': float(calories),
        'protein': float(protein),
        'fat': float(fat),
        'carbs': float(carbs)
    }
    
    # Micronutrients
    micronutrients = {}
    for nutrient in RDA_VALUES:
        if nutrient in nutrient_arrays:
            intake = q @ nutrient_arrays[nutrient]
            rda = RDA_VALUES[nutrient]
            percentage = (intake / rda) * 100 if rda > 0 else 0
            
            micronutrients[nutrient] = {
                'intake': float(intake),
                'rda': float(rda),
                'percentage': float(percentage),
                'status': 'excellent' if percentage >= 100 else 'good' if percentage >= 75 else 'poor'
            }
    
    # Food composition
    foods = []
    for i, amount in enumerate(quantities):
        if amount > 5:  # Only include significant amounts
            foods.append({
                'name': descriptions[i],
                'category': categories[i],
                'amount': float(amount)
            })
    
    foods.sort(key=lambda x: x['amount'], reverse=True)
    
    # Antioxidants
    antioxidants = {}
    antioxidant_nutrients = ['alpha_carotene', 'beta_carotene', 'vitamin_c', 'vitamin_e', 'lycopene']
    for antioxidant in antioxidant_nutrients:
        if antioxidant in nutrient_arrays:
            amount = q @ nutrient_arrays[antioxidant]
            antioxidants[antioxidant] = float(amount)
    
    # Sugar-Fiber analysis
    total_sugar = q @ nutrient_arrays['sugar']
    total_fiber = q @ nutrient_arrays['fiber']
    sugar_fiber_ratio = total_sugar / total_fiber if total_fiber > 0 else float('inf')
    
    sugar_fiber = {
        'sugar': float(total_sugar),
        'fiber': float(total_fiber),
        'ratio': float(sugar_fiber_ratio) if sugar_fiber_ratio != float('inf') else None,
        'quality': 'excellent' if sugar_fiber_ratio <= 1 else 'good' if sugar_fiber_ratio <= 2 else 'poor'
    }
    
    # Fat quality
    saturated = q @ nutrient_arrays['saturated_fat']
    mono = q @ nutrient_arrays['monounsaturated_fat']
    poly = q @ nutrient_arrays['polyunsaturated_fat']
    total_fat_breakdown = saturated + mono + poly
    
    if total_fat_breakdown > 0:
        fat_quality = {
            'saturated': {'amount': float(saturated), 'percentage': float((saturated / total_fat_breakdown) * 100)},
            'monounsaturated': {'amount': float(mono), 'percentage': float((mono / total_fat_breakdown) * 100)},
            'polyunsaturated': {'amount': float(poly), 'percentage': float((poly / total_fat_breakdown) * 100)}
        }
    else:
        fat_quality = {
            'saturated': {'amount': 0, 'percentage': 0},
            'monounsaturated': {'amount': 0, 'percentage': 0},
            'polyunsaturated': {'amount': 0, 'percentage': 0}
        }
    
    # Electrolytes
    sodium = q @ nutrient_arrays['sodium']
    potassium = q @ nutrient_arrays['potassium']
    electrolyte_ratio = sodium / potassium if potassium > 0 else float('inf')
    
    electrolytes = {
        'sodium': float(sodium),
        'potassium': float(potassium),
        'ratio': float(electrolyte_ratio) if electrolyte_ratio != float('inf') else None,
        'quality': 'excellent' if electrolyte_ratio <= 0.5 else 'good' if electrolyte_ratio <= 1.0 else 'poor'
    }
    
    return {
        'macros': macros,
        'micronutrients': micronutrients,
        'foods': foods,
        'antioxidants': antioxidants,
        'sugar_fiber': sugar_fiber,
        'fat_quality': fat_quality,
        'electrolytes': electrolytes
    }

def create_2d_scatter(results, selected_objectives):
    """Create 2D scatter plot for 2 objectives"""
    X, F = results['X'], results['F']
    obj_names = [nutrition_ui.objective_names[i] for i in selected_objectives]
    
    # Extract objective values
    x_vals = F[:, selected_objectives[0]]
    y_vals = F[:, selected_objectives[1]]
    
    # Convert maximization objectives for display
    if selected_objectives[0] in [1, 2, 4, 6]:
        x_vals = -x_vals
    if selected_objectives[1] in [1, 2, 4, 6]:
        y_vals = -y_vals
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode='markers',
        marker=dict(
            size=8,
            color=np.arange(len(x_vals)),
            colorscale='viridis',
            showscale=True,
            colorbar=dict(title="Solution Index")
        ),
        text=[f"Solution {i}" for i in range(len(x_vals))],
        hovertemplate=f'<b>%{{text}}</b><br>' +
                     f'{obj_names[0]}: %{{x:.3f}}<br>' +
                     f'{obj_names[1]}: %{{y:.3f}}<br>' +
                     '<extra></extra>',
        name='Pareto Solutions'
    ))
    
    fig.update_layout(
        title=f'Pareto Front: {obj_names[0]} vs {obj_names[1]}',
        xaxis_title=f'{obj_names[0]} ({nutrition_ui.objective_units[obj_names[0]]})',
        yaxis_title=f'{obj_names[1]} ({nutrition_ui.objective_units[obj_names[1]]})',
        hovermode='closest',
        template='plotly_white'
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def create_3d_scatter(results, selected_objectives):
    """Create 3D scatter plot for 3 objectives"""
    X, F = results['X'], results['F']
    obj_names = [nutrition_ui.objective_names[i] for i in selected_objectives]
    
    # Extract objective values
    x_vals = F[:, selected_objectives[0]]
    y_vals = F[:, selected_objectives[1]]
    z_vals = F[:, selected_objectives[2]]
    
    # Convert maximization objectives for display
    if selected_objectives[0] in [1, 2, 4, 6]:
        x_vals = -x_vals
    if selected_objectives[1] in [1, 2, 4, 6]:
        y_vals = -y_vals
    if selected_objectives[2] in [1, 2, 4, 6]:
        z_vals = -z_vals
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter3d(
        x=x_vals,
        y=y_vals,
        z=z_vals,
        mode='markers',
        marker=dict(
            size=6,
            color=np.arange(len(x_vals)),
            colorscale='viridis',
            showscale=True,
            colorbar=dict(title="Solution Index")
        ),
        text=[f"Solution {i}" for i in range(len(x_vals))],
        hovertemplate=f'<b>%{{text}}</b><br>' +
                     f'{obj_names[0]}: %{{x:.3f}}<br>' +
                     f'{obj_names[1]}: %{{y:.3f}}<br>' +
                     f'{obj_names[2]}: %{{z:.3f}}<br>' +
                     '<extra></extra>',
        name='Pareto Solutions'
    ))
    
    fig.update_layout(
        title=f'3D Pareto Front: {obj_names[0]} vs {obj_names[1]} vs {obj_names[2]}',
        scene=dict(
            xaxis_title=f'{obj_names[0]} ({nutrition_ui.objective_units[obj_names[0]]})',
            yaxis_title=f'{obj_names[1]} ({nutrition_ui.objective_units[obj_names[1]]})',
            zaxis_title=f'{obj_names[2]} ({nutrition_ui.objective_units[obj_names[2]]})'
        ),
        template='plotly_white'
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def create_parallel_coordinates(results, selected_objectives):
    """Create parallel coordinates plot for multiple objectives"""
    X, F = results['X'], results['F']
    obj_names = [nutrition_ui.objective_names[i] for i in selected_objectives]
    
    # Prepare data
    dimensions = []
    for i, obj_idx in enumerate(selected_objectives):
        values = F[:, obj_idx]
        # Convert maximization objectives for display
        if obj_idx in [1, 2, 4, 6]:
            values = -values
        
        dimensions.append(dict(
            range=[float(np.min(values)), float(np.max(values))],
            label=obj_names[i],
            values=values.tolist()
        ))
    
    fig = go.Figure(data=go.Parcoords(
        line=dict(
            color=np.arange(len(F)),
            colorscale='viridis',
            showscale=True,
            colorbar=dict(title="Solution Index")
        ),
        dimensions=dimensions
    ))
    
    fig.update_layout(
        title='Parallel Coordinates Plot of Pareto Solutions',
        template='plotly_white'
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def create_radar_chart(results, selected_objectives):
    """Create radar chart showing top solutions"""
    X, F = results['X'], results['F']
    obj_names = [nutrition_ui.objective_names[i] for i in selected_objectives]
    
    # Normalize objectives to 0-1 scale for radar chart
    normalized_data = []
    for obj_idx in selected_objectives:
        values = F[:, obj_idx]
        # Convert maximization objectives for display
        if obj_idx in [1, 2, 4, 6]:
            values = -values
        
        # Normalize to 0-1 (higher is better for radar chart)
        min_val, max_val = np.min(values), np.max(values)
        if max_val > min_val:
            if obj_idx in [0, 3, 5, 7]:  # Minimization objectives - flip scale
                normalized = 1 - (values - min_val) / (max_val - min_val)
            else:  # Maximization objectives
                normalized = (values - min_val) / (max_val - min_val)
        else:
            normalized = np.ones_like(values) * 0.5
        
        normalized_data.append(normalized)
    
    normalized_data = np.array(normalized_data).T
    
    # Show top 5 solutions based on average performance
    avg_scores = np.mean(normalized_data, axis=1)
    top_indices = np.argsort(avg_scores)[-5:]
    
    fig = go.Figure()
    
    colors = ['red', 'blue', 'green', 'orange', 'purple']
    
    for i, idx in enumerate(top_indices):
        values = normalized_data[idx].tolist()
        values += values[:1]  # Close the radar chart
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=obj_names + [obj_names[0]],
            fill='toself',
            name=f'Solution {idx}',
            line=dict(color=colors[i])
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        showlegend=True,
        title="Top 5 Solutions - Radar Chart",
        template='plotly_white'
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)