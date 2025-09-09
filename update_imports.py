#!/usr/bin/env python3
"""
Script to update import paths in both Social Suit and Sparkr projects after migration.  

This script scans Python files in both projects and updates import statements
to reference the new shared library where appropriate.
"""

import os
import re

def update_sparkr_imports(directory):
    """Update import statements from 'app.' to 'sparkr.app.' in Python files"""
    pattern = re.compile(r'from app\.|import app\.')
    replacement = lambda match: match.group(0).replace('app.', 'sparkr.app.')
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check if the file contains imports to update
                    if pattern.search(content):
                        updated_content = pattern.sub(replacement, content)
                        
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(updated_content)
                        
                        print(f"Updated imports in {file_path}")
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    sparkr_dir = r"C:\Users\hhp\social_suit\sparkr"
    update_sparkr_imports(sparkr_dir)
    print("Import path updates completed.")