"""從 Supabase 撈取 single_news，生成圖片並將 base64 圖片與描述寫回 generated_image 表

用法：
  python generate_from_supabase.py [limit]

需求：在 Picture_generate_system/.env 設定 SUPABASE_URL 與 SUPABASE_KEY，並設定 GEMINI_API_KEY
安裝套件：pip install supabase-py postgrest-py python-dotenv google-genai pillow
"""
import os
import sys
import time
import base64
from typing import Optional
from dotenv import load_dotenv

print("開始執行腳本...")

# 載入環境變數，指定 Picture_generate_system 目錄中的 .env 檔案
picture_system_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'Picture_generate_system')
env_path = os.path.join(picture_system_dir, '.env')
print(f"載入環境變數檔案: {env_path}")
load_dotenv(env_path)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("請在 Picture_generate_system/.env 設定 SUPABASE_URL 與 SUPABASE_KEY")
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
    from google.genai import types
except Exception:
    print("請先安裝 google genai SDK：pip install google-genai")
    raise SystemExit(1)

# 圖片生成相關函數
def _prompt_photoreal_no_text(news_title: str, news_summary: str, category: str) -> str:
    """根據新聞標題和摘要，生成不含文字的攝影級寫實事件示意圖提示。"""
    category_styles = {
        "政治": "dramatic, serious, high-contrast, documentary style",
        "社會": "documentary realism, human-centric",
        "國際": "cinematic realism with diplomatic symbolism (no flags)",
        "財經": "neutral corporate tone, high-tech, clean aesthetics",
        "科技": "futuristic, sleek, innovative, digital aesthetics",
    }
    style_hint = category_styles.get(category or "", "neutral editorial tone with subtle cinematic realism")
    
    photo_style = (
        "photorealistic, realistic photo, cinematic still, natural color grading, "
        "soft directional lighting, subtle film grain, shallow depth of field, creamy bokeh, "
        "subject isolation, rule of thirds, foreground/background layering"
    )
    
    core_subject = (
        f"A scene representing the core concepts of the news: '{news_title}'. "
        f"The visual elements should metaphorically or symbolically illustrate the key points from the summary: '{news_summary}'. "
        f"Focus on generic, non-identifiable persons and symbolic objects to convey the narrative without any text."
    )
    
    no_text = (
        "CRITICAL: Absolutely NO TEXT of any kind within the image. "
        "NO letters, NO numbers, NO words, NO captions, NO labels, NO banners, NO signage, NO UI, NO subtitles. "
        "NO logos, NO trademarks, NO watermarks, NO brand marks."
    )
    
    prompt = (
        f"IMPORTANT: {no_text} "
        f"Generate a scene representing: {core_subject}. "
        f"Style requirements: {style_hint}, {photo_style}. "
        f"Image size 1024x625 pixels, aspect ratio 5:3, high clarity, realistic textures and materials."
    )
    return prompt

def _gen_image_bytes_with_retry(client, prompt: str, model_id: str, retry_times: int, sleep_between_calls: float) -> Optional[bytes]:
    """使用重試機制生成圖片並返回字節數據。"""
    for attempt in range(1, retry_times + 1):
        try:
            resp = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE'],
                ),
            )
            cands = getattr(resp, "candidates", [])
            if not cands:
                raise RuntimeError("No candidates in response")
            
            img_bytes = None
            for part in cands[0].content.parts:
                if getattr(part, "inline_data", None):
                    data = part.inline_data.data
                    if isinstance(data, (bytes, bytearray)):
                        img_bytes = bytes(data)
                        break
                    else:
                        try:
                            img_bytes = base64.b64decode(data)
                            break
                        except (ValueError, TypeError):
                            pass
            
            if img_bytes:
                return img_bytes
            time.sleep(sleep_between_calls)
        except (RuntimeError, ValueError, TypeError) as e:
            if attempt >= retry_times:
                print(f"[ERROR] generate failed after {retry_times} attempts: {e}")
                return None
            time.sleep(sleep_between_calls)
    return None

def _generate_image_description(news_title: str, news_summary: str, category: str) -> str:
    """為生成的圖片創建說明文字。"""
    title_clean = news_title.replace("| 政治", "").replace("｜ 公視新聞網 PNN", "")
    title_clean = title_clean.replace("｜", "").replace("|", "").replace("PNN", "")
    title_clean = title_clean.replace("公視新聞網", "").replace("新聞網", "")
    title_clean = title_clean.strip()
    
    # 簡化的描述生成邏輯
    if len(title_clean) <= 15:
        return title_clean
    else:
        # 取前15個字符並嘗試在合理位置截斷
        truncated = title_clean[:15]
        return truncated

# 建立 Supabase 與 Gemini client
sb = create_client(SUPABASE_URL, SUPABASE_KEY)
gen_client = genai.Client()

# 獲取所有新聞，不限制數量
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else None  # 如果有參數則使用，否則不限制
MODEL_ID = 'gemini-2.0-flash-preview-image-generation'
RETRY_TIMES = 3
SLEEP_BETWEEN = 0.6

print(f"Connecting to Supabase: {SUPABASE_URL}")
if LIMIT:
    print(f"Fetching up to {LIMIT} rows from table 'single_news'...")
else:
    print("Fetching ALL rows from table 'single_news'...")

# 先嘗試選取常見欄位
if LIMIT:
    resp = sb.table('single_news').select('story_id,news_title,long').limit(LIMIT).execute()
else:
    resp = sb.table('single_news').select('story_id,news_title,long').execute()
    
if getattr(resp, 'error', None):
    print("嘗試選取 (story_id,news_title,long) 發生錯誤，改為 select('*') 以檢視欄位：", resp.error)
    if LIMIT:
        resp = sb.table('single_news').select('*').limit(LIMIT).execute()
    else:
        resp = sb.table('single_news').select('*').execute()

rows = resp.data or []
if not rows:
    print("未取得任何 row，請確認表名或權限")
    raise SystemExit(0)

# 讀取已經生成過圖片的 story_id，避免重複生成
print("檢查 generated_image 表中已存在的 story_id...")
existing_resp = sb.table('generated_image').select('story_id').execute()
existing_story_ids = set()
if existing_resp.data:
    existing_story_ids = {row.get('story_id') for row in existing_resp.data if row.get('story_id') is not None}
    print(f"發現 {len(existing_story_ids)} 個已生成圖片的 story_id")
else:
    print("generated_image 表為空或無法讀取")

# 過濾掉已經生成過的新聞
original_count = len(rows)
rows = [row for row in rows if row.get('story_id') not in existing_story_ids]
filtered_count = len(rows)
print(f"原有 {original_count} 筆新聞，過濾後剩餘 {filtered_count} 筆需要生成圖片")

if not rows:
    print("所有新聞都已生成過圖片，無需處理")
    raise SystemExit(0)

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

    print(f"Row {i}/{filtered_count}: story_id={story_id} news_title={title[:40]}")
    if not title and content:
        # 從 content 取前段作為 title 的 fallback
        title = (content[:40] + '...') if len(content) > 40 else content

    prompt = _prompt_photoreal_no_text(title or '', content or '', category='')

    img_bytes = _gen_image_bytes_with_retry(gen_client, prompt, MODEL_ID, RETRY_TIMES, SLEEP_BETWEEN)
    if not img_bytes:
        print(f"第 {i} 筆（story_id={story_id}）生成失敗，跳過")
        fail_count += 1
        continue

    # 產生描述（短）
    description = _generate_image_description(title or '', content or '', '')

    # base64 encode
    b64 = base64.b64encode(img_bytes).decode('ascii')

    payload = {
        'story_id': story_id,
        'image': b64,
        'description': description,
    }

    # 嘗試插入資料庫
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
