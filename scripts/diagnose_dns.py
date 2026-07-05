import socket
import urllib.parse
import os
import sys

def mask_url(url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.password:
            netloc = f"{parsed.username}:****@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            parsed = parsed._replace(netloc=netloc)
        return urllib.parse.urlunparse(parsed)
    except Exception:
        return "[Invalid URL]"

def diagnose():
    print("=== DNS DIAGNOSTICS START ===", flush=True)
    
    # 1. Print current env DATABASE_URL (masked)
    db_url = os.environ.get("DATABASE_URL", "")
    print(f"DATABASE_URL env value: {mask_url(db_url) if db_url else 'NOT SET'}", flush=True)
    
    # 2. Print settings.DATABASE_URL (masked)
    try:
        # Append parent directory to sys.path to import app.config
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.config import settings
        print(f"app.config settings.DATABASE_URL: {mask_url(settings.DATABASE_URL)}", flush=True)
        target_url = settings.DATABASE_URL
    except Exception as e:
        print(f"Failed to import app.config: {e}", flush=True)
        target_url = db_url

    # 3. Parse hostname from target_url
    hostname = None
    if target_url:
        try:
            # Strip scheme if it is not standard for urlparse
            url_to_parse = target_url
            if url_to_parse.startswith("postgresql+asyncpg://"):
                url_to_parse = url_to_parse.replace("postgresql+asyncpg://", "http://", 1)
            elif url_to_parse.startswith("postgresql://"):
                url_to_parse = url_to_parse.replace("postgresql://", "http://", 1)
            elif url_to_parse.startswith("postgres://"):
                url_to_parse = url_to_parse.replace("postgres://", "http://", 1)
                
            parsed = urllib.parse.urlparse(url_to_parse)
            hostname = parsed.hostname
            print(f"Parsed Hostname to resolve: '{hostname}'", flush=True)
        except Exception as e:
            print(f"Failed to parse hostname from target_url: {e}", flush=True)
            
    # 4. Try resolving google.com (external DNS test)
    try:
        google_ips = socket.getaddrinfo("google.com", 80)
        print(f"Resolve 'google.com' (test external DNS) -> SUCCESS: {[ip[4][0] for ip in google_ips]}", flush=True)
    except Exception as e:
        print(f"Resolve 'google.com' (test external DNS) -> FAILED: {e}", flush=True)

    # 5. Try resolving target hostname
    if hostname:
        try:
            ips = socket.getaddrinfo(hostname, 5432)
            print(f"Resolve '{hostname}' -> SUCCESS: {[ip[4][0] for ip in ips]}", flush=True)
        except Exception as e:
            print(f"Resolve '{hostname}' -> FAILED: {e}", flush=True)
            
    # 6. Try resolving raw Neon host (hardcoded test)
    raw_neon = "ep-winter-hall-aokxtmqs-pooler.c-2.ap-southeast-1.aws.neon.tech"
    try:
        neon_ips = socket.getaddrinfo(raw_neon, 5432)
        print(f"Resolve '{raw_neon}' (hardcoded test) -> SUCCESS: {[ip[4][0] for ip in neon_ips]}", flush=True)
    except Exception as e:
        print(f"Resolve '{raw_neon}' (hardcoded test) -> FAILED: {e}", flush=True)
        
    print("=== DNS DIAGNOSTICS END ===", flush=True)

if __name__ == "__main__":
    diagnose()
