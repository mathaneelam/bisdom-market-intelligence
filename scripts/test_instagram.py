import asyncio
import logging
import sys
import os

# Set console output to UTF-8 to prevent emoji errors on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # Fallback for older python versions
        import sys, codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# Add parent directory to path to load app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.collectors.instagram import InstagramCollector

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_instagram")

async def main():
    print("=" * 60)
    print("INSTAGRAM SCRAPER DIAGNOSTIC")
    print("=" * 60)
    
    username = settings.INSTAGRAM_USERNAME
    if not username:
        print("ERROR: INSTAGRAM_USERNAME is not set in your .env file!")
        return
        
    print(f"Target Username: {username}")
    print("Attempting to connect to Instagram...")
    print("Note: If this is the first login from this machine, Instagram may send an SMS/Email checkpoint.")
    print("-" * 60)
    
    collector = InstagramCollector()
    
    try:
        signals = await collector.collect()
        
        print("\n" + "=" * 60)
        print("TEST STATUS")
        print("=" * 60)
        print(f"Total Signals Collected: {len(signals)}")
        
        if signals:
            print("\n--- SAMPLE POSTS ---")
            for i, signal in enumerate(signals[:5], 1):
                print(f"\n[{i}] Source: {signal['source_url']}")
                print(f"    Author: {signal['author']}")
                print(f"    Content (first 150 chars):")
                # Encode and decode using cp1252 ignore or just print if terminal supports
                content = signal['raw_content'][:150]
                try:
                    print(f"    {content}...")
                except UnicodeEncodeError:
                    clean_content = content.encode('ascii', errors='replace').decode('ascii')
                    print(f"    {clean_content}...")
        else:
            print("\nNo signals collected. Scraper returned 0 posts. (Check if login failed or hashtags had no recent posts).")
            
    except Exception as e:
        print(f"\nERROR RUNNING INSTAGRAM COLLECTOR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
