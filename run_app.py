#!/usr/bin/env python3
"""
Simple startup script for the Advanced Nutrition Optimizer Web UI
================================================================

This script handles all the setup and runs the Flask application.
It will work even if optional dependencies are missing.
"""

import sys
import os
import subprocess

def check_and_install_dependencies():
    """Check for required dependencies and install if missing"""
    required_packages = ['flask', 'plotly', 'pandas', 'numpy']
    optional_packages = ['pymoo', 'matplotlib', 'seaborn']
    
    missing_required = []
    missing_optional = []
    
    # Check required packages
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is available")
        except ImportError:
            missing_required.append(package)
            print(f"❌ {package} is missing (required)")
    
    # Check optional packages
    for package in optional_packages:
        try:
            __import__(package)
            print(f"✅ {package} is available")
        except ImportError:
            missing_optional.append(package)
            print(f"⚠️  {package} is missing (optional)")
    
    # Install missing required packages
    if missing_required:
        print(f"\n🔧 Installing required packages: {missing_required}")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_required)
            print("✅ Required packages installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install required packages. Please install manually:")
            print(f"   pip install {' '.join(missing_required)}")
            return False
    
    # Offer to install optional packages
    if missing_optional:
        print(f"\n⚠️  Optional packages missing: {missing_optional}")
        print("These provide full optimization functionality.")
        response = input("Install optional packages? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_optional)
                print("✅ Optional packages installed successfully")
            except subprocess.CalledProcessError:
                print("⚠️  Some optional packages failed to install. The app will still work with demo data.")
    
    return True

def run_application():
    """Run the Flask application"""
    print("\n🚀 Starting Advanced Nutrition Optimizer Web UI...")
    print("=" * 60)
    
    try:
        # Import and run the app
        from app import app
        print("✅ Application loaded successfully")
        print("\n🌐 Open your browser and go to: http://localhost:5000")
        print("💡 Press Ctrl+C to stop the server")
        print("=" * 60)
        
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except KeyboardInterrupt:
        print("\n\n👋 Application stopped by user")
        
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure you have Python 3.8+ installed")
        print("2. Try: pip install flask plotly pandas numpy")
        print("3. Check that all files are in the correct directory")
        return False
    
    return True

def main():
    """Main startup function"""
    print("🥗 ADVANCED NUTRITION OPTIMIZER - STARTUP")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ is required. You have:", sys.version)
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Check and install dependencies
    print("\n🔍 Checking dependencies...")
    if not check_and_install_dependencies():
        return False
    
    # Run the application
    return run_application()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)