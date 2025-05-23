#!/usr/bin/env python

"""
Direct installation script for dependencies.
This script will install all required dependencies directly,
supporting both Conda and pip.
"""

import subprocess
import sys
import os
import platform

def is_conda_environment():
    """Check if we're in a Conda environment."""
    return os.environ.get('CONDA_PREFIX') is not None

def main():
    """Install all dependencies directly."""
    print("Installing dependencies directly...")

    # Check if we're in a Conda environment
    using_conda = is_conda_environment()

    if using_conda:
        print(f"Conda environment detected: {os.environ.get('CONDA_PREFIX')}")

        # Dependencies to install with conda
        conda_dependencies = [
            "numpy",
            "pandas",
            "flask",
            "requests"
        ]

        # Dependencies to install with pip
        pip_dependencies = [
            "flask-cors"
        ]

        # Install conda dependencies
        print("\nInstalling dependencies with conda...")
        try:
            subprocess.check_call(["conda", "install", "-y"] + conda_dependencies)
        except subprocess.CalledProcessError as e:
            print(f"Error installing conda dependencies: {e}")
            print("Please try installing them manually with:")
            print(f"conda install {' '.join(conda_dependencies)}")

        # Install pip dependencies
        print("\nInstalling dependencies with pip...")
        for dep in pip_dependencies:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
                print(f"✓ Successfully installed {dep}")
            except subprocess.CalledProcessError as e:
                print(f"Error installing {dep}: {e}")
                print(f"Please try installing it manually with: pip install {dep}")
    else:
        print("Using system Python or non-Conda environment")

        # Dependencies to install with pip
        dependencies = [
            "wheel",  # Often needed for building packages
            "numpy>=1.26.0",  # Latest version compatible with Python 3.12
            "pandas>=2.0.0",  # Latest version compatible with Python 3.12
            "flask>=2.0.1",
            "flask-cors>=3.0.10",
            "requests>=2.26.0"
        ]

        # Install pip dependencies for non-Conda environment
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
                package_name = dep.split(">=")[0].split("==")[0]
                try:
                    __import__(package_name)
                    print(f"✓ Successfully installed and imported {package_name}")
                except ImportError:
                    print(f"✗ Failed to import {package_name} after installation")

            except subprocess.CalledProcessError as e:
                print(f"Error installing {dep}: {e}")
                print("Please try installing it manually.")

    # Verify all required packages are installed
    required_packages = ["numpy", "pandas", "flask", "flask_cors", "requests"]
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} is installed and importable")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} is not installed or not importable")

    if missing_packages:
        print("\nSome required packages are missing or not importable:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nPlease install them manually and try again.")
    else:
        print("\nAll required packages are installed!")

    print("\nInstallation complete!")
    print("You can now run the application with:")
    if platform.system() == "Windows":
        print("    start.bat")
    else:
        print("    ./fix_and_run.sh")
        print("    or")
        print("    ./start_frontend.sh")

if __name__ == "__main__":
    main()
