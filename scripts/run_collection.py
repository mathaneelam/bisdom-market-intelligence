import asyncio
import os
import sys

# Add parent directory to path to load app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.models import base as models_base
from app.scheduler import run_reddit_collector, run_instagram_collector, run_ai_scorer, run_pattern_matcher

async def main():
    print("Initializing Database Connection...")
    models_base.init_db(settings.DATABASE_URL)
    
    print("\n[1/4] Running Reddit Collector (Database Insert)...")
    await run_reddit_collector()
    
    print("\n[2/4] Running Instagram Collector (Database Insert)...")
    await run_instagram_collector()
    
    print("\n[3/4] Running AI Scorer (Ollama Processing)...")
    processed_count = await run_ai_scorer()
    print(f"AI Scorer processed {processed_count} signals.")
    
    print("\n[4/4] Running Pattern Matcher...")
    matched_count = await run_pattern_matcher()
    print(f"Pattern Matcher linked {matched_count} signals.")
    
    print("\nSUCCESS: Database populated and signals processed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
