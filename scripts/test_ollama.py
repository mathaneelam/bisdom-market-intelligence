import asyncio
import sys
import os
import json
import time
import traceback
from openai import AsyncOpenAI

# Add parent directory to path to load app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.processors.ollama_processor import OllamaProcessor

async def test_single_model(model_name: str):
    print("-" * 60)
    print(f"Testing model: {model_name}")
    print("-" * 60)
    
    # Initialize a temporary processor or custom client to test this specific model
    api_key = settings.OLLAMA_API_KEY or "ollama"
    base_url = settings.OLLAMA_BASE_URL or "http://localhost:11434/v1"
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    
    # We will test the basic analyze_signal logic
    test_signal = (
        "IndiaMART renewal is a complete waste of money. We paid 1.5 lakhs last year "
        "and got nothing but fake buyers and spam inquiries. Avoid it."
    )
    
    from app.processors.ollama_processor import SYSTEM_PROMPT
    
    try:
        start_time = time.time()
        response = await client.chat.completions.create(
            model=model_name,
            max_tokens=512,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": test_signal},
            ],
        )
        elapsed = time.time() - start_time
        text = response.choices[0].message.content.strip()
        
        # Clean up code blocks if model wrapped JSON in them
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        data = json.loads(text.strip())
        print(f"SUCCESS: Model '{model_name}' responded in {elapsed:.2f} seconds!")
        print(json.dumps(data, indent=2))
        return True
    except json.JSONDecodeError as e:
        print(f"PARTIAL SUCCESS: Model '{model_name}' responded but output was not valid JSON.")
        print(f"Raw Output: {text}")
        return False
    except Exception as e:
        print(f"ERROR testing '{model_name}': {e}")
        return False

async def main():
    print("=" * 60)
    print("OLLAMA DUAL-MODEL DIAGNOSTIC")
    print("=" * 60)
    print(f"Base URL: {settings.OLLAMA_BASE_URL}")
    print(f"Configured Model in .env: {settings.OLLAMA_MODEL}")
    print("=" * 60)
    
    # 1. Test the configured model
    print(f"\n[1/3] Testing configured model from .env...")
    success = await test_single_model(settings.OLLAMA_MODEL)
    
    if not success:
        print("\n[2/3] Configured model failed. Retrying with available model 'gemma4:cloud'...")
        success = await test_single_model("gemma4:cloud")
        
    if not success:
        print("\n[3/3] Retrying with alternative available model 'glm-5.2:cloud'...")
        success = await test_single_model("glm-5.2:cloud")
        
    print("\n" + "=" * 60)
    if success:
        print("DIAGNOSTIC COMPLETED: At least one model worked successfully.")
    else:
        print("DIAGNOSTIC FAILED: None of the models were able to respond correctly.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
