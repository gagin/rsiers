#!/usr/bin/env python

"""
Direct installation script for dependencies.
This script will install all required dependencies directly,
without relying on pip's dependency resolution.
"""

import subprocess
import sys
import os
import platform

def main():
    """Install all dependencies directly."""
    print("Installing dependencies directly...")

    # Check if we're in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

    if not in_venv:
        print("WARNING: You are not in a virtual environment.")
        response = input("Do you want to continue installing packages globally? (y/n): ")
        if response.lower() != 'y':
            print("Installation cancelled. Please create and activate a virtual environment first.")
            sys.exit(1)

    # Install dependencies one by one
    dependencies = [
        "wheel",  # Often needed for building packages
        "numpy>=1.26.0",  # Latest version compatible with Python 3.12
        "pandas>=2.0.0",  # Latest version compatible with Python 3.12
        "flask>=2.0.1",
        "flask-cors>=3.0.10",
        "requests>=2.26.0"
    ]

    for dep in dependencies:
        print(f"\nInstalling {dep}...")
        try:
            # Use --no-deps to avoid dependency resolution issues
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-deps", dep])

            # For numpy and pandas, also install with dependencies
            if dep.startswith("numpy") or dep.startswith("pandas"):
                print(f"Installing {dep} with dependencies...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])

            # Verify installation
            package_name = dep.split("==")[0]
            try:
                __import__(package_name)
                print(f"✓ Successfully installed and imported {package_name}")
            except ImportError:
                print(f"✗ Failed to import {package_name} after installation")

        except subprocess.CalledProcessError as e:
            print(f"Error installing {dep}: {e}")
            print("Please try installing it manually.")

    print("\nInstallation complete!")
    print("You can now run the application with:")
    if platform.system() == "Windows":
        print("    start.bat")
    else:
        print("    ./start.sh")

if __name__ == "__main__":
    main()
