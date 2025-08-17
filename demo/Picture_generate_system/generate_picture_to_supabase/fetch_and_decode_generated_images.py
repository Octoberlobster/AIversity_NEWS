"""從 Supabase 的 generated_image 表讀取 story_id 與 image(base64)，解碼並存成 PNG

用法:
  python fetch_and_decode_generated_images.py [limit]

請在 Picture_generate_system/.env 設定 SUPABASE_URL 與 SUPABASE_KEY
"""
import os
import sys
import base64
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

LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 100

client = create_client(SUPABASE_URL, SUPABASE_KEY)
print(f"連線到 Supabase: {SUPABASE_URL}，讀取最多 {LIMIT} 筆 generated_image")

resp = client.table('generated_image').select('story_id,image').limit(LIMIT).execute()
if getattr(resp, 'error', None):
    print("查詢 generated_image 時發生錯誤：", resp.error)
    raise SystemExit(1)

rows = resp.data or []
if not rows:
    print("未取得任何 generated_image 資料。")
    raise SystemExit(0)

out_dir = os.path.join(os.path.dirname(__file__), 'retrieved_pngs')
os.makedirs(out_dir, exist_ok=True)

counts = {}

for idx, r in enumerate(rows, start=1):
    if not isinstance(r, dict):
        print(f"Row {idx}: 非典型資料格式，跳過: {r}")
        continue
    story_id = r.get('story_id') or r.get('id') or f'noid_{idx}'
    b64 = r.get('image')
    if not b64:
        print(f"Row {idx} (story_id={story_id}): image 欄位為空，跳過")
        continue
    # 若 b64 是 data URL 'data:image/png;base64,...'，去除前綴
    if isinstance(b64, str) and b64.startswith('data:'):
        try:
            b64 = b64.split(',', 1)[1]
        except Exception:
            pass
    try:
        img_bytes = base64.b64decode(b64)
    except Exception as e:
        print(f"Row {idx} (story_id={story_id}): base64 解碼失敗: {e}")
        continue

    # 處理重複檔名
    base_name = str(story_id)
    counts.setdefault(base_name, 0)
    counts[base_name] += 1
    out_name = f"{base_name}.png" if counts[base_name] == 1 else f"{base_name}_{counts[base_name]}.png"
    out_path = os.path.join(out_dir, out_name)
    try:
        with open(out_path, 'wb') as f:
            f.write(img_bytes)
        print(f"已寫入: {out_path}")
    except Exception as e:
        print(f"寫檔失敗 (story_id={story_id}): {e}")

print(f"完成：總計處理 {len(rows)} 筆，產生 {sum(counts.values())} 個檔案，輸出目錄：{out_dir}")
