"""從 Supabase 撈取 single_news，生成圖片並將 base64 圖片與描述寫回 generated_image 表

用法：
  python generate_from_supabase.py [limit]

需求：在 Picture_generate_system/.env 設定 SUPABASE_URL 與 SUPABASE_KEY，並設定 GEMINI_API_KEY
安裝套件：pip install supabase-py postgrest-py python-dotenv google-genai pillow
若要直接使用 DB URL，可改用 SUPABASE_DB_URL 與 psycopg（此腳本目前使用 supabase REST）
"""
import os
import sys
import time
import base64
from dotenv import load_dotenv

# 確保能 import core
_this_dir = os.path.dirname(__file__)
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)

try:
    from generate_picture import core
except Exception:
    # 嘗試把父目錄加入 path
    parent = os.path.dirname(_this_dir)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    from generate_picture import core

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("請在 Picture_generate_system/.env 設定 SUPABASE_URL 與 SUPABASE_KEY（或使用 SUPABASE_DB_URL 並改寫腳本）")
    raise SystemExit(1)
if not GEMINI_API_KEY:
    print("請在 Picture_generate_system/.env 設定 GEMINI_API_KEY")
    raise SystemExit(1)

try:
    from supabase import create_client
except Exception:
    print("請先安裝 supabase-py：pip install supabase-py postgrest-py")
    raise SystemExit(1)

try:
    from google import genai
except Exception:
    print("請先安裝 google genai SDK（根據專案需求）並設定 GEMINI_API_KEY")
    raise SystemExit(1)

# 建立 Supabase 與 Gemini client
sb = create_client(SUPABASE_URL, SUPABASE_KEY)
# gemini client will be created inside core._gen_image_bytes_with_retry expects genai.Client passed

LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 150

MODEL_ID = getattr(core, 'DEFAULT_MODEL_ID', None) or 'gemini-2.0-flash-preview-image-generation'
RETRY_TIMES = 3
SLEEP_BETWEEN = 0.6

print(f"Connecting to Supabase: {SUPABASE_URL}")
print(f"Fetching up to {LIMIT} rows from table 'single_news'...")

# 先嘗試選取常見欄位
resp = sb.table('single_news').select('story_id,news_title,long').limit(LIMIT).execute()
if getattr(resp, 'error', None):
    print("嘗試選取 (story_id,news_title,long) 發生錯誤，改為 select('*') 以檢視欄位：", resp.error)
    resp = sb.table('single_news').select('*').limit(LIMIT).execute()

rows = resp.data or []
if not rows:
    print("未取得任何 row，請確認表名或權限")
    raise SystemExit(0)

# 初始化 Gemini client
gen_client = genai.Client()

insert_count = 0
fail_count = 0

for i, r in enumerate(rows, start=1):
    # 支援不同欄位名稱的降級邏輯
    if isinstance(r, dict):
        story_id = r.get('story_id') or r.get('id') or r.get('storyId')
        title = r.get('news_title') or r.get('title') or r.get('article_title') or r.get('headline') or ''
        # 嘗試常見欄位：long 或 content 或 comprehensive_report.versions.long
        content = r.get('long') or r.get('content') or None
        if content is None:
            cr = r.get('comprehensive_report') or r.get('report')
            if isinstance(cr, dict):
                versions = cr.get('versions')
                if isinstance(versions, dict):
                    content = versions.get('long') or versions.get('short')
                if not content:
                    content = cr.get('long') or cr.get('content')
    else:
        story_id = None
        title = ''
        content = None

    print(f"Row {i}: story_id={story_id} news_title={title[:40]}")
    if not title and content:
        # 從 content 取前段作為 title 的 fallback
        title = (content[:40] + '...') if len(content) > 40 else content

    prompt = core._prompt_photoreal_no_text(title or '', content or '', category='')

    img_bytes = core._gen_image_bytes_with_retry(gen_client, prompt, MODEL_ID, RETRY_TIMES, SLEEP_BETWEEN)
    if not img_bytes:
        print(f"第 {i} 筆（story_id={story_id}）生成失敗，跳過")
        fail_count += 1
        continue

    # --- 同步儲存為本機 PNG（供後續解碼比對） ---
    save_dir = os.path.join(os.path.dirname(__file__), 'saved_pngs')
    os.makedirs(save_dir, exist_ok=True)
    out_name = f"{story_id if story_id is not None else 'noid'}_{i}.png"
    out_path = os.path.join(save_dir, out_name)
    try:
        core._save_png(img_bytes, out_path)
        print(f"已在本機儲存 PNG: {out_path}")
    except Exception as e:
        print(f"儲存本機 PNG 失敗: {e}")

    # 產生描述（短）
    description = core._generate_image_description(title or '', content or '', '')

    # base64 encode
    b64 = base64.b64encode(img_bytes).decode('ascii')

    payload = {
    'story_id': story_id,
    'image': b64,
    'description': description,
    }

    # 嘗試 upsert（若有 primary key conflict，請依據實際 schema 調整）
    try:
        ins = sb.table('generated_image').insert(payload).execute()
        if getattr(ins, 'error', None):
            print(f"寫入 generated_image 發生錯誤: {ins.error}")
            fail_count += 1
        else:
            insert_count += 1
            print(f"已寫入 generated_image (story_id={story_id})")
            # 避免速率限制
            time.sleep(0.5)
    except Exception as e:
        print(f"寫入例外: {e}")
        fail_count += 1

print(f"完成：寫入 {insert_count} 筆，失敗 {fail_count} 筆")
