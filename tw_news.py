from env import supabase, gemini_client
import time

def classify_taiwan_news():
    # Step 1️⃣ 查詢 stories 中 Taiwan News 的資料
    stories_response = supabase.table("stories").select("story_id, story_title").eq("category", "Taiwan News").execute()

    stories = stories_response.data or []
    print(f"📚 找到 {len(stories)} 筆 Taiwan News 資料")

    for story in stories:
        story_id = story["story_id"]
        title = story.get("story_title", "")

        # Step 2️⃣ 查詢 cleaned_news 中對應的 content
        news_response = supabase.table("cleaned_news").select("content").eq("story_id", story_id).execute()
        news_data = news_response.data or []

        if not news_data:
            print(f"⚠️ story_id={story_id} 無對應 cleaned_news 資料")
            continue

        content = news_data[0]["content"]

        # Step 3️⃣ 呼叫 Gemini 判斷分類
        prompt = f"""
你是一位新聞分類助手，請根據以下新聞內容，判斷它最接近哪一個類別：

內容：
{content}

請只回傳以下八類之一：
1. Politics
2. International News
3. Science & Technology
4. Lifestyle & Consumer
5. Sports
6. Entertainment
7. Business & Finance
8. Health & Wellness

補充說明：
若新聞主要與天氣、氣候或生活相關，請歸為 "Lifestyle & Consumer"；
若強調氣候變遷、環境科學或災害研究，請歸為 "Science & Technology"。

請只輸出類別名稱（不要多餘文字）。
"""

        try:
            gemini_response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            result = gemini_response.text.strip()
            print(f"📰 {title}（story_id={story_id}） ➜ {result}")

            # Step 4️⃣ 將結果寫回 Supabase
            update_response = supabase.table("stories").update({
                "category": result
            }).eq("story_id", story_id).execute()

            if update_response.data:
                print(f"✅ 已更新 category 至 {result}")
            else:
                print(f"⚠️ 更新失敗或無變化 (story_id={story_id})")

        except Exception as e:
            print(f"❌ Gemini 分析失敗（story_id={story_id}）：{e}")

        # 避免 API 過載
        time.sleep(1)


if __name__ == "__main__":
    classify_taiwan_news()
