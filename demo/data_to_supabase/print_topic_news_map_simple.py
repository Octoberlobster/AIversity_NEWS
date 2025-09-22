#!/usr/bin/env python3
"""簡單腳本：從 Supabase 的 topic_news_map 表抓取 'topic_id, story_id' 並印出

用法：
  python print_topic_news_map_simple.py
  python print_topic_news_map_simple.py --limit 10
  python print_topic_news_map_simple.py --table topic_news_map

此腳本會嘗試載入 Picture_generate_system/.env（若存在），否則使用預設 load_dotenv()
"""
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# 嘗試載入 Picture_generate_system/.env（與 complete_news_grouper 相同的邏輯）
here = Path(__file__).resolve()
candidates = [
    here.parent.parent.parent / 'Picture_generate_system' / '.env',
    here.parent.parent / 'Picture_generate_system' / '.env',
    here.parent.parent.parent / '.env',
]
loaded = False
for p in candidates:
    try:
        if p.exists():
            load_dotenv(p.as_posix())
            print(f"載入環境變數檔案: {p}")
            loaded = True
            break
    except Exception:
        continue

if not loaded:
    load_dotenv()
    print("載入環境變數（預設 load_dotenv）")

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print('錯誤：未找到 SUPABASE_URL 或 SUPABASE_KEY，請確認 .env 設定')
    sys.exit(1)

try:
    from supabase import create_client
except Exception as e:
    print('請先安裝 supabase-py 與 postgrest-py：pip install supabase-py postgrest-py')
    print(e)
    sys.exit(1)

parser = argparse.ArgumentParser(description='列印 topic_news_map (topic_id, story_id)')
parser.add_argument('--table', '-t', default='topic_news_map', help='資料表名稱，預設 topic_news_map')
parser.add_argument('--limit', '-n', type=int, default=None, help='限制筆數')
args = parser.parse_args()

client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_and_print(table_name, limit=None):
    try:
        q = client.table(table_name).select('topic_id, story_id')
        if limit:
            q = q.limit(limit)
        resp = q.execute()
        if getattr(resp, 'error', None):
            print(f"查詢失敗: {resp.error}")
            return
        rows = resp.data or []
        print(f"從 '{table_name}' 取得 {len(rows)} 筆資料")
        for i, r in enumerate(rows, 1):
            print(f"{i}. topic_id={r.get('topic_id')}  story_id={r.get('story_id')}")
    except Exception as e:
        print(f"執行查詢時發生錯誤: {e}")

if __name__ == '__main__':
    fetch_and_print(args.table, args.limit)
