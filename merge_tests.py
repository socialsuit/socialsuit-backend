import os
import shutil
import sys

def merge_tests():
    """Merge unit_tests and edge_tests into the main tests directory"""
    # Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    unit_tests_dir = os.path.join(base_dir, 'services', 'unit_tests')
    edge_tests_dir = os.path.join(base_dir, 'services', 'edge_tests')
    tests_dir = os.path.join(base_dir, 'tests')
    unit_dir = os.path.join(tests_dir, 'unit')
    edge_dir = os.path.join(tests_dir, 'edge')
    integration_dir = os.path.join(tests_dir, 'integration')
    
    # Create directories if they don't exist
    for directory in [unit_dir, edge_dir, integration_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")
    
    # Copy unit tests
    if os.path.exists(unit_tests_dir):
        for filename in os.listdir(unit_tests_dir):
            if filename.endswith('.py'):
                source_path = os.path.join(unit_tests_dir, filename)
                dest_path = os.path.join(unit_dir, filename)
                
                # Read the file content and update imports if needed
                try:
                    with open(source_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                except UnicodeDecodeError:
                    # Try with a different encoding if utf-8 fails
                    with open(source_path, 'r', encoding='latin-1') as file:
                        content = file.read()
                
                # Update import paths if necessary
                content = content.replace(
                    'sys.path.append(os.path.dirname(os.path.dirname(__file__)))',
                    'sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))')
                
                # Write to new location
                with open(dest_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                print(f"Copied and updated: {filename} to {unit_dir}")
    else:
        print(f"Warning: {unit_tests_dir} does not exist")
    
    # Copy edge tests
    if os.path.exists(edge_tests_dir):
        for filename in os.listdir(edge_tests_dir):
            if filename.endswith('.py'):
                source_path = os.path.join(edge_tests_dir, filename)
                dest_path = os.path.join(edge_dir, filename)
                
                # Read the file content and update imports if needed
                try:
                    with open(source_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                except UnicodeDecodeError:
                    # Try with a different encoding if utf-8 fails
                    with open(source_path, 'r', encoding='latin-1') as file:
                        content = file.read()
                
                # Update import paths if necessary
                content = content.replace(
                    'sys.path.append(os.path.dirname(os.path.dirname(__file__)))',
                    'sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))')
                
                # Write to new location
                with open(dest_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                print(f"Copied and updated: {filename} to {edge_dir}")
    else:
        print(f"Warning: {edge_tests_dir} does not exist")
    
    # Create __init__.py files
    for directory in [unit_dir, edge_dir, integration_dir]:
        init_file = os.path.join(directory, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write('# Test package initialization')
            print(f"Created: {init_file}")
    
    print("\nTest migration completed. The tests are now organized as follows:")
    print(f"- Unit tests: {unit_dir}")
    print(f"- Edge tests: {edge_dir}")
    print(f"- Integration tests: {integration_dir}")
    print("\nNote: The original test directories have not been removed.")
    print("After verifying that the tests work correctly, you can remove the original directories.")

if __name__ == "__main__":
    merge_tests()