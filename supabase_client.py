import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()  # for local development

_supabase: Client | None = None

def get_supabase() -> Client:
    """Lazy-load Supabase client so it doesn't crash on Vercel cold start"""
    global _supabase
    if _supabase is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in environment variables")
        _supabase = create_client(url, key)
    return _supabase