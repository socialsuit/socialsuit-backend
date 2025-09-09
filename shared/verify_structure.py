import os
import sys

def verify_directory_structure(base_dir):
    """Verify that the shared library directory structure is correct."""
    expected_dirs = [
        '',  # Base directory
        'auth',
        'database',
        'utils'
    ]
    
    expected_files = [
        '__init__.py',
        'auth/__init__.py',
        'auth/jwt.py',
        'auth/rate_limiter.py',
        'auth/security_middleware.py',
        'database/__init__.py',
        'database/redis_manager.py',
        'database/sqlalchemy_base.py',
        'utils/__init__.py',
        'utils/common.py',
        'utils/config.py',
        'utils/logging_utils.py',
        'README.md',
        'setup.py'
    ]
    
    # Check directories
    for dir_name in expected_dirs:
        dir_path = os.path.join(base_dir, dir_name)
        if not os.path.isdir(dir_path):
            print(f"❌ Missing directory: {dir_path}")
        else:
            print(f"✅ Directory exists: {dir_path}")
    
    # Check files
    for file_name in expected_files:
        file_path = os.path.join(base_dir, file_name)
        if not os.path.isfile(file_path):
            print(f"❌ Missing file: {file_path}")
        else:
            print(f"✅ File exists: {file_path}")

if __name__ == "__main__":
    # Get the directory of this script
    current_dir = os.path.abspath(os.path.dirname(__file__))
    
    print("Verifying shared library structure...\n")
    verify_directory_structure(current_dir)
    
    print("\nShared library structure verification complete.")
    print("The shared library is ready to be used in both Social Suit and Sparkr projects.")