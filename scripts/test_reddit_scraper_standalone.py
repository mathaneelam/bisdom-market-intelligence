import asyncio
import httpx
import feedparser
import urllib.parse
import sys
import os

# Add parent directory to path to load app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.collectors.reddit import PAIN_PULSE_KEYWORDS, OPPORTUNITY_KEYWORDS

async def main():
    print("=" * 60)
    print("TESTING SINGLE-REQUEST OPTIMIZATION WITH BROWSER HEADERS")
    print("=" * 60)
    
    # Combine all keywords into one single list
    all_keywords = PAIN_PULSE_KEYWORDS + OPPORTUNITY_KEYWORDS
    
    # Format each keyword with double quotes for exact phrase matching
    formatted_kws = [f'"{kw}"' for kw in all_keywords]
    combined_query = " OR ".join(formatted_kws)
    encoded_query = urllib.parse.quote(combined_query)
    
    url = f"https://www.reddit.com/search.rss?q={encoded_query}&sort=new"
    
    # Using the standard browser user-agent that worked in the original script
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    # Wait 15 seconds to let any previous block cool down completely
    print("Waiting 15 seconds to clear previous rate limits...")
    await asyncio.sleep(15)
    
    print("\nSending SINGLE query to Reddit RSS...")
    print(f"URL: {url[:100]}... [truncated]")
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(url, headers=headers)
            print(f"HTTP Status Code: {response.status_code}")
            
            if response.status_code == 200:
                feed = feedparser.parse(response.text)
                print(f"SUCCESS: Collected {len(feed.entries)} posts in exactly 1 request!")
                
                if feed.entries:
                    print("\n--- SAMPLE POSTS ---")
                    for i, entry in enumerate(feed.entries[:3], 1):
                        title = entry.get("title", "")
                        summary = entry.get("summary", "")
                        link = entry.get("link", "")
                        
                        # Classify stream locally
                        post_text = f"{title} {summary}".lower()
                        is_opp = any(kw.lower() in post_text for kw in OPPORTUNITY_KEYWORDS)
                        stream = "opportunity_signal" if is_opp else "pain_pulse"
                        
                        print(f"\n[{i}] Stream: {stream}")
                        print(f"    Title: {title}")
                        print(f"    Link:  {link}")
                        print(f"    Text:  {summary[:120]}...")
            else:
                print(f"FAILURE: Reddit responded with status code {response.status_code}")
                print(f"Response headers: {dict(response.headers)}")
                
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
