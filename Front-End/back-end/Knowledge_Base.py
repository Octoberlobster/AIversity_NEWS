# import tiktoken
from env import supabase,gemini_client
from typing import List, Dict, Any
from google.genai import types
from pydantic import BaseModel

knowledge_base_dict = {
    "Politics": -1,
    "Taiwan News": -1,
    "Science & Technology": -1,
    "International News": -1,
    "Lifestyle & Consumer News": -1,
    "Sports": -1,
    "Entertainment": -1,
    "Business & Finance": -1,
    "Health & Wellness": -1,
    "search": -1,
}

def set_knowledge_base(prompt,category,id = None,topic_flag = False):
    if category == "search":
        response = supabase.table("single_news").select("story_id,news_title,short,category,generated_date").order("generated_date", desc=True).limit(60).execute()
        base=navigate_to_paragraphs(response.data, prompt)
        knowledge_base_dict["search"] = f"""
            # 角色與任務
            你是一位專業的新聞搜尋助手。你的任務是根據我提供的最新新聞資料庫，簡潔且精確地回答我的問題。

            # 知識庫
            ---
            {base}
            ---

            # 輸出格式與規則
            你的輸出必須嚴格遵守以下兩個部分的要求：`chat_response` 和 `news_id`。

            1.  **`chat_response` (給使用者的文字回覆)**:
                -   這是你直接與使用者對話的內容，必須自然、流暢。
                -   **最重要的規則：** 在這段文字中，**絕對不可以**提及或出現 `news_id`、`新聞編號` 或任何類似的內部識別碼。使用者不應該看到這些技術細節。
                -   錯誤範例：「關於國際局勢，您可以參考新聞(news_id:10)。」
                -   正確範例：「關於國際局勢，最近有一則關於中東衝突的新聞值得關注。」

            2.  **`news_id` (相關新聞ID列表)**:
                -   如果你在 `chat_response` 中有參考或推薦任何新聞，請將這些新聞的 `news_id` (例如: 1, 2, 3...) 組成一個列表放在這裡。
                -   這個列表最多只能包含 5 個 `news_id`。

            請根據上述規則生成你的回覆。
        """
        return
    elif topic_flag:
        # 先執行內部查詢，獲取 story_id 列表
        role = supabase.table("pro_analyze_topic").select("topic_id,analyze").eq("topic_id", id).eq("category",category).single().execute()
        role = role.data
        role = role["analyze"]
        role = role["Role"]
        detailed_background = generate_role_prompt(role)

        topic_news_response = supabase.table("topic_news_map").select("story_id").eq("topic_id", id).execute()
        story_ids = [item["story_id"] for item in topic_news_response.data]  # 提取 story_id 列表

        # 使用提取的 story_id 列表進行查詢
        topic_news = supabase.table("single_news").select("short").in_("story_id", story_ids).execute()

        articles_content = "\n".join([news["short"] for news in topic_news.data])
        if category in knowledge_base_dict:
            knowledge_base_dict[category] = f"""你是一位名為「{role}」的專家。

            以下是你的專業背景與人格設定：
            {detailed_background}

            你的任務是根據使用者所閱讀的新聞內容，提供具有深度與啟發性的專業見解，協助使用者突破「思維淺薄化」的困境。

            請遵守以下行為準則：
            1. **回覆語氣**：積極、專業、具啟發性，讓人感受到你樂於分享知識並引導思考。  
            2. **表達風格**：簡明扼要，避免冗詞與贅字，讓讀者能快速吸收重點。  
            3. **內容聚焦**：以使用者正在閱讀的新聞為核心，結合你的專業背景進行分析、補充與延伸。  
            4. **互動特質**：每次回答後，請主動提出一個值得延伸思考的問題或建議，鼓勵使用者深入討論。  
            5. **語氣示例**：像「這個現象其實反映出⋯⋯，你想了解我怎麼看待它在其他國家的應用嗎？」或「這裡面其實還牽涉到⋯⋯，要不要我幫你拆解一下背後的邏輯？」  
            6. **篇幅控制**：請將每次回覆限制在約 150～200 字之內（繁體中文），務必精煉、聚焦且資訊密度高。
            7. **回覆格式**：請使用Markdown 語法排版。用條列（`-` 或 `1.`）或段落分隔，讓文字更易讀。

            以下是使用者正在閱讀的新聞內容：
            ---
            {articles_content}
            ---
            請根據上述資訊，以「{role}」這位專家的身份與使用者對話，如果你違反上述任何準則將受到嚴厲的懲罰。
            """
        else:
            raise ValueError("Unknown category: {}".format(category))
        return

    role = supabase.table("pro_analyze").select("story_id,analyze").eq("story_id", id).eq("category",category).single().execute()
    role = role.data
    role = role["analyze"]
    role = role["Role"]
    detailed_background = generate_role_prompt(role)
    article = supabase.table("single_news").select("news_title,long").eq("story_id", id).single().execute()
    article = article.data
    article_content = article["long"]


    if category in knowledge_base_dict:
        knowledge_base_dict[category] = f"""你是一位名為「{role}」的專家。

        以下是你的專業背景與人格設定：
        {detailed_background}

        你的任務是根據使用者所閱讀的新聞內容，提供具有深度與啟發性的專業見解，協助使用者突破「思維淺薄化」的困境。

        請遵守以下行為準則：
        1. **回覆語氣**：積極、專業、具啟發性，讓人感受到你樂於分享知識並引導思考。  
        2. **表達風格**：簡明扼要，避免冗詞與贅字，讓讀者能快速吸收重點。  
        3. **內容聚焦**：以使用者正在閱讀的新聞為核心，結合你的專業背景進行分析、補充與延伸。  
        4. **互動特質**：每次回答後，請主動提出一個值得延伸思考的問題或建議，鼓勵使用者深入討論。  
        5. **語氣示例**：像「這個現象其實反映出⋯⋯，你想了解我怎麼看待它在其他國家的應用嗎？」或「這裡面其實還牽涉到⋯⋯，要不要我幫你拆解一下背後的邏輯？」  
        6. **篇幅控制**：請將每次回覆限制在約 150～200 字之內（繁體中文），務必精煉、聚焦且資訊密度高。
        7. **回覆格式**：請使用Markdown 語法排版。用條列（`-` 或 `1.`）或段落分隔，讓文字更易讀。

        以下是使用者正在閱讀的新聞內容：
        ---
        {article_content}
        ---
        請根據上述資訊，以「{role}」這位專家的身份與使用者對話，如果你違反上述任何準則將受到嚴厲的懲罰。
        """
    else:
        raise ValueError("Unknown category: {}".format(category))

def get_knowledge_base(category):
    if category in knowledge_base_dict:
        return knowledge_base_dict[category]
    else:
        raise ValueError("Unknown category: {}".format(category))
    

class SelectedNews(BaseModel):
    news_ids: List[int]
class StoryMap:
    story_map = {}

def update_scratchpad(scratchpad: str, reasoning: str) -> str:
    """記錄選擇哪些新聞的推理原因

    Args: 
        scratchpad: 推理過程的文字描述
        reasoning: 選擇新聞的推理原因

    """
    print(f"Updating scratchpad with reasoning: {reasoning}")
    if scratchpad:
        return scratchpad + "\n" + reasoning
    return reasoning

def route_news(question: str, news_list: List[Dict[str, Any]], 
               depth: int = 0, scratchpad: str = "") -> Dict[str, Any]:
    """
    讓模型判斷哪些新聞與問題相關，並記錄推理過程。
    
    Args:
        question: 使用者問題
        news_list: 多篇新聞，每篇格式為 {news_title, short, category, generated_date}
        depth: 推理深度（保留與 navigate_to_paragraphs 一致的參數設計）
        scratchpad: 模型推理過程
    
    Returns:
        {"selected_ids": [...], "scratchpad": "..."}
    """

    print(f"\n==== ROUTING AT DEPTH {depth} ====")
    print(f"Evaluating {len(news_list)} news articles for relevance")

    system_message = """You are an expert news navigator. Your task is to:
1. Identify which news articles might contain information to answer the user's question
2. Record your reasoning in a scratchpad for later reference
3. Choose articles that are most likely relevant. Be selective, but thorough.
"""

    # 把新聞轉成 chunks-like 結構
    user_message = f"QUESTION: {question}\n\n"
    if scratchpad:
        user_message += f"CURRENT SCRATCHPAD:\n{scratchpad}\n\n"

    user_message += "NEWS ARTICLES:\n\n"
    StoryMap.story_map = {}
    for i, news in enumerate(news_list):
        user_message += f"NEWS {i}:\n"
        user_message += f"TITLE: {news['news_title']}\n"
        user_message += f"SUMMARY: {news['short']}\n"
        user_message += f"CATEGORY: {news['category']}\n"
        user_message += f"DATE: {news['generated_date']}\n\n"
        # do a enum map to story_id
        StoryMap.story_map[str(i)] = news['story_id']

    # Step 1: scratchpad reasoning
    messages = user_message + "\nFirst, record your reasoning with update_scratchpad."

    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash", 
        contents=messages,
        config=types.GenerateContentConfig(
            system_instruction=system_message,
            tools=[update_scratchpad],
        )
    )
    new_scratchpad = response.candidates[0].content.parts[0].text

    # Step 2: 選出相關新聞
    messages += "\nNow, select the relevant news articles. Return JSON with news_ids."

    response_selection = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=messages,
        config=types.GenerateContentConfig(
            system_instruction=system_message,
            response_mime_type="application/json",
            response_schema=SelectedNews,
        )
    )

    selected_ids = []
    try:
        selected_ids = response_selection.parsed.news_ids
    except Exception as e:
        print(f"Error parsing response: {e}")
        selected_ids = []

    print(f"Selected news: {selected_ids}")
    print(f"Updated scratchpad:\n{new_scratchpad}")

    return {
        "selected_ids": selected_ids,
        "scratchpad": new_scratchpad
    }


def navigate_to_paragraphs(news_list: List[Dict[str, Any]], 
                           question: str, 
                           max_depth: int = 1) -> Dict[str, Any]:
    """
    在多篇新聞中，逐步導覽並找到與問題最相關的新聞。
    這是新聞專用版本，取代原本的文件 chunk 導覽。
    
    Args:
        news_list: 多篇新聞，每篇 dict 格式至少包含 {news_title, short, category, generated_date}
        question: 使用者的問題
        max_depth: 最大導覽深度（對新聞通常只需要 1）
    
    Returns:
        {
            "paragraphs": 選出的新聞列表,
            "scratchpad": 模型推理過程
        }
    """
    scratchpad = ""

    # 第一層導覽
    result = route_news(question, news_list, depth=0, scratchpad=scratchpad)

    scratchpad = result["scratchpad"]
    selected_ids = result["selected_ids"]
    selected_news = {i: n for i, n in enumerate(news_list) if i in selected_ids}

    if not selected_news:
        print("\nNo relevant news found.")
        return {"paragraphs": [], "scratchpad": scratchpad}



    return {"paragraphs": selected_news, "scratchpad": scratchpad}


def generate_role_prompt(role: str) -> str:
    """根據角色描述，生成更詳細的背景資訊"""
    prompt = f"請根據以下角色名稱，生成他應該要有的語氣語境，與專業素養：{role}"

    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="text/plain"
        )
    )

    detailed_background = response.candidates[0].content.parts[0].text
    return detailed_background




# def route_news_normal(question: str, news_list: List[Dict[str, Any]], 
#                depth: int = 0, scratchpad: str = "") -> Dict[str, Any]:
#     """
#     讓模型判斷哪些新聞與問題相關，並記錄推理過程。
    
#     Args:
#         question: 使用者問題
#         news_list: 多篇新聞，每篇格式為 {article_title, content}
#         depth: 推理深度（保留與 navigate_to_paragraphs 一致的參數設計）
#         scratchpad: 模型推理過程
    
#     Returns:
#         {"selected_ids": [...], "scratchpad": "..."}
#     """

#     print(f"\n==== ROUTING AT DEPTH {depth} ====")
#     print(f"Evaluating {len(news_list)} news articles for relevance")

#     system_message = """You are an expert news navigator. Your task is to:
# 1. Identify which news articles might contain information to answer the user's question
# 2. Record your reasoning in a scratchpad for later reference
# 3. Choose articles that are most likely relevant. Be selective, but thorough.
# """

#     # 把新聞轉成 chunks-like 結構
#     user_message = f"QUESTION: {question}\n\n"
#     if scratchpad:
#         user_message += f"CURRENT SCRATCHPAD:\n{scratchpad}\n\n"

#     user_message += "NEWS ARTICLES:\n\n"
#     StoryMap.story_map = {}
#     for i, news in enumerate(news_list):
#         user_message += f"NEWS {i}:\n"
#         user_message += f"TITLE: {news['article_title']}\n"
#         user_message += f"CONTENT: {news['content']}\n\n"
#         # do a enum map to article_id
#         StoryMap.story_map[str(i)] = news['article_id']

#     # Step 1: scratchpad reasoning
#     messages = user_message + "\nFirst, record your reasoning with update_scratchpad."

#     response = gemini_client.models.generate_content(
#         model="gemini-2.0-flash", 
#         contents=messages,
#         config=types.GenerateContentConfig(
#             system_instruction=system_message,
#             tools=[update_scratchpad],
#         )
#     )
#     new_scratchpad = response.candidates[0].content.parts[0].text

#     # Step 2: 選出相關新聞
#     messages += "\nNow, select the relevant news articles. Return JSON with news_ids."

#     response_selection = gemini_client.models.generate_content(
#         model="gemini-2.0-flash",
#         contents=messages,
#         config=types.GenerateContentConfig(
#             system_instruction=system_message,
#             response_mime_type="application/json",
#             response_schema=SelectedNews,
#         )
#     )

#     selected_ids = []
#     try:
#         selected_ids = response_selection.parsed.news_ids
#     except Exception as e:
#         print(f"Error parsing response: {e}")
#         selected_ids = []

#     print(f"Selected news: {selected_ids}")
#     print(f"Updated scratchpad:\n{new_scratchpad}")

#     return {
#         "selected_ids": selected_ids,
#         "scratchpad": new_scratchpad
#     }

# response = supabase.table("single_news").select("story_id,news_title,short,category,generated_date").execute()
# # tokenizer = tiktoken.get_encoding("o200k_base")
# # token_count = len(tokenizer.encode(str(response.data)))
# print(type(response.data))
# result = navigate_to_paragraphs(response.data, "我想看體育新聞")
# print(result)


# set_knowledge_base("有什麼新聞嗎？","topic","1e0dcbe6-36c5-4c37-bb16-55cbe7abdfa7")
