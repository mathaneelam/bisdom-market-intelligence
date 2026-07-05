import asyncio
import sys
import os
import urllib.parse
import instaloader

# Add parent directory to path to load app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.models.base import init_db
from app.collectors.instagram_session_store import save_session_to_db

def create_session(session_id_val: str):
    username = settings.INSTAGRAM_USERNAME
    if not username:
        print("ERROR: INSTAGRAM_USERNAME is not set in your .env file!")
        return False
        
    print("=" * 60)
    print("MANUAL INSTAGRAM SESSION CREATOR (EXACT USER-AGENT)")
    print("=" * 60)
    print(f"Target Username: {username}")
    print("-" * 60)
    
    # Clean the session ID
    session_id_val = session_id_val.strip().strip('"').strip("'")
    
    try:
        decoded_sid = urllib.parse.unquote(session_id_val)
        if ":" in decoded_sid:
            user_id = decoded_sid.split(":")[0]
        else:
            user_id = session_id_val.split("%3A")[0]
            
        # Verify it's a numeric ID
        int(user_id)
        print(f"Extracted Numeric User ID: {user_id}")
    except Exception:
        print("WARNING: Could not parse numeric User ID from sessionid. We will try using '0'.")
        user_id = "0"
        
    L = instaloader.Instaloader()
    
    # Set context username so instaloader considers us logged in
    L.context.username = username
    
    # Enforce your exact Chrome User-Agent string from the console
    chrome_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
    L.context.user_agent = chrome_ua
    L.context._session.headers['User-Agent'] = chrome_ua
    
    # Manually inject the cookies into the instaloader session
    L.context._session.cookies.set('sessionid', session_id_val, domain='.instagram.com')
    L.context._session.cookies.set('ds_user_id', user_id, domain='.instagram.com')
    
    try:
        # Verify the session by fetching the profile
        print("Connecting to Instagram to verify session...")
        profile = instaloader.Profile.from_username(L.context, username)
        print(f"Session verified! Logged in as profile: {profile.username} (ID: {profile.userid})")
        
        # Save session to local file (for local dev runs)
        L.save_session_to_file()

        # Also push to the database so Railway/Render pick it up without a volume
        print("Pushing session to the database...")
        init_db(settings.DATABASE_URL)
        asyncio.run(save_session_to_db(L, username))

        print("\nSUCCESS: Instagram session created and saved successfully!")
        return True
        
    except Exception as e:
        print(f"\nERROR VERIFYING SESSION: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_session_manually.py <sessionid_cookie_value>")
    else:
        create_session(sys.argv[1])
