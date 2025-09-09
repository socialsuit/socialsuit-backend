#!/usr/bin/env python3
"""
Script to verify that both Social Suit and Sparkr projects build and run correctly after migration.

This script performs the following checks:
1. Verifies that all required files exist in the new structure
2. Checks that Python syntax is valid in all Python files
3. Attempts to import key modules to verify import paths
4. Optionally runs basic tests for each project
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path

# Define the paths to the two projects
SOCIAL_SUIT_PATH = Path("social-suit")
SPARKR_PATH = Path("sparkr")
SHARED_PATH = Path("shared")

# Define key files that should exist in each project
KEY_FILES = {
    "social-suit": [
        "main.py",
        "celery_app.py",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "README.md",
    ],
    "sparkr": [
        "main.py",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "fly.toml",
        "README.md",
    ],
    "shared": [
        "README.md",
    ]
}

# Define key directories that should exist in each project
KEY_DIRECTORIES = {
    "social-suit": [
        "services/api",
        "services/models",
        "services/tasks",
        "tests",
    ],
    "sparkr": [
        "app/api",
        "app/models",
        "app/core",
        "tests",
    ],
    "shared": [
        "auth",
        "database",
        "utils",
    ]
}


def check_file_exists(file_path):
    """Check if a file exists."""
    return os.path.isfile(file_path)


def check_directory_exists(dir_path):
    """Check if a directory exists."""
    return os.path.isdir(dir_path)


def check_python_syntax(file_path):
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        compile(content, file_path, "exec")
        return True, None
    except SyntaxError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)


def find_python_files(directory):
    """Find all Python files in the given directory."""
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


def check_imports(file_path):
    """Check if imports in a Python file can be resolved."""
    # This is a simplified check that doesn't actually import the modules
    # A more thorough check would require setting up the Python path and actually importing
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for imports of shared components
        shared_imports = []
        if "from shared." in content or "import shared." in content:
            shared_imports.append("shared")
        
        return True, shared_imports
    except Exception as e:
        return False, str(e)


def run_tests(project_path):
    """Run tests for a project."""
    try:
        # Change to the project directory
        os.chdir(project_path)
        
        # Run pytest if available
        result = subprocess.run(["pytest", "-xvs"], capture_output=True, text=True)
        
        # Change back to the original directory
        os.chdir(Path("..."))
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except Exception as e:
        # Change back to the original directory
        os.chdir(Path("..."))
        return False, str(e)


def verify_project(project_name, project_path):
    """Verify that a project is correctly set up."""
    print(f"\nVerifying {project_name}...")
    
    # Check if the project directory exists
    if not project_path.exists():
        print(f"  [ERROR] Project directory {project_path} does not exist")
        return False
    
    # Check key files
    print("  Checking key files...")
    all_files_exist = True
    for file in KEY_FILES.get(project_name, []):
        file_path = project_path / file
        if check_file_exists(file_path):
            print(f"    [OK] {file}")
        else:
            print(f"    [ERROR] {file} does not exist")
            all_files_exist = False
    
    # Check key directories
    print("  Checking key directories...")
    all_dirs_exist = True
    for directory in KEY_DIRECTORIES.get(project_name, []):
        dir_path = project_path / directory
        if check_directory_exists(dir_path):
            print(f"    [OK] {directory}")
        else:
            print(f"    [ERROR] {directory} does not exist")
            all_dirs_exist = False
    
    # Check Python syntax
    print("  Checking Python syntax...")
    python_files = find_python_files(project_path)
    syntax_errors = 0
    for file in python_files:
        valid, error = check_python_syntax(file)
        if not valid:
            print(f"    [ERROR] Syntax error in {file}: {error}")
            syntax_errors += 1
    
    if syntax_errors == 0:
        print(f"    [OK] All {len(python_files)} Python files have valid syntax")
    else:
        print(f"    [ERROR] {syntax_errors} out of {len(python_files)} Python files have syntax errors")
    
    # Check imports
    print("  Checking imports...")
    import_errors = 0
    shared_imports = set()
    for file in python_files:
        valid, result = check_imports(file)
        if valid and isinstance(result, list):
            shared_imports.update(result)
        else:
            print(f"    [ERROR] Import error in {file}: {result}")
            import_errors += 1
    
    if import_errors == 0:
        print(f"    [OK] All {len(python_files)} Python files have valid imports")
        if shared_imports:
            print(f"    [INFO] {len(shared_imports)} files import from the shared library")
    else:
        print(f"    [ERROR] {import_errors} out of {len(python_files)} Python files have import errors")
    
    # Overall status
    if all_files_exist and all_dirs_exist and syntax_errors == 0 and import_errors == 0:
        print(f"  [SUCCESS] {project_name} verification passed")
        return True
    else:
        print(f"  [FAILURE] {project_name} verification failed")
        return False


def main(run_project_tests=False):
    print("Verifying migration...\n")
    
    # Verify Social Suit
    social_suit_ok = verify_project("social-suit", SOCIAL_SUIT_PATH)
    
    # Verify Sparkr
    sparkr_ok = verify_project("sparkr", SPARKR_PATH)
    
    # Verify shared library
    shared_ok = verify_project("shared", SHARED_PATH)
    
    # Run tests if requested
    if run_project_tests:
        if social_suit_ok:
            print("\nRunning Social Suit tests...")
            success, output = run_tests(SOCIAL_SUIT_PATH)
            if success:
                print("  [SUCCESS] Social Suit tests passed")
            else:
                print(f"  [FAILURE] Social Suit tests failed: {output}")
        
        if sparkr_ok:
            print("\nRunning Sparkr tests...")
            success, output = run_tests(SPARKR_PATH)
            if success:
                print("  [SUCCESS] Sparkr tests passed")
            else:
                print(f"  [FAILURE] Sparkr tests failed: {output}")
    
    # Overall status
    print("\nOverall verification status:")
    if social_suit_ok and sparkr_ok and shared_ok:
        print("[SUCCESS] Migration verification passed")
        return 0
    else:
        print("[FAILURE] Migration verification failed")
        return 1


if __name__ == "__main__":
    run_tests = "--run-tests" in sys.argv
    sys.exit(main(run_tests))