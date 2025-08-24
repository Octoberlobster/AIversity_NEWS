"""查詢 Supabase 中的 cleaned news 表，並列印前 5 筆的 article_id、article_title、content

用法：
  python test_show_cleaned_news.py [table_name]
若不指定 table_name，預設會使用 Config.SUPABASE_TABLES['comprehensive_reports']。

請先在 word_analysis_system/.env 設定 SUPABASE_URL 與 SUPABASE_KEY（或使用 SUPABASE_DB_URL 與 psycopg 直接查詢）
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("請先在 word_analysis_system/.env 設定 SUPABASE_URL 與 SUPABASE_KEY（或提供 SUPABASE_DB_URL 並使用 psycopg）")
    raise SystemExit(1)

try:
    from supabase import create_client
except Exception:
    print("請先安裝 supabase-py：pip install supabase-py postgrest-py")
    raise SystemExit(1)

# 決定要查詢哪個表
table_arg = sys.argv[1] if len(sys.argv) > 1 else None
try:
    from config import Config
    default_table = Config.get_supabase_table('comprehensive_reports')
except Exception:
    default_table = 'comprehensive_reports'

table = table_arg or default_table

print(f"嘗試連線到 Supabase: {SUPABASE_URL}")
client = create_client(SUPABASE_URL, SUPABASE_KEY)

print(f"查詢表：{table}，取前 5 筆（嘗試選取欄位 article_id, article_title, content）")
try:
    # 先嘗試只選指定欄位
    resp = client.table(table).select('article_id,article_title,content').limit(5).execute()
    if getattr(resp, 'error', None):
        print(f"查詢時發生錯誤（可能欄位不存在或權限問題）：{resp.error}")
        print("改為查詢全部欄位並顯示前 5 筆（降級顯示）")
        resp = client.table(table).select('*').limit(5).execute()

    rows = resp.data or []
    if not rows:
        print("查無資料（或無權限）")
        raise SystemExit(0)

    for i, r in enumerate(rows, start=1):
        article_id = r.get('article_id') if isinstance(r, dict) else None
        article_title = r.get('article_title') if isinstance(r, dict) else None
        content = r.get('content') if isinstance(r, dict) else None

        # 若欄位不存在，嘗試常見欄位名
        if article_id is None:
            article_id = r.get('id') if isinstance(r, dict) else None
        if article_title is None:
            article_title = r.get('title') if isinstance(r, dict) else None
        if content is None:
            # 嘗試 nested structures commonly used (e.g., comprehensive_report->versions->long)
            if isinstance(r, dict):
                cr = r.get('comprehensive_report') or r.get('report')
                if isinstance(cr, dict):
                    # try content in versions
                    versions = cr.get('versions') if isinstance(cr.get('versions'), dict) else None
                    if versions:
                        content = versions.get('long') or versions.get('short') or None
                    # or direct fields
                    if not content:
                        content = cr.get('content') or cr.get('summary') or None

        print(f"--- Row {i} ---")
        print(f"article_id   : {article_id}")
        print(f"article_title: {article_title}")
        # 截斷 content 以免輸出過長
        if content:
            snippet = content if len(content) <= 400 else content[:400] + '...'
            print(f"content (snippet): {snippet}")
        else:
            print("content       : <空或未找到欄位>")

except Exception as e:
    print("查詢時發生例外：", e)
    print("請確認 SUPABASE_URL、SUPABASE_KEY 是否正確，或表名是否存在。")
    raise
