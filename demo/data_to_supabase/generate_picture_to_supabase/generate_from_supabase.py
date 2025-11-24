"""從 Supabase 撈取 single_news，生成圖片並將 base64 圖片與描述寫回 generated_image 表

使用說明（可放任意順序的參數）:

    python generate_from_supabase.py [LIMIT] [no-write] [force]

參數說明：
    LIMIT      - (可選) 整數，限制要處理的新聞筆數。例如 1、3、10。若未提供則處理全部符合條件的新聞。
    no-write   - (可選) 測試模式：不會寫入資料庫，而是把生成結果存成 JSON 檔案於
                             generated_image_previews/ 目錄，檔名格式：generated_image_preview_{story_id}.json
    force      - (可選) 強制模式：忽略已存在於 generated_image 表中的 story_id，會對取出的新聞強制重新生成
                             （僅建議在測試時使用，避免不小心覆寫或重複產生大量圖片）。

使用範例：
    python generate_from_supabase.py 3                # 處理前 3 筆（會跳過已生成過的 story_id）
    python generate_from_supabase.py 1 no-write       # 處理 1 筆並將結果寫為 JSON（不寫入 DB）
    python generate_from_supabase.py force 1 no-write # 強制處理 1 筆（忽略已生成檢查），並以 JSON 儲存
    python generate_from_supabase.py no-write         # 處理全部符合條件的新聞，但不寫入 DB（小心耗時）

注意事項：
    - 執行會使用工作目錄下的 .env 檔（或系統環境）中的 SUPABASE_URL、SUPABASE_KEY 與 GEMINI_API_KEY。
    - 生成圖片會呼叫 Gemini 圖像 API，可能會產生費用與配額消耗。請確認您同意使用該帳號/金鑰。
    - 若要避免覆寫/新增資料，請在測試時使用 no-write 模式；若需重生成已存在項目，可搭配 force 使用。

需求/安裝：
    pip install supabase-py postgrest-py python-dotenv google-genai pillow

輸出位置：
    - 真正寫入 DB：寫入至 Supabase 的 generated_image 表（欄位 story_id, image (base64), description）
    - no-write 模式：JSON 檔案存於 generated_image_previews/ 下（包含 prompt、description、image_base64）

"""
import os
import sys
import time
import base64
import json
from typing import Optional
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from postgrest.exceptions import APIError


def execute_builder_with_retry(builder, max_retries: int = 3):
    """Execute a postgrest request builder with retry on statement timeout."""
    for attempt in range(1, max_retries + 1):
        try:
            return builder.execute()
        except APIError as e:
            msg = str(e)
            if 'canceling statement due to statement timeout' in msg and attempt < max_retries:
                wait = attempt * 2
                print(f"[warn] DB statement timeout, retry {attempt}/{max_retries} after {wait}s")
                time.sleep(wait)
                continue
            raise

print("開始執行腳本...")


load_dotenv()

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
    """根據新聞標題和摘要，生成不含文字的攝影級寫實事件示意圖提示。
    
    嚴格要求：
    1. 絕對禁止任何文字、符號、標誌
    2. 高解析度專業攝影品質
    3. 完全基於新聞實際內容生成，不使用隱喻或不相關物件
    """
    
    # 超高解析度與專業攝影品質要求
    high_quality = (
        "ULTRA HIGH RESOLUTION, 8K quality, professional photojournalism grade, "
        "crystal clear focus, razor-sharp details, maximum clarity, "
        "professional DSLR camera shot, high dynamic range (HDR), "
        "exceptional image quality, publication-ready, commercial photography standard"
    )
    
    # 專業攝影風格（可依 category 調整）
    category_styles = {
        "政治": "serious editorial photography, dramatic natural lighting, documentary photojournalism style",
        "社會": "human-interest documentary style, authentic moments, environmental portrait approach",
        "國際": "international photojournalism, diplomatic event coverage, architectural context",
        "財經": "corporate editorial photography, professional business environment, clean modern aesthetics",
        "科技": "tech editorial photography, innovative spaces, modern industrial design",
    }
    style_hint = category_styles.get(category or "", "professional editorial photography, authentic documentary approach")

    photo_technique = (
        "photorealistic, professional photography, cinematic composition, "
        "natural color grading with accurate white balance, "
        "professional lighting setup, optimal exposure, "
        "depth of field control, bokeh quality, "
        "rule of thirds composition, leading lines, visual hierarchy"
    )

    # 絕對禁止文字 - 多層次強調
    absolute_no_text = (
        "【ABSOLUTE CRITICAL REQUIREMENT - NO TEXT WHATSOEVER】\n"
        "ZERO TEXT allowed in the image. This is NON-NEGOTIABLE.\n"
        "NO letters, NO numbers, NO characters of any language (English, Chinese, Japanese, Korean, Arabic, etc.), "
        "NO words, NO captions, NO labels, NO signs, NO signage, NO banners, NO posters, "
        "NO billboards, NO newspapers, NO books with visible text, NO screens with text, "
        "NO UI elements, NO subtitles, NO watermarks, NO logos, NO trademarks, NO brand names, "
        "NO license plates with readable text, NO nametags, NO badges with text, "
        "NO graffiti, NO writing of any kind, NO textual overlays, NO typographic elements.\n"
        "If buildings/locations must appear, show them from angles where signs are NOT visible. "
        "If documents must appear, show them as blank papers or blur any text completely. "
        "If screens must appear, show them turned off or with pure abstract patterns only."
    )

    # 嚴格的否定清單：禁止不相關物件與隱喻道具
    negative_items = (
        "【FORBIDDEN OBJECTS】Do NOT include: "
        "hammers, mallets, gavels, tools, hand tools, construction tools, carpentry tools, "
        "weapons, guns, knives, swords, mechanical instruments, "
        "scales of justice (unless the news is specifically about courts/justice system), "
        "chess pieces, light bulbs, keys, locks (unless directly relevant to the news content), "
        "clocks, hourglasses (unless about time-related news), "
        "puzzle pieces, magnifying glasses (unless detective/investigation news), "
        "arrows, targets, ladders, chains, "
        "generic metaphorical objects that have no direct connection to the actual news event. "
        "ONLY include objects and locations that are LITERALLY mentioned or directly implied in the news content."
    )

    # 基於新聞實際內容的具體場景指示
    content_based_generation = (
        f"【CONTENT-BASED GENERATION - STRICT ADHERENCE TO NEWS CONTENT】\n"
        f"News Title: '{news_title}'\n"
        f"News Summary: '{news_summary}'\n\n"
        "REQUIREMENT: Generate ONLY what is directly described or clearly implied in the above news content.\n"
        "- If the news mentions a specific location (hospital, court, parliament, street, building, etc.), show that location.\n"
        "- If the news mentions specific objects (medical equipment, vehicles, ballot boxes, etc.), show those objects.\n"
        "- If the news mentions people in specific roles (doctors, politicians, protesters, etc.), show anonymous figures in those roles "
        "(rear view, silhouette, or far enough that faces are not identifiable).\n"
        "- If the news is about an abstract concept (policy, economy, legislation), show the PHYSICAL LOCATION where such activities occur "
        "(e.g., parliament building exterior, stock exchange hall, government office, business district) "
        "rather than using symbolic objects.\n"
        "- Use environmental storytelling: show the ACTUAL SCENE of the event, not metaphors.\n"
        "- Prefer wide shots or establishing shots that show context and environment.\n"
        "- If people must be shown, ensure they are anonymous, non-identifiable, "
        "shot from behind, from a distance, or in silhouette to protect privacy and avoid identification."
    )

    # 具體場景範例指引（根據常見新聞類型）
    scene_examples = (
        "【SCENE EXAMPLES BASED ON NEWS TYPE】\n"
        "- Election/Voting news → polling station interior, ballot boxes, voting booths, empty civic centers\n"
        "- Medical/Health news → hospital corridors, medical facilities, clinical environments, ambulances\n"
        "- Legal/Court news → courtroom interior (empty or with anonymous figures), courthouse architecture\n"
        "- Political news → parliament/government buildings (exterior or interior), official meeting spaces\n"
        "- Economic/Business news → modern office buildings, stock exchange, business districts, corporate environments\n"
        "- Technology news → tech campuses, data centers, modern workspaces, innovation labs\n"
        "- Social/Community news → public spaces, community centers, street scenes, residential areas\n"
        "- Environmental news → natural landscapes, urban environments, infrastructure, relevant geographical locations\n"
        "- Crime/Safety news → urban environments, police stations (exterior), public safety contexts (no graphic content)\n"
        "- International news → relevant architectural landmarks, diplomatic buildings, international settings"
    )

    # 超級強調：開頭再次重複禁止文字
    ultra_critical_no_text = (
        "!!!CRITICAL OVERRIDE!!! ABSOLUTELY NO TEXT IN THE IMAGE !!!\n"
        "This is the HIGHEST PRIORITY requirement that OVERRIDES everything else.\n"
        "NO TEXT means NO TEXT. Not even a single letter, number, or symbol.\n"
        "Remove ALL signs, labels, writing, captions, subtitles from the scene.\n"
        "If you see ANY text forming in the image generation, STOP and regenerate without it.\n\n"
    )
    
    # 組合最終 prompt - 多次重複禁止文字要求
    prompt = (
        f"{ultra_critical_no_text}"
        f"{absolute_no_text}\n\n"
        f"REPEAT: NO TEXT ALLOWED. ZERO TEXT. 絕對不能有任何文字。\n\n"
        f"{negative_items}\n\n"
        f"{content_based_generation}\n\n"
        f"{scene_examples}\n\n"
        f"【TECHNICAL SPECIFICATIONS】\n"
        f"{high_quality}\n"
        f"Photography style: {style_hint}\n"
        f"Technical approach: {photo_technique}\n"
        f"Image dimensions: 1024x625 pixels (aspect ratio 5:3)\n"
        f"Quality requirement: Maximum resolution and clarity, professional grade, publication ready\n\n"
        f"【FINAL CRITICAL INSTRUCTION - REPEAT】\n"
        f"⚠️ MOST IMPORTANT: The generated image MUST NOT contain ANY text whatsoever. ⚠️\n"
        f"NO letters, NO words, NO numbers, NO symbols, NO writing of ANY kind in ANY language.\n"
        f"If there are signs/billboards in the scene, show them completely blank or remove them entirely.\n"
        f"If there are screens, show them turned off (black) or with pure solid colors only.\n"
        f"If there are documents/papers, show them as blank white sheets.\n"
        f"Shoot from angles that avoid any text that might exist in the environment.\n\n"
        f"Create a high-resolution, professional photojournalistic image that LITERALLY represents "
        f"the news event described above. Use ONLY elements directly mentioned or clearly implied "
        f"in the news content. "
        f"Prioritize authenticity, clarity, and direct visual representation over symbolic or metaphorical imagery.\n\n"
        f"FINAL VERIFICATION: Before returning the image, check - is there ANY text visible? If YES, regenerate without text. "
        f"The image must be 100% text-free. 圖片必須 100% 無文字。"
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
            if cands[0].content.parts is None:
                raise RuntimeError("No content parts in candidate")
            
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

def _generate_image_description_with_vision(gen_client, img_bytes: bytes, news_title: str, news_summary: str, category: str) -> str:
    """使用 Gemini Vision API 分析圖片並結合新聞內容生成說明。
    
    Args:
        gen_client: Gemini client 實例
        img_bytes: 圖片的 bytes 資料
        news_title: 新聞標題
        news_summary: 新聞摘要
        category: 新聞類別
        
    Returns:
        str: 生成的圖片說明（15字以內）
    """
    try:
        # 建立提示詞
        prompt = f"""請根據以下新聞內容和圖片，生成一個簡短且語意完整的圖片說明。

新聞標題：
{news_title}

新聞內容：
{news_summary[:1000]}

【絕對嚴格的要求 - 必須100%遵守】：

1. 字數限制：說明必須在 15 個字以內（含標點符號）
2. 完整性要求：說明必須是完整的句子，絕對不可以中途截斷
3. 標點符號：不要以逗號（，）、頓號（、）、分號（；）、冒號（：）結尾
4. 可接受的結尾：句號（。）、驚嘆號（！）、問號（？）或直接以名詞/動詞結尾
5. 禁止使用：「...」、「等」、「之類」等任何省略表達
6. 內容準確：必須準確描述圖片實際內容
7. 相關性：必須與新聞內容相關
8. 語氣：客觀、中立、不帶情感色彩
9. 格式：直接輸出說明文字，不要有任何前綴或說明
10. 精簡原則：在字數限制內，用最精煉的方式表達完整意思

【正確範例】（完整且符合字數）：
✓ 總統參加經濟論壇
✓ 股市今日收盤上漲
✓ 新手機產品發表
✓ 民眾街頭示威遊行
✓ 颱風造成淹水災情
✓ 新遊戲即將上市
✓ 遊戲發表會現場

【錯誤範例】（會被系統拒絕）：
✗ 總統出席重要的國際經濟會議並發表... (超過15字且被截斷)
✗ 股市收盤創下史上最高, (以逗號結尾)
✗ 新款科技產品等 (使用「等」省略)
✗ 民眾參與 (語意不完整)

現在請生成符合所有要求的圖片說明：
"""
        
        # 使用 Gemini Vision API
        response = gen_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(
                            data=img_bytes,
                            mime_type="image/png"
                        ),
                        types.Part.from_text(text=prompt)
                    ]
                )
            ],
            config=types.GenerateContentConfig(
                temperature=0.0
            )
        )
        
        # 提取生成的文字
        description = response.text.strip()
        
        # 移除可能的引號或多餘空白
        description = description.strip('"\'\'「」『』 ')
        
        # 檢查長度並進行智能截斷
        if len(description) > 15:
            print(f"⚠️  警告：AI 生成的說明超過 15 字（{len(description)} 字）：{description}")
            print("   正在智能分析並修正...")
            
            # 定義檢查函數
            def is_meaningful_truncation(original: str, truncated: str) -> bool:
                """檢查截斷後的內容是否仍保有完整語意"""
                if '年' in truncated and '月' in original and '月' not in truncated:
                    if original.find('年') < original.find('月'):
                        return False
                
                if truncated and truncated[-1].isdigit():
                    truncated_end = len(truncated) - 1
                    if truncated_end < len(original) - 1 and original[truncated_end + 1].isdigit():
                        return False
                
                incomplete_endings = ['於', '在', '將', '至', '從', '向', '對', '為', '給', '被', '把']
                if truncated and truncated[-1] in incomplete_endings:
                    return False
                
                quote_pairs = [
                    ('《', '》'), ('「', '」'), ('『', '』'), 
                    ('"', '"'), (''', '''), ('(', ')'), ('（', '）'), ('[', ']')
                ]
                for open_q, close_q in quote_pairs:
                    if open_q in truncated and close_q not in truncated:
                        return False
                
                if len(truncated) < 5:
                    return False
                
                return True
            
            # 策略1: 在句號處截斷
            best_cut = -1
            for i in range(14, 0, -1):
                if description[i] in '。！？':
                    candidate = description[:i+1]
                    if is_meaningful_truncation(description, candidate):
                        best_cut = i + 1
                        break
            
            if best_cut > 0:
                description = description[:best_cut]
                print("   → 策略1：在句號處截斷為完整句子")
            else:
                # 策略2: 在逗號處截斷
                candidates = []
                for i in range(min(14, len(description)-1), 4, -1):
                    if description[i] in '，、':
                        candidate = description[:i]
                        if candidate and candidate[-1] not in '的了在與和及或：:':
                            if is_meaningful_truncation(description, candidate):
                                candidates.append((i, candidate))
                
                if candidates:
                    best_idx, description = candidates[0]
                    print("   → 策略2：在標點處取語意完整部分")
                else:
                    # 使用備用說明
                    category_map = {
                        '政治': '政治新聞',
                        '經濟': '經濟新聞',
                        '社會': '社會新聞',
                        '國際': '國際新聞',
                        '科技': '科技新聞',
                        '體育': '體育新聞',
                        '娛樂': '娛樂新聞',
                    }
                    description = category_map.get(category, '新聞圖片')
                    print(f"   → 使用備用說明：{description}")
            
            print(f"   ✓ 最終結果：{description} ({len(description)}字)")
        
        # 最終清理
        while description and description[-1] in '，、；：':
            description = description[:-1]
        
        # 確保不是空字串
        if not description or len(description) < 3:
            print("⚠️  生成的說明過短或為空，使用備用說明")
            description = f"{category}新聞圖片" if category else "新聞圖片"
        
        # 最終驗證
        if len(description) > 15:
            print("❌ 錯誤：截斷後仍超過 15 字，強制截斷")
            description = description[:15].rstrip('的了在與和，、；：及或是有到被給為著過')
        
        return description
        
    except Exception as e:
        print(f"❌ 使用 Vision API 生成說明時發生錯誤: {e}")
        # 回退到簡單的標題截取
        title_clean = news_title.replace("| 政治", "").replace("｜ 公視新聞網 PNN", "")
        title_clean = title_clean.replace("｜", "").replace("|", "").replace("PNN", "")
        title_clean = title_clean.replace("公視新聞網", "").replace("新聞網", "")
        title_clean = title_clean.strip()
        
        if len(title_clean) <= 15:
            return title_clean
        else:
            return title_clean[:15]

# 建立 Supabase 與 Gemini client
sb = create_client(SUPABASE_URL, SUPABASE_KEY)
gen_client = genai.Client()

# 獲取所有新聞，不限制數量
# 支援參數：LIMIT, no-write, force（參數順序不限）
args = sys.argv[1:]
# 找到第一個數字作為 LIMIT（如果有）
LIMIT = None
for a in args:
    if a.isdigit():
        LIMIT = int(a)
        break
# 若傳入 'no-write' 則禁止寫入資料庫（測試模式）
NO_WRITE = 'no-write' in args
# 若傳入 'force' 則忽略 existing_story_ids 檢查（強制重生成，僅用於測試）
FORCE = 'force' in args
MODEL_ID = 'gemini-2.5-flash-image'
RETRY_TIMES = 3
SLEEP_BETWEEN = 0.6

print(f"Connecting to Supabase: {SUPABASE_URL}")
if LIMIT:
    print(f"Fetching up to {LIMIT} rows from table 'single_news'...")
else:
    print("Fetching ALL rows from table 'single_news'...")

# 先嘗試選取常見欄位
resp = []
batch_size = 1000
start = 0

while True:
    try:
        builder = sb.table('single_news').select('story_id,news_title,long').range(start, start + batch_size - 1).order("generated_date", desc=True)
        temp = execute_builder_with_retry(builder)
    except Exception as e:
        print(f"[error] Failed to fetch rows from single_news (range {start}-{start+batch_size-1}): {e}")
        break
    if not getattr(temp, 'data', None):
        break
    resp.extend(temp.data)
    start += batch_size

if getattr(resp, 'error', None):
    print("嘗試選取 (story_id,news_title,long) 發生錯誤，改為 select('*') 以檢視欄位：", resp.error)
    batch_size = 1000
    start = 0
    while True:
        try:
            builder = sb.table('single_news').select('*').range(start, start + batch_size - 1)
            temp = execute_builder_with_retry(builder)
        except Exception as e:
            print(f"[error] Failed to fetch rows with select('*') (range {start}-{start+batch_size-1}): {e}")
            break
        if not getattr(temp, 'data', None):
            break
        resp.extend(temp.data)
        start += batch_size

rows = resp or []
if not rows:
    print("未取得任何 row，請確認表名或權限")
    raise SystemExit(0)

# 讀取已經生成過圖片的 story_id，避免重複生成
print("檢查 generated_image 表中已存在的 story_id...")
existing_resp = []
batch_size = 1000
start = 0

while True:
    temp = sb.table('generated_image').select('story_id').range(start, start + batch_size - 1).execute()
    if not temp.data:
        break
    existing_resp.extend(temp.data)
    start += batch_size
existing_story_ids = set()
if existing_resp:
    existing_story_ids = {row.get('story_id') for row in existing_resp if row.get('story_id') is not None}
    print(f"發現 {len(existing_story_ids)} 個已生成圖片的 story_id")
else:
    print("generated_image 表為空或無法讀取")

# 過濾掉已經生成過的新聞（如果沒有 force 標記）
original_count = len(rows)
if not FORCE:
    rows = [row for row in rows if row.get('story_id') not in existing_story_ids]
else:
    print("FORCE 模式：忽略已生成紀錄，將強制對取出的新聞生成圖片（僅用於測試）")
filtered_count = len(rows)
print(f"原有 {original_count} 筆新聞，過濾後剩餘 {filtered_count} 筆需要生成圖片")

if not rows:
    print("所有新聞都已生成過圖片（或過濾後無資料），無需處理")
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

    # 使用 Vision API 產生描述（15字以內）
    print("正在使用 Vision API 生成圖片描述...")
    description = _generate_image_description_with_vision(gen_client, img_bytes, title or '', content or '', '')

    # base64 encode
    b64 = base64.b64encode(img_bytes).decode('ascii')

    payload = {
        'story_id': story_id,
        'image': b64,
        'description': description,
    }

    # 嘗試插入資料庫
    try:
        if NO_WRITE:
            # 測試模式：不寫入資料庫，將結果以 JSON 存檔供檢查
            out_dir = "generated_image_previews"
            try:
                os.makedirs(out_dir, exist_ok=True)
                preview = {
                    'story_id': story_id,
                    'description': description,
                    'image_base64': b64,
                    'prompt': prompt
                }
                filename = f"{out_dir}/generated_image_preview_{story_id}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(preview, f, ensure_ascii=False, indent=2)
                print(f"[no-write] 已將預覽輸出為 JSON: {filename} (image_len={len(b64)} chars)")
            except Exception as e:
                print(f"[no-write] 無法寫入預覽 JSON: {e}")
        else:
            ins = sb.table('generated_image').insert(payload).execute()
            if getattr(ins, 'error', None):
                print(f"寫入 generated_image 發生錯誤: {ins.error}")
                fail_count += 1
            else:
                insert_count += 1
                print(f"已寫入 generated_image (story_id={story_id})")
                # 同步更新 single_news 表的 updated_date 欄位為目前時間
                try:
                    tz_taipei = timezone(timedelta(hours=8))
                    updated_date_str = datetime.now(tz_taipei).strftime("%Y-%m-%d %H:%M")
                    upd = sb.table('single_news').update({'updated_date': updated_date_str}).eq('story_id', story_id).execute()
                    if getattr(upd, 'error', None):
                        print(f"更新 single_news.updated_date 失敗 (story_id={story_id}): {upd.error}")
                    else:
                        print(f"已更新 single_news.updated_date (story_id={story_id}) -> {updated_date_str}")
                except Exception as e:
                    print(f"更新 single_news.updated_date 發生例外 (story_id={story_id}): {e}")
                # 避免速率限制
                time.sleep(0.5)
    except Exception as e:
        print(f"寫入例外: {e}")
        fail_count += 1

print(f"完成：寫入 {insert_count} 筆，失敗 {fail_count} 筆")