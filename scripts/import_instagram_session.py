import asyncio
import sys
import os
import instaloader

# Add parent directory to path to load app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.models.base import init_db
from app.collectors.instagram_session_store import save_session_to_db

def import_session():
    username = settings.INSTAGRAM_USERNAME
    if not username:
        print("ERROR: INSTAGRAM_USERNAME is not set in your .env file!")
        return False
        
    print("=" * 60)
    print("INSTAGRAM CHROME SESSION IMPORTER")
    print("=" * 60)
    print(f"Target Username: {username}")
    print("Reading active Instagram session from Chrome browser cookies...")
    print("Note: Please make sure you are actively logged in to Instagram on Google Chrome.")
    print("-" * 60)
    
    L = instaloader.Instaloader()
    
    try:
        # Load cookies from Chrome
        L.context.load_cookies(browser='chrome')
        
        # Test if the session is valid by fetching a profile
        # This checks if the cookies loaded actually log us in
        print("Testing session by fetching profile metadata...")
        profile = instaloader.Profile.from_username(L.context, username)
        print(f"Session verification: Logged in as profile ID {profile.userid}")
        
        # Save session to local file (for local dev runs)
        print(f"Saving session file for user '{username}'...")
        L.save_session_to_file(username)

        # Also push to the database so Railway/Render pick it up without a volume
        print("Pushing session to the database...")
        init_db(settings.DATABASE_URL)
        asyncio.run(save_session_to_db(L, username))

        print("\n✅ SUCCESS: Instagram session imported and saved successfully!")
        print("Our scraper can now bypass all passwords and login checks!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR IMPORTING SESSION: {e}")
        print("\nTroubleshooting tips:")
        print("1. Open Chrome and go to Instagram.com. Confirm you are logged in as 'evvi.clothing'.")
        print("2. Close Chrome completely before running this script, as Chrome sometimes locks the cookie database while open.")
        print("3. Ensure your profile is public/accessible.")
        return False

if __name__ == "__main__":
    import_session()
