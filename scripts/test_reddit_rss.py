import asyncio
import httpx
import feedparser
import urllib.parse

async def test_reddit_rss():
    keyword = "IndiaMART fake leads"
    encoded_kw = urllib.parse.quote(keyword)
    url = f"https://www.reddit.com/search.rss?q={encoded_kw}&sort=new"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                parsed = feedparser.parse(response.text)
                if parsed.entries:
                    entry = parsed.entries[0]
                    print("Available keys in RSS Entry:")
                    print(entry.keys())
                    print("\nDetailed values:")
                    print(f"Title:       {entry.get('title')}")
                    print(f"Link:        {entry.get('link')}")
                    print(f"Author:      {entry.get('author')}")
                    print(f"Published:   {entry.get('published')}")
                    print(f"Updated:     {entry.get('updated')}")
                    print(f"Summary/Content length: {len(entry.get('summary', ''))}")
                    print(f"Summary (first 300 chars):")
                    print(entry.get('summary', '')[:300])
            else:
                print(f"Failed with status: {response.status_code}")
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_reddit_rss())
