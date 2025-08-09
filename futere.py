import google.generativeai as genai
import json
import os
import re # <--- 1. 新增導入 re 模組
from collections import defaultdict
from dotenv import load_dotenv


# --- 1. 環境設定 ---
# 從 .env 檔案載入環境變數 (請確保您的 .env 檔案中有 GEMINI_API_KEY)
load_dotenv()


# 取得 Gemini API 金鑰
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("找不到 GEMINI_API_KEY，請在 .env 檔案中設定。")
genai.configure(api_key=api_key)


# --- 2. 初始化模型與設定提示訊息 ---
# 初始化 Gemini 模型
try:
    model = genai.GenerativeModel('gemini-1.5-pro')
except Exception as e:
    print(f"模型初始化失敗，請檢查 API 金鑰是否正確或網路連線: {e}")
    exit()


# 給予模型的初始指示訊息
first_message = (
    "接下來我會給你一連串的新聞內容，這些內容都已經依照發生順序給分類好了，請你記得這些內容，在最後提到\"預測未來\"時請你幫我根據先前的內容以三種面向來預測近日可能發生的未來(用十五到二十個字之間對每個面向總結除此之外生成關於這篇預測的標題即可)，"
    "請你以在預測時以JSON格式回答格式如下:"
    "{\"title\": \"請生成一個符合預測的標題\",\"content\": [\"1.\",\"2.\",\"3.\"]}"
    "如果你有接收到我的指示，請一律回答\"是的\"，謝謝！"
)


# 觸發預測的提示詞
prediction_prompt = "預測未來"


# --- 3. 讀取並分組 JSON 資料 ---
input_json_path = 'full_backfill0706.json'
output_json_path = 'perdit_future0706.json'  # 修改此處為您指定的輸出檔名


try:
    with open(input_json_path, 'r', encoding='utf-8') as f:
        all_news_data = json.load(f)
except FileNotFoundError:
    print(f"錯誤：找不到檔案 '{input_json_path}'。")
    exit()
except json.JSONDecodeError:
    print(f"錯誤：檔案 '{input_json_path}' 不是有效的 JSON 格式。")
    exit()


# 依照 event_id 將新聞分組
grouped_events = defaultdict(list)
for news_item in all_news_data:
    if isinstance(news_item, dict) and 'event_id' in news_item:
        grouped_events[news_item['event_id']].append(news_item)


# --- 4. 處理每個事件群組並生成預測 ---
all_predictions = []  # 用來存放所有事件的預測結果


for event_id, news_items in grouped_events.items():
    print(f"--- 正在處理 Event ID: {event_id} ---")


    # 為每個事件建立一個新的對話
    chat_session = model.start_chat(history=[])
    
    # 發送初始指示
    chat_session.send_message(first_message)


    # 依照日期排序新聞
    sorted_news = sorted(news_items, key=lambda x: x.get('date', 0))
    
    # 提取新聞內容
    news_contents = [item.get('content', '') for item in sorted_news]
    
    # 將新聞內容打包成 JSON 字串後發送
    news_body = json.dumps(news_contents, ensure_ascii=False, indent=4)
    chat_session.send_message(news_body)
    
    # 發送預測提示詞
    predict_response = chat_session.send_message(prediction_prompt)
    
    # --- 2. 以下是修改的部分 ---
    try:
        # 清理並解析模型回傳的 JSON 字串
        predict_text = predict_response.text
        
        # 使用正規表示式從回應中提取 JSON 字串
        # re.DOTALL 讓 '.' 可以匹配包含換行在內的所有字元
        match = re.search(r'\{.*\}', predict_text, re.DOTALL)
        
        if match:
            json_str = match.group(0)
            predict_data = json.loads(json_str)
        else:
            # 如果正規表示式找不到匹配，表示回應格式不如預期，印出錯誤並跳過
            print(f"錯誤：在 Event {event_id} 的模型回應中找不到有效的 JSON 物件。")
            print(f"模型原始回應: {predict_response.text}")
            continue # 繼續處理下一個 event
            
        # 加上 event_id 以便於識別
        predict_data['event_id'] = event_id

        # 將 'content' 列表合併為帶有換行的單一字串
        if "content" in predict_data and isinstance(predict_data["content"], list):
            total_content = "\n".join(predict_data["content"])
            predict_data["content"] = total_content.strip()
        
        # 將處理好的預測結果加入到總列表中
        all_predictions.append(predict_data)
        print(f"Event {event_id} 的預測處理完成。")

    except json.JSONDecodeError:
        # 只有在正規表達式找到的字串依然不是有效的JSON時，才會觸發這裡的錯誤
        print(f"錯誤：解析 Event {event_id} 的模型回應失敗 (JSON格式無效)。")
        print(f"試圖解析的字串: {json_str}")
    except Exception as e:
        print(f"處理 Event {event_id} 時發生預期外的錯誤: {e}")
    # --- 修改結束 ---


# --- 5. 將所有預測結果寫入檔案 ---
try:
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(all_predictions, f, ensure_ascii=False, indent=4)
    print(f"\n--- 所有預測結果已成功寫入至 '{output_json_path}' ---")
except Exception as e:
    print(f"\n--- 寫入檔案 '{output_json_path}' 時發生錯誤: {e} ---")

