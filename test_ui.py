#!/usr/bin/env python3
"""
Test script for the Advanced Nutrition Optimizer UI
==================================================

This script tests the basic functionality of the web UI system
without requiring external dependencies that might not be installed.
"""

import os
import sys
import json

def test_file_structure():
    """Test that all required files are present"""
    print("🔍 Testing file structure...")
    
    required_files = [
        'app.py',
        'templates/base.html',
        'templates/index.html', 
        'templates/solutions.html',
        'static/css/style.css',
        'requirements.txt',
        'UI_GUIDE.md'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

def test_template_syntax():
    """Basic test of template syntax"""
    print("🔍 Testing template syntax...")
    
    try:
        # Test that templates contain expected elements
        with open('templates/index.html', 'r') as f:
            index_content = f.read()
            
        with open('templates/solutions.html', 'r') as f:
            solutions_content = f.read()
        
        # Check for key elements
        index_checks = [
            '{% extends "base.html" %}',
            'optimizationForm',
            'objectivesContainer',
            'generateVisualization'
        ]
        
        solutions_checks = [
            '{% extends "base.html" %}', 
            'solutionsContainer',
            'viewSolutionDetail',
            'compareSolution'
        ]
        
        for check in index_checks:
            if check not in index_content:
                print(f"❌ Missing in index.html: {check}")
                return False
                
        for check in solutions_checks:
            if check not in solutions_content:
                print(f"❌ Missing in solutions.html: {check}")
                return False
        
        print("✅ Template syntax looks good")
        return True
        
    except Exception as e:
        print(f"❌ Template test failed: {e}")
        return False

def test_app_imports():
    """Test that the main app can import required modules"""
    print("🔍 Testing app imports...")
    
    try:
        # Test basic imports without running the app
        import importlib.util
        
        spec = importlib.util.spec_from_file_location("app", "app.py")
        if spec is None:
            print("❌ Could not load app.py")
            return False
            
        # Check if we can at least parse the file
        with open('app.py', 'r') as f:
            app_content = f.read()
            
        # Basic syntax check
        compile(app_content, 'app.py', 'exec')
        
        print("✅ App syntax is valid")
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error in app.py: {e}")
        return False
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_ui_features():
    """Test that UI features are properly implemented"""
    print("🔍 Testing UI feature implementation...")
    
    try:
        with open('app.py', 'r') as f:
            app_content = f.read()
        
        # Check for key features
        required_features = [
            'create_2d_scatter',
            'create_3d_scatter', 
            'create_parallel_coordinates',
            'create_radar_chart',
            'analyze_solution_detailed',
            'NutritionUI',
            "@app.route('/optimize'",
            "@app.route('/visualize'",
            "@app.route('/solutions'"
        ]
        
        missing_features = []
        for feature in required_features:
            if feature not in app_content:
                missing_features.append(feature)
        
        if missing_features:
            print(f"❌ Missing features: {missing_features}")
            return False
        else:
            print("✅ All key UI features implemented")
            return True
            
    except Exception as e:
        print(f"❌ Feature test failed: {e}")
        return False

def test_visualization_types():
    """Test that all visualization types are supported"""
    print("🔍 Testing visualization type support...")
    
    try:
        with open('templates/index.html', 'r') as f:
            template_content = f.read()
        
        # Check for visualization controls
        viz_features = [
            'generateVisualization',
            'chartType',
            'vizObjectivesContainer',
            'plotlyChart'
        ]
        
        for feature in viz_features:
            if feature not in template_content:
                print(f"❌ Missing visualization feature: {feature}")
                return False
        
        print("✅ All visualization types supported")
        return True
        
    except Exception as e:
        print(f"❌ Visualization test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and return overall result"""
    print("🧪 ADVANCED NUTRITION OPTIMIZER UI - TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_file_structure,
        test_template_syntax,
        test_app_imports,
        test_ui_features,
        test_visualization_types
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
            print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! UI system is ready.")
        print("\n🚀 To start the application:")
        print("   python app.py")
        print("   Then open: http://localhost:5000")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    print("=" * 60)
    return passed == total

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)