import google.generativeai as genai
import json
from time import sleep
import os
from supabase import create_client, Client
import uuid

# 設定 API 金鑰
api_key = os.getenv("API_KEY_Ge")
genai.configure(api_key=api_key)
api_key_supabase = os.getenv("API_KEY_supa")
supabase_url = os.getenv("API_KEY_URL")
supabase: Client = create_client(supabase_url, api_key_supabase)

model = genai.GenerativeModel('gemini-1.5-pro-002')

# 假設你有 JSON 資料（可以從檔案讀取或其他來源獲得）
# 這裡我使用你提供的範例格式
def load_json_data():
    """
    載入 JSON 資料的函數
    可以從檔案讀取或其他資料源獲得
    """
    # 範例：從檔案讀取 JSON
    with open('json/processed/cleaned_final_news.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def process_news_stories():
    """
    處理新聞故事的主要函數
    """
    # 載入 JSON 資料
    json_data = load_json_data()
    
    # 處理每個故事
    for story in json_data:
        story_index = story["story_index"]
        story_title = story["story_title"]
        articles = story["articles"]
        
        print(f"處理故事 {story_index}: {story_title}")
        
        # 準備文章內容給 AI 處理
        articles_content = []
        for article in articles:
            article_info = {
                "title": article["article_title"],
                "url": article["final_url"],
                "content": article["content"],
                "date": article["date"]
            }
            articles_content.append(article_info)
        
        # 轉換為 JSON 字串
        news_body = json.dumps(articles_content, ensure_ascii=False, indent=4)
        
        # 生成 AI 內容
        try:
            news_response = model.generate_content(
                "請根據以下彙整的新聞內容，生成一篇新的新聞報導，並提供標題與統整內容。請確保內容具有新聞性，並清楚呈現事件的背景、發展與影響。"
                "輸出格式（請以 JSON 格式回傳）："
                "{"
                "\"title\": \"請生成一個符合新聞風格的標題\","
                "\"content\": \"請綜合以下新聞內容，撰寫一篇具邏輯性、流暢且完整的新聞報導\","
                "\"date\": \"請填寫新聞生成的日期（格式：YYYY-MM-DD HH:MM）\","
                f"\"story_index\": {story_index}"
                "}"
                f"需要彙整的新聞內容：\n{news_body}"
                "請確保新生成的新聞報導符合以下要求："
                "維持新聞的公正與專業性"
                "使用清晰且具邏輯性的語句"
                "確保內容與事實相符，不加入虛構或未經證實的資訊"
            )
            
            # 處理 AI 回應
            news_text = news_response.text
            news_text = news_text.replace('```json', '').replace('```', '').strip()
            news_data = json.loads(news_text)
            
            # 生成唯一 ID
            generated_uuid = str(uuid.uuid4())
            news_data["id"] = generated_uuid
            
            print(f"生成的新聞標題: {news_data['title']}")
            print(f"生成的 UUID: {generated_uuid}")
            
            # 這裡可以將結果儲存到資料庫或檔案
            # save_to_database(news_data)
            # 或儲存到 JSON 檔案
            save_to_json_file(news_data)
            
        except json.JSONDecodeError as e:
            print(f"JSON 解析錯誤 - Story {story_index}: {e}")
        except Exception as e:
            print(f"處理錯誤 - Story {story_index}: {e}")
        
        # 延遲避免 API 限制
        sleep(1)

def save_to_json_file(news_data, filename="json/generated_news/generated_news2.json"):
    """
    將生成的新聞儲存到 JSON 檔案
    """
    try:
        # 嘗試讀取現有檔案
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except FileNotFoundError:
            existing_data = []
        
        # 添加新資料
        existing_data.append(news_data)
        
        # 寫入檔案
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
            
        print(f"新聞已儲存到 {filename}")
        
    except Exception as e:
        print(f"儲存檔案錯誤: {e}")

def save_to_database(news_data):
    """
    將生成的新聞儲存到 Supabase 資料庫
    """
    try:
        response = supabase.table("generated_news").insert(news_data).execute()
        print(f"新聞已儲存到資料庫: {news_data['id']}")
    except Exception as e:
        print(f"資料庫儲存錯誤: {e}")

# 主程式執行
if __name__ == "__main__":
    process_news_stories()