import google.generativeai as genai
import asyncio
import os
import sys

# Add parent directory to path to load config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import settings

# Configure the API key
genai.configure(api_key=settings.GEMINI_API_KEY)

# ==========================================
# HANDS-ON EXERCISE: PROMPT ENGINEERING
# ==========================================

# 1. THE SYSTEM PROMPT (The Rules)
# This is where you program the AI using plain English.
# Try changing this to make the AI act like a pirate, or to only return JSON!
SYSTEM_PROMPT = """
You are a helpful assistant.
"""

# 2. THE USER INPUT (The Data)
# This is the raw data we scraped from the internet.
USER_INPUT = "IndiaMART charged me 50,000 rupees and I got zero genuine buyers. All leads were fake!"

async def run_ai():
    print("==========================================")
    print(f"Sending data to AI...\nRaw Input: {USER_INPUT}")
    print("==========================================\n")
    
    # We initialize the LLM and pass it your System Prompt
    model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)
    
    # We ask the LLM to generate a response based on the input
    response = await model.generate_content_async(USER_INPUT)
    
    print("AI Output:")
    print(response.text)
    print("\n==========================================")

if __name__ == "__main__":
    asyncio.run(run_ai())
