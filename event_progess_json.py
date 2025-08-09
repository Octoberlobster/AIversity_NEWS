import os
import json
import uuid
import datetime
from time import sleep
from collections import defaultdict
from dotenv import load_dotenv

import google.generativeai as genai

# --- 1. 環境設定 ---
# 建議使用 .env 檔案來管理您的 API 金鑰
load_dotenv()

# 從環境變數讀取 GEMINI_API_KEY
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 檢查金鑰是否存在
if not GEMINI_API_KEY:
    print("錯誤：請確認 .env 檔案中已設定 GEMINI_API_KEY")
    exit()

# 初始化 Gemini 模型客戶端
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

# --- 2. 從本地 JSON 檔案讀取並處理資料 ---
input_filename = 'full_backfill0706.json'
output_filename = 'event_progess0706.json'

try:
    with open(input_filename, 'r', encoding='utf-8') as f:
        rows = json.load(f)
except FileNotFoundError:
    print(f"錯誤：找不到 '{input_filename}' 檔案。")
    exit()
except json.JSONDecodeError:
    print(f"錯誤：'{input_filename}' 檔案格式不正確。")
    exit()

# 依照 event_id 分組並排序
events_news: dict[str, list[dict]] = defaultdict(list)
for r in rows:
    eid = r.get("event_id")
    if not eid:
        continue

    # 將毫秒時間戳轉換為 'YYYY-MM-DD' 格式
    timestamp_ms = r.get("date")
    if timestamp_ms:
        r['date'] = datetime.datetime.fromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d')
    else:
        r['date'] = "未知日期"
    
    events_news[eid].append(r)

# 將每個事件中的新聞按日期排序
for eid in events_news:
    events_news[eid].sort(key=lambda x: x["date"])

# --- 3. 定義事件分析函式 ---
def analyse_event(eid: str, news_rows: list[dict]) -> list[dict]:
    """
    分析單一事件的新聞，並生成時間軸項目。
    """
    total = len(news_rows)
    if total == 0:
        return []

    chunk_size = total // 5 + (1 if total % 5 else 0)
    items = []

    for idx in range(5):
        chunk = news_rows[idx * chunk_size : (idx + 1) * chunk_size]
        if not chunk:
            continue

        # 整理 prompt
        news_block = ""
        for art in chunk:
            news_block += (
                f"標題：{art.get('title', 'N/A')}\n"
                f"內容：{art.get('content', 'N/A')}\n"
                f"日期：{art.get('date', 'N/A')}\n---\n"
            )

        date_range = f"{chunk[0]['date']} ~ {chunk[-1]['date']}"
        prompt = f"""
                請閱讀以下多篇新聞，並完成以下任務：

                1. 統整此時段新聞進展：
                - 這些新聞依時間排序，請分析此段時間的整體事件發展、趨勢與關鍵轉折。
                2. 摘要與脈絡分析：
                - Summary 最多 15 個字，簡潔描述此時段的關鍵進展。

                3. 回覆格式為 JSON（嚴格遵守）：
                {{
                "Part": "{idx + 1}",
                "DateRange": "{date_range}",
                "Summary": "請填入簡要摘要（15字內）"
                }}

                注意：
                - 只能輸出 JSON。
                - Summary 最多 15 個字。
                - 使用繁體中文。

                以下是新聞資料：
                {news_block}
                """.strip()

        j = None
        for retry in range(3):
            try:
                res = model.generate_content(prompt)
                
                if not hasattr(res, 'text') or not res.text or not res.text.strip():
                    raise ValueError("模型返回了空的回應。")

                raw_text = res.text
                start_index = raw_text.find('{')
                end_index = raw_text.rfind('}') + 1

                if start_index == -1 or end_index <= start_index:
                    raise ValueError("回應中未找到有效的JSON格式。")

                json_str = raw_text[start_index:end_index]
                j = json.loads(json_str)
                break 
            except Exception as e:
                print(f"事件 {eid} 第 {retry+1} 次嘗試失敗: {e}")
                if hasattr(res, 'text'):
                     print(f"模型原始回應: '{res.text}'")
                if retry == 2:
                    print(f"事件 {eid} 分析失敗，跳過此區塊。")
                sleep(1)
        
        if not j:
            continue

        item_id = str(uuid.uuid4())
        items.append({
            "timeline_items_id": item_id,
            "event_id": eid,
            "date_range": j.get("DateRange"),
            "start_date": j.get("DateRange", " ~ ").split("~")[0].strip(),
            "summary": j.get("Summary"),
        })

    return items

# --- 4. 主執行迴圈並將結果寫入檔案 ---
all_event_progress = []

for eid, news in events_news.items():
    print(f"--- 正在處理事件 {eid} ---")
    items_rows = analyse_event(eid, news)
    
    if items_rows:
        all_event_progress.extend(items_rows)
        print(f"事件 {eid} 已生成 {len(items_rows)} 筆進程資料。")
    else:
        print(f"事件 {eid} 未生成任何資料。")
    
    print("-" * 50)

# 將所有結果寫入 event_progess.json
try:
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(all_event_progress, f, ensure_ascii=False, indent=4)
    print(f"\n--- 所有事件進程已成功寫入至 '{output_filename}' ---")
except Exception as e:
    print(f"\n--- 寫入檔案 '{output_filename}' 時發生錯誤: {e} ---")
