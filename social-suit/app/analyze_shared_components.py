#!/usr/bin/env python3
"""
Script to analyze the Social Suit and Sparkr codebases to identify potential shared components.

This script scans both codebases and identifies:
1. Common imports
2. Similar file names
3. Potential utility functions that could be shared
"""

import os
import re
import sys
from collections import defaultdict, Counter
from pathlib import Path

# Define the paths to the two projects
SOCIAL_SUIT_PATH = Path("social-suit")
SPARKR_PATH = Path("sparkr")
SHARED_PATH = Path("shared")

# File extensions to analyze
PYTHON_EXTENSIONS = [".py"]

# Patterns to identify potential shared components
AUTH_PATTERNS = [r"auth", r"login", r"jwt", r"token", r"password", r"credential"]
DB_PATTERNS = [r"database", r"db", r"model", r"orm", r"sqlalchemy", r"sqlmodel", r"session", r"connection"]
UTIL_PATTERNS = [r"util", r"helper", r"common", r"shared", r"tool", r"formatter", r"validator"]


def find_python_files(directory):
    """Find all Python files in the given directory."""
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in PYTHON_EXTENSIONS):
                python_files.append(os.path.join(root, file))
    return python_files


def extract_imports(file_path):
    """Extract import statements from a Python file."""
    imports = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Find all import statements
            import_lines = re.findall(r"^\s*(?:from|import)\s+[\w\.]+", content, re.MULTILINE)
            imports.extend(import_lines)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return imports


def analyze_file_content(file_path, patterns):
    """Analyze file content for specific patterns."""
    matches = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    matches.append(pattern)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return matches


def categorize_file(file_path):
    """Categorize a file based on its content and path."""
    categories = []
    
    # Check file path for category hints
    path_str = str(file_path).lower()
    if any(p in path_str for p in ["auth", "login", "jwt", "token"]):
        categories.append("auth")
    if any(p in path_str for p in ["db", "database", "model", "schema"]):
        categories.append("database")
    if any(p in path_str for p in ["util", "helper", "common"]):
        categories.append("utils")
    
    # Check file content for category patterns
    auth_matches = analyze_file_content(file_path, AUTH_PATTERNS)
    if auth_matches:
        categories.append("auth")
    
    db_matches = analyze_file_content(file_path, DB_PATTERNS)
    if db_matches:
        categories.append("database")
    
    util_matches = analyze_file_content(file_path, UTIL_PATTERNS)
    if util_matches:
        categories.append("utils")
    
    # Remove duplicates
    return list(set(categories))


def find_similar_files(social_suit_files, sparkr_files):
    """Find files with similar names or paths in both projects."""
    similar_files = []
    
    social_suit_basenames = [os.path.basename(f) for f in social_suit_files]
    sparkr_basenames = [os.path.basename(f) for f in sparkr_files]
    
    # Find files with the same basename
    for ss_file in social_suit_files:
        ss_basename = os.path.basename(ss_file)
        if ss_basename in sparkr_basenames:
            sparkr_file = sparkr_files[sparkr_basenames.index(ss_basename)]
            similar_files.append((ss_file, sparkr_file))
    
    return similar_files


def analyze_imports(social_suit_files, sparkr_files):
    """Analyze import statements to find common dependencies."""
    social_suit_imports = []
    sparkr_imports = []
    
    for file in social_suit_files:
        social_suit_imports.extend(extract_imports(file))
    
    for file in sparkr_files:
        sparkr_imports.extend(extract_imports(file))
    
    # Count occurrences of each import
    social_suit_import_counts = Counter(social_suit_imports)
    sparkr_import_counts = Counter(sparkr_imports)
    
    # Find common imports
    common_imports = set(social_suit_import_counts.keys()) & set(sparkr_import_counts.keys())
    
    return common_imports, social_suit_import_counts, sparkr_import_counts


def suggest_shared_components(social_suit_files, sparkr_files):
    """Suggest components that could be shared between the two projects."""
    shared_components = defaultdict(list)
    
    # Categorize files
    for file in social_suit_files:
        categories = categorize_file(file)
        for category in categories:
            shared_components[category].append(("social_suit", file))
    
    for file in sparkr_files:
        categories = categorize_file(file)
        for category in categories:
            shared_components[category].append(("sparkr", file))
    
    return shared_components


def main():
    # Check if the directories exist
    if not SOCIAL_SUIT_PATH.exists() or not SPARKR_PATH.exists():
        print(f"Error: One or both project directories do not exist.")
        print(f"Social Suit path: {SOCIAL_SUIT_PATH} (exists: {SOCIAL_SUIT_PATH.exists()})")
        print(f"Sparkr path: {SPARKR_PATH} (exists: {SPARKR_PATH.exists()})")
        sys.exit(1)
    
    print("Analyzing codebases for potential shared components...\n")
    
    # Find all Python files in both projects
    social_suit_files = find_python_files(SOCIAL_SUIT_PATH)
    sparkr_files = find_python_files(SPARKR_PATH)
    
    print(f"Found {len(social_suit_files)} Python files in Social Suit")
    print(f"Found {len(sparkr_files)} Python files in Sparkr\n")
    
    # Find files with similar names
    similar_files = find_similar_files(social_suit_files, sparkr_files)
    print(f"Found {len(similar_files)} files with similar names in both projects:")
    for ss_file, sp_file in similar_files:
        print(f"  - {os.path.basename(ss_file)}")
        print(f"    Social Suit: {ss_file}")
        print(f"    Sparkr: {sp_file}")
    print()
    
    # Analyze imports
    common_imports, ss_import_counts, sp_import_counts = analyze_imports(social_suit_files, sparkr_files)
    print(f"Found {len(common_imports)} common imports in both projects:")
    for imp in sorted(common_imports):
        print(f"  - {imp} (Social Suit: {ss_import_counts[imp]}, Sparkr: {sp_import_counts[imp]})")
    print()
    
    # Suggest shared components
    shared_components = suggest_shared_components(social_suit_files, sparkr_files)
    print("Suggested shared components:")
    for category, files in shared_components.items():
        social_suit_count = sum(1 for proj, _ in files if proj == "social_suit")
        sparkr_count = sum(1 for proj, _ in files if proj == "sparkr")
        
        if social_suit_count > 0 and sparkr_count > 0:
            print(f"\n{category.upper()} ({social_suit_count} in Social Suit, {sparkr_count} in Sparkr):")
            
            # Print Social Suit files
            print("  Social Suit files:")
            for proj, file in files:
                if proj == "social_suit":
                    print(f"    - {file}")
            
            # Print Sparkr files
            print("  Sparkr files:")
            for proj, file in files:
                if proj == "sparkr":
                    print(f"    - {file}")
    
    # Generate recommendations for shared library structure
    print("\nRecommended shared library structure:")
    for category in shared_components.keys():
        if category in ["auth", "database", "utils"]:
            print(f"  - shared/{category}/")
    
    print("\nNext steps:")
    print("1. Review the suggested shared components")
    print("2. Extract common functionality to the shared library")
    print("3. Update import paths in both projects")
    print("4. Test both projects to ensure they work correctly")


if __name__ == "__main__":
    main()