import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.ai_content import OpenRouterAI

ai = OpenRouterAI()

# Test content generation
print("Testing generate_content()...")
content = ai.generate_content("Explain Web3 in simple words")
print("Generated Content:", content)

# Test caption generation
print("\nTesting generate_caption()...")
caption = ai.generate_caption("Web3 trends")
print("Generated Caption:", caption)
