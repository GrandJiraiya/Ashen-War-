import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_supabase: Client | None = None

def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        # DEBUG PRINTS (will appear in Vercel logs)
        print("=== SUPABASE DEBUG ===")
        print("SUPABASE_URL present:", bool(url))
        print("SUPABASE_KEY present:", bool(key))
        if key:
            print("SUPABASE_KEY starts with:", key[:20] + "..." if len(key) > 20 else key)
        print("=====================")
        
        if not url or not key:
            raise ValueError(f"Missing Supabase env vars. URL={bool(url)}, KEY={bool(key)}")
        
        _supabase = create_client(url, key)
    return _supabase