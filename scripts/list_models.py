"""List available OpenAI models."""

import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

load_dotenv()

def list_models():
    """List all available OpenAI models."""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not set")
        return
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        print("Fetching available models...\n")
        
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers=headers
        )
        response.raise_for_status()
        
        data = response.json()
        models = data.get("data", [])
        
        # Filter and categorize models
        gpt_models = []
        embedding_models = []
        other_models = []
        
        for model in models:
            model_id = model["id"]
            if "gpt" in model_id:
                gpt_models.append(model_id)
            elif "embedding" in model_id or "ada" in model_id:
                embedding_models.append(model_id)
            else:
                other_models.append(model_id)
        
        # Sort
        gpt_models.sort(reverse=True)
        
        # Display GPT models only
        print(f"GPT Models ({len(gpt_models)}):\n")
        for model in gpt_models:
            print(f"  {model}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    list_models()
