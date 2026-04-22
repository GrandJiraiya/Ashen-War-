import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

supabase: Client | None = None


def get_supabase() -> Client:
    global supabase
    if supabase is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("Missing Supabase environment variables")
        supabase = create_client(url, key)
    return supabase
