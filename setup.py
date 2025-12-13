"""
Setup script to verify and install dependencies
"""

import subprocess
import sys

def install_requirements():
    """Install requirements from requirements.txt"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def verify_imports():
    """Verify that all required imports work"""
    try:
        from langgraph.graph import StateGraph, END
        print("✅ LangGraph imports successful")
        
        from orchestrator import create_workflow_graph, AgentState
        print("✅ Orchestrator imports successful")
        
        from fastapi import FastAPI
        print("✅ FastAPI import successful")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please run: pip install -r requirements.txt --upgrade")
        return False

if __name__ == "__main__":
    print("Setting up Provider Directory Management System...")
    print("-" * 60)
    
    if install_requirements():
        print("\nVerifying imports...")
        if verify_imports():
            print("\n✅ Setup complete! You can now run: python app.py")
        else:
            print("\n❌ Setup incomplete. Please check the errors above.")
            sys.exit(1)
    else:
        sys.exit(1)

