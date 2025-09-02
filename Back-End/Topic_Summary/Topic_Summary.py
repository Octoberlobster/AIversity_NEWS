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
    """使用 Gemini 生成專題摘要，並透過多步驟確保字數符合要求"""
    if not stories:
        return {
            "topic_title": topic_title, 
            "short_summary": "無相關新聞資料",
            "long_summary": "無相關新聞資料"
        }
    
    # 步驟 1: 建立初始 Prompt
    news_content = "\n".join([f"標題: {story['news_title']}\n摘要: {story['short']}" for story in stories])
    initial_prompt = f"""
        請根據以下新聞資料，為專題「{topic_title}」生成兩種長度的摘要：
        **重要：字數限制非常嚴格，請務必遵守**

        **撰寫要求：**
        1. 短摘要（約80字）：**絕對不可超過80字**。
        2. 長摘要（約200字）：**絕對不可超過200字**。

        **內容原則：**
        - 僅使用下方提供的新聞資料，不得添加資料外的資訊。
        - 使用正式、客觀的繁體中文。

        **輸出格式：**
        - 嚴格按照 JSON 格式輸出。

        **新聞資料：**
        {news_content}
    """    
    
    # 步驟 2: 第一次嘗試 (寬鬆生成，確保JSON完整)
    try:
        config = types.GenerateContentConfig(
            system_instruction="你是一個新聞摘要專家，專注於生成指定字數的摘要。字數控制是最高優先級。",
            response_mime_type="application/json",
            response_schema=TopicSummaryResponse.model_json_schema(),
            max_output_tokens=450,
            temperature=0.5
        )
        
        print(f"--- 第一次嘗試生成 '{topic_title}' 摘要 ---")
        response = gemini.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=initial_prompt,
            config=config
        )
        response_text = response.text.strip().removeprefix("```json").removesuffix("```").strip()
        result = json.loads(response_text)
        
        short_summary = result.get("short_summary", "")
        long_summary = result.get("long_summary", "")
        short_len, long_len = len(short_summary), len(long_summary)
        print(f"第一次生成長度：短摘要 {short_len} 字，長摘要 {long_len} 字")

        # 步驟 3: 驗證與第二次嘗試 (如果字數超標)
        if short_len > 80 or long_len > 200:
            print(f"--- 字數超標，進行第二次嚴格修正 ---")
            refine_prompt = f"""你上次為「{topic_title}」生成的摘要太長了。請根據以下原文，嚴格縮減到指定字數內：

            **你的目標：**
            1.  **短摘要**：從 {short_len} 字縮減到 **80字以內**。
            2.  **長摘要**：從 {long_len} 字縮減到 **200字以內**。

            **你的原文：**
            短摘要：「{short_summary}」
            長摘要：「{long_summary}」

            請重新提煉，只保留最核心的資訊，確保輸出是完整的 JSON 格式。
            """
            strict_config = types.GenerateContentConfig(
                system_instruction="你是一個文字精煉專家。你的唯一任務是縮減文字長度，同時保持核心意思。字數限制是絕對的！",
                response_mime_type="application/json",
                response_schema=TopicSummaryResponse.model_json_schema(),
                max_output_tokens=400,
                temperature=0.2
            )
            
            retry_response = gemini.models.generate_content(
                model="gemini-2.5-flash-lite", contents=refine_prompt, config=strict_config
            )
            retry_text = retry_response.text.strip().removeprefix("```json").removesuffix("```").strip()
            retry_result = json.loads(retry_text)

            short_summary = retry_result.get("short_summary", short_summary)
            long_summary = retry_result.get("long_summary", long_summary)
            print(f"第二次生成長度：短摘要 {len(short_summary)} 字，長摘要 {len(long_summary)} 字")

    except (json.JSONDecodeError, Exception) as e:
        print(f"生成摘要時發生錯誤: {e}")
        return {
            "topic_title": topic_title, 
            "short_summary": f"生成摘要失敗: {str(e)}",
            "long_summary": f"生成摘要失敗: {str(e)}"
        }

    # 步驟 4: 最終保障 (強制截斷)
    if len(short_summary) > 80:
        print(f"短摘要 ({len(short_summary)}字) 仍超標，強制截斷。")
        short_summary = short_summary[:80]
    if len(long_summary) > 200:
        print(f"長摘要 ({len(long_summary)}字) 仍超標，強制截斷。")
        long_summary = long_summary[:200]

    return {
        "topic_title": topic_title, 
        "short_summary": short_summary,
        "long_summary": long_summary
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