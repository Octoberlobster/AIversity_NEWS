"""測試：從 Supabase 讀取 single_news 並印出 story_id / title / long

用法：
  python test_fetch_single_news.py [limit]

環境變數：請於 Picture_generate_system/.env 設定 SUPABASE_URL 與 SUPABASE_KEY
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("請先在 Picture_generate_system/.env 設定 SUPABASE_URL 與 SUPABASE_KEY")
    raise SystemExit(1)

try:
    from supabase import create_client
except Exception:
    print("請先安裝 supabase-py：pip install supabase-py postgrest-py")
    raise SystemExit(1)

LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 10

print(f"連線到 Supabase: {SUPABASE_URL}")
client = create_client(SUPABASE_URL, SUPABASE_KEY)

print(f"從表 single_news 取前 {LIMIT} 筆資料（優先取 story_id,news_title,long）...")
resp = client.table('single_news').select('story_id,news_title,long').limit(LIMIT).execute()
if getattr(resp, 'error', None):
    print("嘗試選取 (story_id,title,long) 發生錯誤，改為 select('*') 並降級處理：", resp.error)
    resp = client.table('single_news').select('*').limit(LIMIT).execute()

rows = resp.data or []
if not rows:
    print("未取得任何資料，請確認表名或權限")
    raise SystemExit(0)

for idx, r in enumerate(rows, start=1):
    if not isinstance(r, dict):
        print(f"Row {idx}: 非典型回傳格式: {r}")
        continue
    story_id = r.get('story_id') or r.get('id') or r.get('storyId')
    title = r.get('news_title') or r.get('title') or r.get('article_title') or r.get('headline') or ''
    long = r.get('long') or r.get('content') or None
    # 嘗試 nested fallback
    if long is None:
        cr = r.get('comprehensive_report') or r.get('report')
        if isinstance(cr, dict):
            versions = cr.get('versions') if isinstance(cr.get('versions'), dict) else None
            if versions:
                long = versions.get('long') or versions.get('short')
            if not long:
                long = cr.get('long') or cr.get('content')

    print('---')
    print(f"#{idx}")
    print(f"story_id: {story_id}")
    print(f"news_title   : {title}")
    if long:
        snippet = long if len(long) <= 500 else long[:500] + '...'
        print(f"long (snippet): {snippet}")
    else:
        print("long    : <未找到或為空>")

print(f"完成，共輸出 {len(rows)} 筆（最大 {LIMIT}）")
