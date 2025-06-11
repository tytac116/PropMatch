#!/usr/bin/env python3
"""
Install and check dependencies for PropMatch API testing

This script ensures all required packages are installed before running tests.
"""

import subprocess
import sys
import importlib.util
from pathlib import Path

def check_package_installed(package_name):
    """Check if a package is installed"""
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def install_package(package_name):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("🔧 PropMatch API Dependency Checker")
    print("=" * 40)
    
    # Check if requirements.txt exists
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found!")
        print("Please run this script from the Backend directory.")
        return
    
    # Core packages needed for testing
    test_packages = {
        'httpx': 'httpx',  # For API testing
        'asyncio': None,    # Built-in, just check
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn[standard]',
        'sqlalchemy': 'sqlalchemy',
        'psycopg2': 'psycopg2-binary'
    }
    
    print("Checking required packages...")
    
    missing_packages = []
    for package, install_name in test_packages.items():
        if check_package_installed(package):
            print(f"✅ {package} - OK")
        else:
            print(f"❌ {package} - Missing")
            if install_name:
                missing_packages.append(install_name)
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        
        # Try to install from requirements.txt first
        try:
            print("Installing from requirements.txt...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ Successfully installed from requirements.txt")
        except subprocess.CalledProcessError:
            print("⚠️  Failed to install from requirements.txt, trying individual packages...")
            
            # Install individual packages
            for package in missing_packages:
                print(f"Installing {package}...")
                if install_package(package):
                    print(f"✅ {package} installed successfully")
                else:
                    print(f"❌ Failed to install {package}")
    
    # Final verification
    print("\n🔍 Final verification...")
    all_good = True
    for package, _ in test_packages.items():
        if check_package_installed(package):
            print(f"✅ {package}")
        else:
            print(f"❌ {package} - Still missing!")
            all_good = False
    
    if all_good:
        print("\n🎉 All dependencies are ready!")
        print("\nNext steps:")
        print("1. Start the server: python start_server.py")
        print("2. Run tests: python test_api_endpoints.py")
        print("3. Use Postman collection: PropMatch_API_Postman_Collection.json")
    else:
        print("\n❌ Some dependencies are still missing.")
        print("You may need to install them manually:")
        print("pip install fastapi uvicorn[standard] sqlalchemy psycopg2-binary httpx")

if __name__ == "__main__":
    main() 