"""輕量 Supabase 客戶端封裝，用於讀寫新聞與關鍵字結果。

要求環境變數：
- SUPABASE_URL
- SUPABASE_KEY

用法：
from supabase_client import SupabaseClient
client = SupabaseClient()
rows = client.fetch_table('comprehensive_reports')
client.insert_row('keyword_explanations', {'story_index': 1, 'keywords': [...]})
"""
from typing import Any, List, Dict
import os
from dotenv import load_dotenv

load_dotenv()

try:
    from supabase import create_client
except Exception:
    create_client = None

class SupabaseClient:
    def __init__(self, url: str = None, key: str = None):
        self.url = url or os.getenv('SUPABASE_URL')
        self.key = key or os.getenv('SUPABASE_KEY')
        if not self.url or not self.key:
            raise EnvironmentError('SUPABASE_URL or SUPABASE_KEY not found in environment')
        if create_client is None:
            raise ImportError('supabase package not installed')
        self.client = create_client(self.url, self.key)

    def fetch_table(self, table: str) -> List[Dict[str, Any]]:
        """Fetch all rows from a table. Returns list of dicts."""
        resp = self.client.table(table).select('*').execute()
        if resp.error:
            raise RuntimeError(f"Supabase fetch error: {resp.error}")
        return resp.data or []

    def insert_row(self, table: str, row: Dict[str, Any]) -> Dict[str, Any]:
        resp = self.client.table(table).insert(row).execute()
        if resp.error:
            raise RuntimeError(f"Supabase insert error: {resp.error}")
        return resp.data

    def upsert_row(self, table: str, row: Dict[str, Any], on_conflict: str = None):
        # upsert: insert or update
        if on_conflict:
            resp = self.client.table(table).upsert(row, on_conflict=on_conflict).execute()
        else:
            resp = self.client.table(table).upsert(row).execute()
        if getattr(resp, 'error', None):
            raise RuntimeError(f"Supabase upsert error: {resp.error}")
        return resp.data
