from env import supabase, gemini_client
from google.genai import types
from pydantic import BaseModel
import json
import datetime

class TopTenResponse(BaseModel):
    top_ten_story_ids: list[str]

def fetch_news_by_date(date: str):
    try:
        response = supabase.table("single_news")\
            .select("story_id, news_title, short, generated_date")\
            .like("generated_date", f"%{date}%")\
            .execute()
    except Exception as e:
        print(f"Error fetching news by date: {e}")
        return None
    return response.data

def fetch_country(story_id: str):
    try:
        response = supabase.table("stories").select("country").eq("story_id", story_id).execute()
    except Exception as e:
        print(f"Error fetching country: {e}")
        return None
    return response.data[0]["country"]

def generate_TopTen_news(country: str, news_list: list[dict], top_n: int = 10):
    
    system_instruction = f"""
        你是一個高效的新聞排序和資料處理引擎。
        你的任務是讀取使用者提供的 JSON 格式新聞列表。每則新聞都會有一個 `story_id` 和 `short`。

        你必須基於以下標準來評估 `short` 的重要性：
        1.  **影響範圍**：事件影響的人群規模（例如：國際、全國、地方）。
        2.  **顯著性**：事件的嚴重性或獨特性（例如：重大政策變更、突發災難、重要人物）。
        3.  **後續發展**：事件是否可能引發連鎖反應或未來有更多後續報導。

        你的回應**必須**嚴格遵守以下格式：
        -   **只回傳一個 JSON 陣列 (Array)**。
        -   此陣列中必須剛好包含 10 個字串 (String) 元素。
        -   這些元素必須是按重要性排序後的 `story_id`。
        -   陣列中的第一個 `story_id` 必須是當天最重要的新聞。
        -   **絕對不要**在 JSON 陣列之外添加任何文字（例如：不要說「這是今天的十大新聞...」或使用 ```json 標記）。
    """
    
    user_prompt = f"""
        這是我今天收到的{country}所有新聞報導，格式為 JSON 陣列。
        每篇新聞都包含一個 `story_id` 和 `short` 欄位。
        請你根據我們設定的規則，分析這些新聞的重要性，並只回傳一個包含前 10 大新聞 `story_id` 的 JSON 陣列。
        新聞資料如下：
        {json.dumps(news_list, ensure_ascii=False)}
    """
    
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="application/json",
        response_schema=TopTenResponse,
    )
    
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=user_prompt,
            config=config
        )
        
        #檢查結果是否有十篇新聞
        response_data = json.loads(response.text)
        if len(response_data.get("top_ten_story_ids", [])) != top_n:
            print(f"警告：回傳的新聞數量不等於 {top_n}，實際數量為 {len(response_data.get('top_ten_story_ids', []))}")
            return None
        return response.text
    except Exception as e:
        print(f"翻譯時發生錯誤: {e}")
        return None

def save_top_ten_news(date: str, country: str, top_ten_story_ids: dict):
    try:
        data = {
            "date": date,
            "country": country,
            "top_ten_news_id": top_ten_story_ids
        }
        supabase.table("top_ten_news").upsert(data).execute()
    except Exception as e:
        print(f"Error saving top ten news: {e}")

if __name__ == "__main__":
    
    #取今天日期的前一天
    date = datetime.datetime.now() - datetime.timedelta(days=1)
    date = date.strftime("%Y-%m-%d")
    allow_country = ["Taiwan", "United States of America", "Japan", "Indonesia"]
    
    print(f"Fetching news for date: {date}")
    news = fetch_news_by_date(date)
    
    country_news = {}
    for news in news:
        country = fetch_country(news["story_id"])
        if country not in allow_country:
            continue
        if country not in country_news:
            country_news[country] = []
        country_news[country].append(news)

    for country, country_news in country_news.items():
        print(f"Country: {country}, News Count: {len(country_news)}")
        top_ten = generate_TopTen_news(country, country_news, top_n=10)
        top_ten_result = json.loads(top_ten)
        
        if top_ten_result:
            print(f"Top 10 News for {country} on {date}:")
            print(top_ten_result["top_ten_story_ids"])
            save_top_ten_news(date, country, top_ten)
            
        