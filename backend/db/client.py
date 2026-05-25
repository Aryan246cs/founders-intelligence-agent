from __future__ import annotations

from supabase import create_client, Client
from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

_client = None


def get_supabase() -> Client:
    global _client
    if _client is None:
        _client = create_client(
            settings.supabase_url, settings.supabase_service_role_key
        )
        logger.info("Supabase client initialized")
    return _client
