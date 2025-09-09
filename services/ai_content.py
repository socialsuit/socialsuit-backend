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
    """Class for interacting with OpenRouter API to generate content using DeepSeek models with robust fallback logic"""
    
    def __init__(self):
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Fallback templates for different platforms
        self.fallback_templates = {
            "instagram": {
                "professional": "Excited to share our latest update with you! This represents our commitment to quality and innovation. #innovation #quality #{custom}",
                "casual": "Check this out! We thought you might like what we've been working on lately. #awesome #vibes #{custom}"
            },
            "twitter": {
                "professional": "We're proud to announce our latest development. Designed with our customers in mind. #innovation #{custom}",
                "casual": "Just dropped! Check out what we've been working on lately. Thoughts? #new #{custom}"
            }
        }
        
        # Default fallback template
        self.default_fallback = "Check out our latest update! We're constantly working to bring you the best experience. #innovation #quality #{custom}"
    
    @staticmethod
    def clean_caption(text: str) -> str:
        """Clean and format social media captions"""
        # Return early if text is None
        if text is None:
            return ""
            
        text = re.sub(r'\n+', ' ', text).strip()  # Remove extra new lines
        hashtags = re.findall(r"#\w+", text)      # Extract hashtags
        text = re.sub(r"#\w+", '', text).strip()  # Remove hashtags from main text
        text += " " + " ".join(hashtags[:5])      # Append only first 5 hashtags
        return text

    def generate_content(self, prompt: str) -> Dict[str, Union[str, Dict]]:
        """Generate general content using OpenRouter API with fallback logic"""
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
                json=data,
                timeout=20.0  # Reduced timeout for better UX
            )
            result = response.json()
            return {
                "generated": result["choices"][0]["message"]["content"],
                "raw_response": result
            }
        except requests.Timeout:
            return {"error": "API request timed out", "fallback": True}
        except Exception as e:
            return {"error": str(e), "fallback": True}

    def get_fallback_caption(self, topic: str, platform: str = "instagram", tone: str = "professional") -> str:
        """Generate a fallback caption when the API is unavailable"""
        # Extract a relevant keyword from the topic for the custom hashtag
        words = topic.lower().split()
        # Filter out common words
        common_words = {"the", "and", "a", "an", "in", "on", "at", "to", "for", "with"}
        keywords = [word for word in words if word not in common_words and len(word) > 3]
        
        # Use the first meaningful keyword or a default
        custom_hashtag = keywords[0] if keywords else "update"
        
        # Get the appropriate template based on platform and tone
        if platform.lower() in self.fallback_templates:
            platform_templates = self.fallback_templates[platform.lower()]
            if tone.lower() in platform_templates:
                template = platform_templates[tone.lower()]
            else:
                # Default to professional tone if specified tone not found
                template = platform_templates["professional"]
        else:
            # Use default fallback for unsupported platforms
            template = self.default_fallback
        
        # Replace the custom hashtag placeholder
        return template.replace("{custom}", custom_hashtag)

    def generate_caption(self, topic: str, platform: str = "instagram", tone: str = "professional") -> str:
        """Generate social media caption with proper formatting and fallback logic"""
        prompt = f"Generate an engaging social media post about {topic} with 4-5 relevant hashtags for {platform} in a {tone} tone."
        
        data = {
            "model": "deepseek/deepseek-chat:free",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8
        }

        try:
            response = requests.post(self.base_url, json=data, headers=self.headers, timeout=20.0)
            response_data = response.json()
            
            if "choices" in response_data and response_data["choices"]:
                raw_caption = response_data["choices"][0]["message"]["content"].strip()
                cleaned = self.clean_caption(raw_caption)
                self.save_to_history(topic, cleaned, False)  # Not a fallback
                return cleaned
            
            # If API returned invalid response, use fallback
            fallback_caption = self.get_fallback_caption(topic, platform, tone)
            self.save_to_history(topic, fallback_caption, True)  # Mark as fallback
            return fallback_caption
            
        except (requests.Timeout, requests.RequestException) as e:
            # Handle timeout or connection errors with fallback
            fallback_caption = self.get_fallback_caption(topic, platform, tone)
            self.save_to_history(topic, fallback_caption, True)  # Mark as fallback
            return fallback_caption
            
        except Exception as e:
            fallback_caption = self.get_fallback_caption(topic, platform, tone)
            self.save_to_history(topic, fallback_caption, True)  # Mark as fallback
            return fallback_caption

    def save_to_history(self, topic: str, caption: str, is_fallback: bool = False):
        """Save generated caption to history log file"""
        fallback_marker = "[FALLBACK] " if is_fallback else ""
        with open("caption_history.log", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} | {fallback_marker}{topic} | {caption}\n")

# Example usage
if __name__ == "__main__":
    ai = OpenRouterAI()
    
    # Test general content generation
    content_result = ai.generate_content("Explain blockchain in simple words")
    print("Generated Content:", content_result.get("generated", "Error"))

    # Test social media caption generation (also logs the result)
    caption = ai.generate_caption("Crypto trading strategies")
    print("Generated Caption:", caption)
