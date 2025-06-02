import os
import re
import requests
from dotenv import load_dotenv
from typing import Dict, Union
from datetime import datetime

# Load environment variables
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

class OpenRouterAI:
    def __init__(self):
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
    
    @staticmethod
    def clean_caption(text: str) -> str:
        """Clean and format social media captions"""
        text = re.sub(r'\n+', ' ', text).strip()  # Remove extra new lines
        hashtags = re.findall(r"#\w+", text)      # Extract hashtags
        text = re.sub(r"#\w+", '', text).strip()  # Remove hashtags from main text
        text += " " + " ".join(hashtags[:5])      # Append only first 5 hashtags
        return text

    def generate_content(self, prompt: str) -> Dict[str, Union[str, Dict]]:
        """Generate general content using OpenRouter API"""
        data = {
            "model": "deepseek/deepseek-chat:free",
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }

        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=data
            )
            result = response.json()
            return {
                "generated": result["choices"][0]["message"]["content"],
                "raw_response": result
            }
        except Exception as e:
            return {"error": str(e)}

    def generate_caption(self, topic: str) -> str:
        """Generate social media caption with proper formatting"""
        prompt = f"Generate an engaging social media post about {topic} with 4-5 relevant hashtags."
        
        data = {
            "model": "deepseek/deepseek-chat:free",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8
        }

        try:
            response = requests.post(self.base_url, json=data, headers=self.headers)
            response_data = response.json()
            
            if "choices" in response_data and response_data["choices"]:
                raw_caption = response_data["choices"][0]["message"]["content"].strip()
                cleaned = self.clean_caption(raw_caption)
                self.save_to_history(topic, cleaned)  # ✅ Logging history here
                return cleaned
            return "❌ Error: API did not return a valid caption"
        except Exception as e:
            return f"❌ API Error: {str(e)}"

    def save_to_history(self, topic: str, caption: str):
        """Save generated caption to history log file"""
        with open("caption_history.log", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} | {topic} | {caption}\n")

# Example usage
if __name__ == "__main__":
    ai = OpenRouterAI()
    
    # Test general content generation
    content_result = ai.generate_content("Explain blockchain in simple words")
    print("Generated Content:", content_result.get("generated", "Error"))

    # Test social media caption generation (also logs the result)
    caption = ai.generate_caption("Crypto trading strategies")
    print("Generated Caption:", caption)
