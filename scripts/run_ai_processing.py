import asyncio
import os
import sys

# Add parent directory to path to load app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.models import base as models_base
from app.scheduler import run_ai_scorer, run_pattern_matcher

async def main():
    print("Initializing Database Connection...")
    models_base.init_db(settings.DATABASE_URL)
    
    print("\nStarting processing of all unprocessed signals in database...")
    print("-" * 60)
    
    total_processed = 0
    batch_num = 1
    
    while True:
        print(f"\n--- Batch #{batch_num} ---")
        processed = await run_ai_scorer()
        if processed == 0:
            print("No more unprocessed signals found in database.")
            break
            
        total_processed += processed
        print(f"Batch #{batch_num} completed. Processed: {processed} signals. Running pattern matcher...")
        
        matched = await run_pattern_matcher()
        print(f"Pattern matcher linked {matched} signals in this batch.")
        
        batch_num += 1
        print("Waiting 2 seconds before the next batch...")
        await asyncio.sleep(2)
        
    print("\n" + "=" * 60)
    print(f"SUCCESS: AI processing complete! Total signals scored: {total_processed}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
