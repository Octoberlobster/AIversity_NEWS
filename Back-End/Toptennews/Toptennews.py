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
        你是一位資深的新聞主編和資料分析師，專門分析 **{country}** 的國家級新聞。
        你的任務是讀取使用者提供的 JSON 格式新聞列表，並為 **{country}** 評選出當天前 {top_n} 則最重要的新聞。

        你必須嚴格遵守以下的**分層優先級 (Hierarchical Priority)** 來進行排序和篩選：

        **【第一優先： {country} 國內新聞】**
        這是你的**首要**考量。你必須優先從 {country} 國內尋找符合以下條件的新聞：
        1.  **國家級影響**：直接影響 **{country}** 政府、國內政策、經濟（例如：央行、關鍵產業）、或國家安全的事件。
        2.  **重大社會/環境事件**：**發生在 {country} 境內**的重大事件，如天災（地震、颱風）、大規模示威、重大公安事故、或全國性的科學 breakthrough。

        **【第二優先： {country} 相關國際新聞】**
        只有在 {country} 國內新聞無法填滿 {top_n} 個名額，或此類新聞重要性極高時，才可考慮：
        3.  **國際關係**：**{country}** 作為主要參與者的外交、軍事或重大貿易事件。
        4.  **重大外部衝擊**：對 **{country}** 經濟、國民或安全有**直接且重大**衝擊的國際事件。

        ---
        **【嚴格過濾：不相關的國際新聞】**
        -   你分析的新聞列表中可能包含 {country} 媒體報導的「**其他國家的地區性/內部新聞**」（例如：日本熊害、歐洲皇室動態）。
        -   **你必須將這些新聞的優先級排在所有「第一優先」和「第二優先」的新聞之後。** -   只有在極少數情況下（例如 {country} 國內新聞嚴重不足）才可使用。
        ---

        **【【最重要規則：主題多樣性演算法】】**
        你的最終列表**必須**代表 {top_n} 個「不同」的宏觀新聞主題。
        你必須遵循以下**內部思考步驟**來建構你的答案（不要在輸出中顯示這些步驟）：

        -   **步驟 1 (分析與分群)**：閱讀所有的新聞 `short` 內容。在你的內部分析中，將所有關於**同一個宏觀主題**的新聞歸為一類。
            -   *範例*：「候選人A的演說」、「候選人B的反應」、「選票統計結果」... 這些都屬於**單一的「選舉」主題**。
            -   *範例*：「地震災情」、「救援進度」、「捐款統計」... 這些都屬於**單一的「地震」主題**。

        -   **步驟 2 (主題內篩選)**：對於你分出的**每一個「宏觀主題」**，只挑選出**一篇**最能總結該事件、最重要、或最具代表性的 `story_id`。

        -   **步驟 3 (跨主題排序)**：彙總所有在步驟 2 中被選出的 `story_id`（現在你的候選列表都已是不同主題）。

        -   **步驟 4 (最終輸出)**：根據【第一優先】和【第二優先】的標準，對步驟 3 的候選列表進行最終排序，然後只輸出最重要的前 {top_n} 個。

        **結果**：你的最終輸出列表將因此**強制實現多樣性**，絕不會有多篇報導是關於同一個選舉、同一場災難或同一個政策辯論。
        ---

        **【== 嚴厲警告與最終指示 ==】**
        你的任務**絕對嚴格**，不容許任何錯誤。
        1.  **JSON 格式**：你的回應**必須**是、且**只能**是一個完全符合 Pydantic 模型的 JSON 物件。**嚴禁**在 JSON 物件之外添加任何文字、註解、道歉或 ```json 標記。
        2.  **數量準確**：`top_ten_story_ids` 列表**必須**剛好包含 {top_n} 个元素。
        3.  **規則遵守**：你**必須**嚴格遵守上述所有的「分層優先級」、「嚴格過濾」和「主題多樣性演算法」規則。

        任何偏離這些指示的行為都將被視為任務的完全失敗。
        ---

        你的回應**必須**是一個完全符合 Pydantic 模型的 JSON 物件。
        模型定義如下：
        class TopTenResponse(BaseModel):
            top_ten_story_ids: list[str]
    """
    
    user_prompt = f"""
    這是 {country} 今天的所有新聞資料。請根據你的角色和系統指示（特別是「分層優先級」、「嚴格過濾」和「主題多樣性」規則），
    分析以下 JSON 列表，並回傳前 {top_n} 大新聞的 `story_id`。

    新聞資料：
    {json.dumps(news_list, ensure_ascii=False)}
    """
    
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="application/json",
        response_schema=TopTenResponse,
        temperature=0.1
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
            
        