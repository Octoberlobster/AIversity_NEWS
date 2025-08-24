"""列印 Supabase single_news 的 story_id 與 long（檢查用）

用法:
  python print_single_news_fields.py [limit]

請在 Picture_generate_system/.env 設定 SUPABASE_URL 與 SUPABASE_KEY
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

client = create_client(SUPABASE_URL, SUPABASE_KEY)
print(f"連線到 Supabase: {SUPABASE_URL}，取前 {LIMIT} 筆 single_news 的 story_id,long")

resp = client.table('single_news').select('story_id,long').limit(LIMIT).execute()
if getattr(resp, 'error', None):
    print("嘗試選取 (story_id,long) 發生錯誤，改為 select('*') 並降級處理：", resp.error)
    resp = client.table('single_news').select('*').limit(LIMIT).execute()

rows = resp.data or []
if not rows:
    print("未取得資料，請確認表名/權限")
    raise SystemExit(0)

for idx, r in enumerate(rows, start=1):
    if not isinstance(r, dict):
        print(f"Row {idx}: 非典型格式，跳過: {r}")
        continue
    story_id = r.get('story_id') or r.get('id') or r.get('storyId')
    long = r.get('long')
    print('---')
    print(f"#{idx}")
    print(f"story_id: {story_id}")
    if long is None:
        print("long: <未找到>")
    else:
        snippet = long if len(long) <= 800 else long[:800] + '...'
        print(f"long (snippet): {snippet}")

print(f"完成，共輸出 {len(rows)} 筆（最大 {LIMIT}）")
