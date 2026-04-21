import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

_supabase: Client | None = None


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip().strip('"').strip("'")
    return value or None


def get_supabase() -> Client:
    """Lazy-load Supabase client with clearer validation for Vercel env vars."""
    global _supabase
    if _supabase is not None:
        return _supabase

    url = _clean(os.getenv("SUPABASE_URL"))
    key = (
        _clean(os.getenv("SUPABASE_KEY"))
        or _clean(os.getenv("SUPABASE_ANON_KEY"))
        or _clean(os.getenv("SUPABASE_PUBLISHABLE_KEY"))
    )

    if not url or not key:
        raise ValueError(
            "Missing Supabase env vars. Set SUPABASE_URL and SUPABASE_KEY "
            "(or SUPABASE_ANON_KEY / SUPABASE_PUBLISHABLE_KEY)."
        )

    if "supabase.com/dashboard" in url or ".supabase.co" not in url:
        raise ValueError(
            "SUPABASE_URL must be your project API URL like "
            "https://<project-ref>.supabase.co, not the dashboard URL."
        )

    _supabase = create_client(url, key)
    return _supabase
