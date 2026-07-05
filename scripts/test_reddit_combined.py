import asyncio
import httpx
import feedparser
import urllib.parse

async def test_reddit_combined():
    # Broader keywords to ensure we find matching posts
    keywords = [
        'IndiaMART',
        '"sourcing problem"',
        '"WhatsApp chaos"',
        '"supplier fraud"',
        '"garment manufacturer"',
        '"textile supplier"'
    ]
    
    combined_query = " OR ".join(keywords)
    encoded_query = urllib.parse.quote(combined_query)
    url = f"https://www.reddit.com/search.rss?q={encoded_query}&sort=new"
    
    headers = {
        "User-Agent": "windows:bisdom-market-intel:v1.0.0 (by /u/bisdom_intel_bot)"
    }
    
    print(f"Combined Query: {combined_query}")
    print(f"Fetching from: {url}")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url, headers=headers)
            print(f"HTTP Status Code: {response.status_code}")
            
            if response.status_code == 200:
                parsed = feedparser.parse(response.text)
                print(f"SUCCESS: Collected {len(parsed.entries)} posts in a single combined query!")
                if parsed.entries:
                    entry = parsed.entries[0]
                    print("\n--- SAMPLE POST ---")
                    print(f"Title:     {entry.get('title')}")
                    print(f"Link:      {entry.get('link')}")
                    print(f"Author:    {entry.get('author')}")
                    print(f"Published: {entry.get('published')}")
                    print(f"Summary (first 250 chars):")
                    print(entry.get('summary', '')[:250])
            else:
                print(f"FAILURE: Status code {response.status_code}")
                
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_reddit_combined())
