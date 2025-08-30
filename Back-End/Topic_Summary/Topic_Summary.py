import os, json
from supabase import create_client
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
from datetime import datetime

class TopicSummaryResponse(BaseModel):
    topic_title: str
    short_summary: str
    long_summary: str

def initialize_services():
    """初始化 Supabase 和 Gemini 服務連接"""
    load_dotenv()
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return supabase, gemini

def fetch_data_from_database(supabase):
    """從資料庫獲取專題和新聞資料"""
    topic = supabase.table("topic").select("topic_id, topic_title").execute()
    topic_news_map = supabase.table("topic_news_map").select("topic_id, story_id").execute()
    story_ids = [item["story_id"] for item in topic_news_map.data]
    news = supabase.table("single_news").select("story_id, news_title, short").in_("story_id", story_ids).execute() if story_ids else None

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

def generate_topic_summary(gemini, topic_title, stories):
    """使用 Gemini 生成專題摘要"""
    if not stories:
        return {
            "topic_title": topic_title, 
            "short_summary": "無相關新聞資料",
            "long_summary": "無相關新聞資料"
        }
    
    # 建立 prompt
    news_content = "\n".join([f"標題: {story['news_title']}\n摘要: {story['short']}" for story in stories])
    prompt = f"""請根據以下新聞資料，為專題「{topic_title}」生成兩種長度的摘要：
        **撰寫要求：**
        1. 短摘要（60-70字）：
        - 突出最核心的事件或發展
        - 包含關鍵數據或結果
        - 語調客觀中性，避免情緒性用詞
        - 嚴格控制在70字以內

        2. 長摘要（約150字）：
        - 提供事件背景與完整脈絡
        - 說明各方立場或影響
        - 包含時間軸和因果關係
        - 嚴格控制在150字左右

        **內容原則：**
        - 以事實為主，避免推測或評論
        - 使用正式書面語，避免口語化表達
        - 優先提及具體數字、日期、人物
        - 保持時序邏輯清晰
        - **重要：僅使用繁體中文，禁止使用任何其他語言文字**
        - **嚴格限制：僅使用下方提供的新聞資料，不得添加資料外的資訊**

        **輸出格式：**
        請嚴格按照 JSON 格式輸出，不要添加任何額外說明文字。
        所有內容必須是繁體中文，不得包含英文、阿拉伯文、日文或其他語言字符。
        摘要內容必須完全來自提供的新聞資料，不可加入外部知識。
        
        **新聞資料：**
        {news_content}
    """
    
    # 設定 config
    config = types.GenerateContentConfig(
        system_instruction="你是一個新聞摘要專家，請根據提供的新聞資料生成簡潔、客觀的專題摘要。短摘要應控制在60-70字內，突出最重要的信息；長摘要應控制在150字左右，提供更詳細的背景與發展。請嚴格按照指定的 JSON 格式輸出。重要：請只使用繁體中文，絕對不要使用其他語言文字（包括英文、阿拉伯文、日文等），確保所有文字都是正確的中文字符。請僅根據提供的新聞資料內容進行摘要，不要添加資料中沒有的資訊或背景知識。",
        response_mime_type="application/json",
        response_schema=TopicSummaryResponse.model_json_schema()
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
        return {
            "topic_title": topic_title, 
            "short_summary": result["short_summary"],
            "long_summary": result["long_summary"]
        }
    except json.JSONDecodeError as e:
        return {
            "topic_title": topic_title, 
            "short_summary": "生成摘要失敗: JSON解析錯誤",
            "long_summary": "生成摘要失敗: JSON解析錯誤"
        }
    except Exception as e:
        return {
            "topic_title": topic_title, 
            "short_summary": f"生成摘要失敗: {str(e)}",
            "long_summary": f"生成摘要失敗: {str(e)}"
        }

def update_topic_summaries_to_database(supabase, topic_summaries):
    """將生成的摘要存入資料庫"""

    current_time = datetime.now().strftime("%Y/%m/%d %H:%M")
    
    for topic_id, summary_data in topic_summaries.items():
        try:
            supabase.table("topic").update({
                "topic_short": summary_data["short_summary"],
                "topic_long": summary_data["long_summary"],
                "generated_date": current_time
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
            summary = generate_topic_summary(gemini, t_title, stories)
            topic_summaries[t_id] = summary
    
    # 將摘要存入資料庫
    update_topic_summaries_to_database(supabase, topic_summaries)
    
    # 將資料轉成 JSON 格式輸出
    result = topic_summaries
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()