#!/usr/bin/env python

"""
Setup script to ensure all dependencies are properly installed.
This script will:
1. Check if numpy and other dependencies are installed
2. Install them if they're not
"""

import subprocess
import sys
import os
import platform

def check_venv():
    """Check if running in a virtual environment."""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def create_venv():
    """Create a virtual environment if not already in one."""
    if not check_venv():
        print("Creating virtual environment...")
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])
        
        # Determine the Python executable in the virtual environment
        if platform.system() == "Windows":
            python_executable = os.path.join("venv", "Scripts", "python")
        else:
            python_executable = os.path.join("venv", "bin", "python")
        
        # Upgrade pip in the virtual environment
        subprocess.check_call([python_executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        print("Virtual environment created.")
        return python_executable
    else:
        print("Already in a virtual environment.")
        return sys.executable

def install_dependencies(python_executable):
    """Install required dependencies."""
    print("Installing dependencies...")
    
    # Install each dependency individually to better handle errors
    dependencies = [
        "flask==2.0.1",
        "flask-cors==3.0.10",
        "requests==2.26.0",
        "numpy==1.21.2",
        "pandas==1.3.3"
    ]
    
    for dep in dependencies:
        print(f"Installing {dep}...")
        try:
            subprocess.check_call([python_executable, "-m", "pip", "install", dep])
            print(f"Successfully installed {dep}")
        except subprocess.CalledProcessError:
            print(f"Failed to install {dep}. Please install it manually.")
            sys.exit(1)

def main():
    """Main function to set up the environment."""
    print("Setting up the environment...")
    
    # Create virtual environment if needed
    python_executable = create_venv()
    
    # Install dependencies
    install_dependencies(python_executable)
    
    print("\nSetup complete! You can now run the application.")
    print("To activate the virtual environment:")
    if platform.system() == "Windows":
        print("    venv\\Scripts\\activate")
    else:
        print("    source venv/bin/activate")
    
    print("\nTo start the application:")
    if platform.system() == "Windows":
        print("    start.bat")
    else:
        print("    ./start.sh")

if __name__ == "__main__":
    main()
