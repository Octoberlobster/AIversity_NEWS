import os, json
import time
from supabase import create_client
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
from datetime import datetime
from postgrest.exceptions import APIError

class TopicSummaryResponse(BaseModel):
    topic_title: str
    summary: str

def execute_with_retry(query, max_retries=5, initial_delay=1):
    """Execute a Supabase query with retry logic"""
    for attempt in range(max_retries):
        try:
            return query.execute()
        except APIError as e:
            if attempt == max_retries - 1:  # Last attempt
                raise  # Re-raise the last error if all retries failed
            delay = initial_delay * (2 ** attempt)  # Exponential backoff
            print(f"API Error occurred. Retrying in {delay} seconds... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)
    return None

def initialize_services():
    """初始化 Supabase 和 Gemini 服務連接"""
    load_dotenv()
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return supabase, gemini

def fetch_data_from_database(supabase):
    """從資料庫獲取專題和新聞資料"""
    try:
        # Get topics with retry
        topic_query = supabase.table("topic").select("topic_id, topic_title").eq("alive", 1)
        topic = execute_with_retry(topic_query)
        
        # Get topic news mapping with retry
        topic_news_map_query = supabase.table("topic_news_map").select("topic_id, story_id")
        topic_news_map = execute_with_retry(topic_news_map_query)
        
        story_ids = [item["story_id"] for item in topic_news_map.data]
        
        if not story_ids:
            return topic, topic_news_map, {}
        
        # Process story IDs in batches to avoid query size limits
        batch_size = 100
        news_data = []
        
        for i in range(0, len(story_ids), batch_size):
            batch_ids = story_ids[i:i + batch_size]
            news_query = supabase.table("single_news").select("story_id, news_title, short").in_("story_id", batch_ids)
            batch_result = execute_with_retry(news_query)
            if batch_result and batch_result.data:
                news_data.extend(batch_result.data)
            print(f"Processed {len(batch_ids)} stories ({i + len(batch_ids)}/{len(story_ids)})")
        
        news = type('NewsResponse', (), {'data': news_data})() if news_data else None
        
        # Build story map
        story_map = {item["story_id"]: item for item in news.data} if news and news.data else {}
        
        # Build topic to stories map
        topic_to_stories_map = {}
        for item in topic_news_map.data:
            t_id = item["topic_id"]
            s_id = item["story_id"]
            story_info = story_map.get(s_id)
            if story_info:
                entry = {
                    "news_title": story_info["news_title"],
                    "short": story_info["short"]
                }
                topic_to_stories_map.setdefault(t_id, []).append(entry)
        
        return topic, topic_news_map, topic_to_stories_map
        
    except Exception as e:
        print(f"Error fetching data from database: {str(e)}")
        return None, None, {}

    # 建立 story_id -> news 資料的 map
    story_map = {item["story_id"]: item for item in news.data} if news and news.data else {}
    # 建立 topic_id -> stories 的 map
    topic_to_stories_map = {}
    for item in topic_news_map.data:
        t_id = item["topic_id"]
        s_id = item["story_id"]
        story_info = story_map.get(s_id)
        if story_info:
            entry = {
                "news_title": story_info["news_title"],
                "short": story_info["short"]
            }
            topic_to_stories_map.setdefault(t_id, []).append(entry)
    return topic, topic_news_map, topic_to_stories_map

def generate_topic_summary(gemini, topic_title, stories, summary_type):
    """使用 Gemini 生成專題摘要"""
    if not stories:
        return {
            "topic_title": topic_title, 
            "short_summary": "無相關新聞資料",
            "long_summary": "無相關新聞資料"
        }
    
    # 建立 prompt
    news_content = "\n".join([f"標題: {story['news_title']}\n摘要: {story['short']}" for story in stories])
    
    if summary_type == "long":
        prompt = f"""請根據下方提供的新聞資料，為專題「{topic_title}」生成一份約 100 字的詳細摘要。

            **摘要要求：**
            - 長度：約 100 字，最長不應超過 120 字。
            - 內容：需提供事件背景與完整脈絡，說明各方立場或影響，並包含關鍵的時間軸與因果關係。
            - 風格：使用客觀、中性的正式書面語。
            
            **處理原則：**
            1.  **事實依據**：摘要內容必須完全基於下方提供的「新聞資料」，嚴禁添加任何外部資訊、個人推測或評論。
            2.  **關鍵資訊**：優先提及具體的數字、日期、人物等事實細節。
            3.  **語言要求**：內容必須為繁體中文。若原文包含無法或不宜翻譯的專有名詞（如 Apple、COVID-19），可直接沿用。

            **新聞資料：**
            ```
            {news_content}
            ```

            **輸出格式：**
            請嚴格按照以下 JSON 格式輸出，不要添加任何說明文字。
            ```json
            {{
                "topic_title": "{topic_title}",
                "summary": "（這裡放入生成的約 100 字摘要）"
            }}
            ```
        """
    elif summary_type == "short":
        prompt = f"""請根據下方提供的新聞資料，為專題「{topic_title}」生成一份 30 至 40 字的重點摘要。

            **摘要要求：**
            - 長度：嚴格控制在 30 至 40 字之間。
            - 內容：需突出最核心的事件或發展，包含關鍵數據或結果。
            - 風格：語調客觀中性，避免情緒性用詞。

            **處理原則：**
            1.  **事實依據**：摘要內容必須完全基於下方提供的「新聞資料」，嚴禁添加任何外部資訊、個人推測或評論。
            2.  **關鍵資訊**：優先提及具體的數字、日期、人物等事實細節。
            3.  **語言要求**：內容必須為繁體中文。若原文包含無法或不宜翻譯的專有名詞（如 Apple、COVID-19），可直接沿用。

            **新聞資料：**
            ```
            {news_content}
            ```

            **輸出格式：**
            請嚴格按照以下 JSON 格式輸出，不要添加任何說明文字。
            ```json
            {{
                "topic_title": "{topic_title}",
                "summary": "（這裡放入生成的 30-40 字摘要）"
            }}
            ```
        """

    # 設定 config
    config = types.GenerateContentConfig(
        system_instruction="你是一個新聞摘要專家，請根據提供的新聞資料生成簡潔、客觀的專題摘要。請嚴格按照指定的 JSON 格式輸出。重要：請只使用繁體中文，絕對不要使用其他語言文字（包括英文、阿拉伯文、日文等），確保所有文字都是正確的中文字符。請僅根據提供的新聞資料內容進行摘要，不要添加資料中沒有的資訊或背景知識。",
        response_mime_type="application/json",
        response_schema=TopicSummaryResponse,
    )
    
    try:
        response = gemini.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=config
        )
        response_text = response.text.strip()
        
        # 移除可能的 markdown 代碼塊格式
        if response_text.startswith("```json") and response_text.endswith("```"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```") and response_text.endswith("```"):
            # 處理沒有 json 標記的情況
            response_text = response_text[3:-3].strip()
        
        result = json.loads(response_text)
        print("type = ", summary_type, "Summary = ", result["summary"], len(result["summary"]))
        return {
            "topic_title": topic_title, 
            "summary": result["summary"],
        }
    except json.JSONDecodeError as e:
        return {
            "topic_title": topic_title, 
            "summary": "生成摘要失敗: JSON解析錯誤"
        }
    except Exception as e:
        return {
            "topic_title": topic_title, 
            "summary": f"生成摘要失敗: {str(e)}",
        }

def update_topic_summaries_to_database(supabase, topic_summaries):
    """將生成的摘要存入資料庫"""

    current_time = datetime.now().strftime("%Y/%m/%d %H:%M")
    
    for topic_id, summary_data in topic_summaries.items():
        try:
            supabase.table("topic").update({
                "topic_short": summary_data["short_summary"],
                "topic_long": summary_data["long_summary"],
                "update_date": current_time
            }).eq("topic_id", topic_id).execute()
            print(f"成功更新 topic {summary_data['topic_title']} 的摘要")
        except Exception as e:
            print(f"更新 topic {topic_id} 失敗: {str(e)}")

def main():
    supabase, gemini = initialize_services()
    topic, topic_news_map, topic_to_stories_map = fetch_data_from_database(supabase)
    
    # 只處理在 topic_news_map 中有對應的 topic_id
    topic_ids_with_news = set(topic_to_stories_map.keys())
    
    # 生成每個 topic 的摘要
    topic_summaries = {}
    for t in topic.data:
        t_id = t["topic_id"]
        t_title = t["topic_title"]
        # 只處理有新聞資料的 topic
        if t_id in topic_ids_with_news:
            stories = topic_to_stories_map.get(t_id, [])
            short_summary = generate_topic_summary(gemini, t_title, stories, "short")
            long_summary = generate_topic_summary(gemini, t_title, stories, "long")
            print("short summary len = ", len(short_summary["summary"]))
            print("long summary len = ", len(long_summary["summary"]))
            topic_summaries[t_id] = {
                "topic_title": t_title,
                "short_summary": short_summary["summary"],
                "long_summary": long_summary["summary"],
            }
    
    # 將摘要存入資料庫
    update_topic_summaries_to_database(supabase, topic_summaries)

if __name__ == "__main__":
    main()
    