import os
import re
import sys

def update_social_suit_imports(directory):
    """Update import paths in Python files from 'services.' to 'social_suit.app.services.'"""
    pattern = re.compile(r'from\s+services\.(.*?)\s+import|import\s+services\.(.*?)\s+')
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if the file contains imports from 'services'
                if pattern.search(content):
                    print(f"Updating imports in {file_path}")
                    
                    # Replace 'from services.' with 'from social_suit.app.services.'
                    updated_content = re.sub(
                        r'from\s+services\.', 
                        'from social_suit.app.services.', 
                        content
                    )
                    
                    # Replace 'import services.' with 'import social_suit.app.services.'
                    updated_content = re.sub(
                        r'import\s+services\.', 
                        'import social_suit.app.services.', 
                        updated_content
                    )
                    
                    # Write the updated content back to the file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)

if __name__ == "__main__":
    # Get the directory to update from command line argument or use default
    directory = sys.argv[1] if len(sys.argv) > 1 else "social-suit"
    update_social_suit_imports(directory)
    print(f"Finished updating import paths in {directory}")