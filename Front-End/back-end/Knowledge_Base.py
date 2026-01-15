import logging
from typing import List, Dict, Any
from pydantic import BaseModel
from google.genai import types
from env import supabase, gemini_client

# 設置日誌
# logging.basicConfig(level=logging.INFO) # Can be configured in app.py
logger = logging.getLogger(__name__)

# <<< ADDED: Import the necessary Pydantic model >>>
# Assuming NewExpertResponse is defined consistently in both Change_experts files
# If they differ, you might need to adjust the import or define a common model
try:
    # Attempt to import from Change_experts, adjust path if necessary
    from Change_experts import NewExpertResponse
except ImportError:
    # Fallback or define a basic structure if import fails (less ideal)
    logger.warning("Could not import NewExpertResponse from Change_experts. Using a basic definition.")
    class NewExpertResponse(BaseModel):
        Role: str
        Analyze: str




# --- Pydantic 模型定義 for Search Response ---
class SelectedNews(BaseModel):
    news_ids: List[int]

class StoryMap:
    story_map = {} # Class variable to hold mapping for search results

# --- Language Mapping ---
language_map = {
    "zh-TW": "繁體中文 (Traditional Chinese)",
    "en-US": "English (US)",
    "ja-JP": "日本語 (Japanese)",
    "id-ID": "Bahasa Indonesia (Indonesian)"
}

# --- Knowledge Base Dictionary ---
knowledge_base_dict = {
    "Politics": -1,
    "Taiwan News": -1,
    "Science & Technology": -1,
    "International News": -1,
    "Lifestyle & Consumer": -1,
    "Sports": -1,
    "Entertainment": -1,
    "Business & Finance": -1,
    "Health & Wellness": -1,
    "search": -1,
    # This dictionary will be dynamically updated for non-search categories
}

# --- Helper Functions ---

def generate_role_prompt(role: str) -> str:
    """根據角色描述，生成更詳細的背景資訊"""
    # <<< MODIFIED: Use a more robust language parameter if needed >>>
    # For now, assumes the role name itself guides the language implicitly or uses default
    prompt = f"請根據以下角色名稱，生成他應該要有的語氣語境，與專業素養：{role}"
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash", # Consider using a slightly more powerful model if needed for nuance
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="text/plain" # Expect plain text for background
            )
        )
        # Add basic validation for response content
        if response and response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
             detailed_background = response.candidates[0].content.parts[0].text
             logger.info(f"Generated detailed background for role: {role}")
             return detailed_background
        else:
            logger.warning(f"Gemini did not return valid background for role: {role}. Using role name as background.")
            return role # Fallback to just the role name
    except Exception as e:
        logger.error(f"Error generating role prompt for '{role}': {e}")
        return role # Fallback to just the role name

def update_scratchpad(scratchpad: str, reasoning: str) -> str:
    """記錄選擇哪些新聞的推理原因 (for search)"""
    logger.debug(f"Updating scratchpad with reasoning: {reasoning}")
    if scratchpad:
        return scratchpad + "\n" + reasoning
    return reasoning

def route_news(question: str, news_list: List[Dict[str, Any]],
               depth: int = 0, scratchpad: str = "") -> Dict[str, Any]:
    """
    讓模型判斷哪些新聞與問題相關 (for search)。
    """
    logger.info(f"Routing news at depth {depth} for question: '{question}'")
    logger.debug(f"Evaluating {len(news_list)} news articles.")

    system_message = """You are an expert news navigator. Your task is to:
1. Identify which news articles might contain information to answer the user's question.
2. Record your reasoning in a scratchpad for later reference.
3. Choose articles that are most likely relevant. Be selective, but thorough.
Return ONLY the JSON structure specified in the tool schema, do not add extra explanations.
"""

    user_message = f"QUESTION: {question}\n\n"
    if scratchpad:
        user_message += f"CURRENT SCRATCHPAD:\n{scratchpad}\n\n"

    user_message += "NEWS ARTICLES:\n\n"
    StoryMap.story_map = {} # Reset story map for this search routing
    for i, news in enumerate(news_list):
        # Ensure essential keys exist, provide defaults if missing
        title = news.get('news_title', 'No Title')
        summary = news.get('short', 'No Summary')
        category = news.get('category', 'Uncategorized')
        date = news.get('generated_date', 'No Date')
        story_id = news.get('story_id', f'temp_id_{i}') # Use temporary ID if original missing

        user_message += f"NEWS {i}:\n"
        user_message += f"TITLE: {title}\n"
        user_message += f"SUMMARY: {summary}\n"
        user_message += f"CATEGORY: {category}\n"
        user_message += f"DATE: {date}\n\n"
        StoryMap.story_map[str(i)] = story_id # Map index (as string) to original story_id

    # Step 1: Scratchpad reasoning (using function calling)
    scratchpad_tool = types.FunctionDeclaration(
        name="update_scratchpad",
        description="Records the reasoning for selecting news articles.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "scratchpad": types.Schema(type=types.Type.STRING),
                "reasoning": types.Schema(type=types.Type.STRING),
            },
            required=["scratchpad", "reasoning"],
        ),
    )
    # Step 2: Selecting news (JSON schema)
    select_news_schema = types.Schema(
            type=types.Type.OBJECT,
            properties={
                 "news_ids": types.Schema(
                      type=types.Type.ARRAY,
                      items=types.Schema(type=types.Type.INTEGER),
                      description="List of integer indices corresponding to the relevant NEWS articles."
                 )
            },
            required=["news_ids"]
         )


    try:
         # Combined request for reasoning and selection
         full_prompt = user_message + "\nReason about which articles are relevant, then select their indices."
         response = gemini_client.models.generate_content(
             model="gemini-2.0-flash", # Or a more capable model if needed
             contents=full_prompt,
             config=types.GenerateContentConfig(
                 system_instruction=system_message,
                 response_mime_type="application/json",
                 response_schema=select_news_schema # Focus on getting the selected IDs
             ),
            # tools=[scratchpad_tool] # If you need the reasoning step explicitly separated
         )

         # Extract selected IDs directly
         selected_ids = []
         if response and response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
              parsed_response = response.parsed # Access the parsed Pydantic object directly
              if parsed_response and isinstance(parsed_response, SelectedNews): # Check type
                  selected_ids = parsed_response.news_ids
                  logger.info(f"Selected news indices: {selected_ids}")
              else:
                   logger.warning(f"Could not parse SelectedNews from response: {response.text}")
         else:
              logger.warning(f"No valid content in selection response: {response}")

         # Placeholder for scratchpad if you separate the calls or need a default
         new_scratchpad = scratchpad + "\n(Reasoning step skipped or combined)"

    except Exception as e:
         logger.error(f"Error during news routing with Gemini: {e}", exc_info=True)
         selected_ids = []
         new_scratchpad = scratchpad + f"\nError during routing: {e}"


    logger.info(f"Selected news indices: {selected_ids}")
    logger.debug(f"Updated scratchpad:\n{new_scratchpad}")

    return {
        "selected_ids": selected_ids,
        "scratchpad": new_scratchpad
    }


def navigate_to_paragraphs(news_list: List[Dict[str, Any]],
                           question: str,
                           max_depth: int = 1) -> Dict[str, Any]:
    """
    導覽新聞列表找到相關新聞 (for search)。
    """
    scratchpad = ""
    logger.info(f"Navigating paragraphs for question: '{question}'")

    # Only one level needed for news list typically
    result = route_news(question, news_list, depth=0, scratchpad=scratchpad)

    scratchpad = result["scratchpad"]
    selected_ids = result["selected_ids"]

    # Filter the original news_list based on selected indices
    selected_news_dict = {
         i: news for i, news in enumerate(news_list) if i in selected_ids
     }
    selected_news_list = list(selected_news_dict.values()) # Keep as list for consistency if needed downstream

    if not selected_news_list:
        logger.warning("No relevant news found after routing.")
        return {"paragraphs": [], "scratchpad": scratchpad}

    logger.info(f"Found {len(selected_news_list)} relevant news articles.")
    return {"paragraphs": selected_news_list, "scratchpad": scratchpad} # Return list

# --- Main Functions ---

def set_knowledge_base(prompt, category, id=None, topic_flag=False, language="zh-TW", role=None, analyze=None):
    """
    Sets the system instruction for a specific category in the knowledge_base_dict.
    Now directly accepts role and analyze for non-search categories.
    """
    output_language = language_map.get(language, "繁體中文 (Traditional Chinese)")
    language_instruction = f"\n\n# 語言規則\n- 你必須嚴格使用「{output_language}」來回覆所有內容。"
    logger.info(f"Setting knowledge base for category: {category}, language: {language}, topic_flag: {topic_flag}")

    if category == "search":
        try:
            # --- MODIFICATION START ---
            # 透過 !inner JOIN 一次性查詢 single_news 並過濾 stories.country
            # 假設 'single_news' 表有 'story_id' 欄位作為外鍵關聯到 'stories' 表的 'story_id'
            
            response = (
                supabase.table("single_news")
                .select("story_id, news_title, short, category, generated_date, stories!inner(country)") # 請求 JOIN
                .eq("stories.country", "Taiwan")  # 對 JOIN 的 'stories' 表下篩選條件
                .order("generated_date", desc=True)
                .limit(60) # 限制 60 筆最新的台灣新聞
                .execute()
            )
            
            # --- MODIFICATION END ---

            if not response.data:
                 logger.warning("No recent news found for search knowledge base (post-filter).")
                 news_base_content = "目前無法獲取最新台灣新聞。"
            else:
                 # Find relevant news based on the prompt
                 navigation_result = navigate_to_paragraphs(response.data, prompt)
                 relevant_news = navigation_result.get("paragraphs", [])
                 if not relevant_news:
                     logger.warning(f"No relevant news found for prompt: '{prompt}'. Using generic base.")
                     # Fallback: maybe use top N news titles/summaries
                     news_base_content = "\n".join([f"ID {n['story_id']}: {n['news_title']} - {n['short']}" for n in response.data[:5]]) # Limit fallback size
                 else:
                     news_base_content = "\n".join([f"ID {n['story_id']}: {n['news_title']} - {n['short']}" for n in relevant_news])

            original_instruction = f"""
                 # 角色與任務
                 你是一位專業的新聞搜尋助手。你的任務是根據我提供的最新新聞資料庫，簡潔且精確地回答我的問題。

                 # 知識庫 (相關新聞摘要)
                 ---
                 {news_base_content}
                 ---

                 # 輸出格式與規則
                 你的輸出必須嚴格遵守以下兩個部分的要求：`chat_response` 和 `news_id` (JSON Schema: {{ "news_id": List[str], "chat_response": str }}).

                 1.  **`chat_response` (給使用者的文字回覆)**:
                     -   這是你直接與使用者對話的內容，必須自然、流暢、簡潔。
                     -   根據知識庫中的新聞內容回答問題。
                     -   如果知識庫沒有相關資訊，禮貌地告知使用者。
                     -   **最重要的規則：** 在這段文字中，**絕對不可以**提及或出現 `news_id`、`新聞編號` 或任何類似的內部識別碼。使用者不應該看到這些技術細節。

                 2.  **`news_id` (相關新聞ID列表)**:
                     -   如果你在 `chat_response` 中有參考或推薦任何知識庫中的新聞，請將這些新聞的 `story_id` (從知識庫中提取，例如 "ID 12345: Title - Summary" 中的 12345) 組成一個**字串列表**放在這裡。
                     -   這個列表最多只能包含 5 個 `story_id`。
                     -   如果回答沒有參考任何具體新聞，返回空列表 `[]`。

                 請根據上述規則生成你的回覆。
             """
            knowledge_base_dict["search"] = original_instruction + language_instruction
            logger.info("Knowledge base set for 'search' category.")
        except Exception as e:
             logger.error(f"Error setting knowledge base for 'search': {e}", exc_info=True)
             knowledge_base_dict["search"] = "作為新聞搜尋助手，我目前無法訪問資料庫，請稍後再試。" + language_instruction # Fallback instruction


        return

    # --- Logic for single news or topic (non-search) ---
    if role is None:
        logger.warning(f"Role not provided for category {category}. Using a default role.")
        role = f"{category} 領域專家" # Generate a default role based on category
        # If analyze is also missing, generate a default one or handle error
        if analyze is None:
            analyze = "針對此主題提供專業見解。"


    # Generate detailed background based on the (provided or default) role
    detailed_background = generate_role_prompt(role)

    articles_content = ""
    try:
        if topic_flag:
            # Fetch topic related news content (remains the same)
            topic_news_response = supabase.table("topic_news_map").select("story_id").eq("topic_id", id).execute()
            story_ids = [item["story_id"] for item in topic_news_response.data] if topic_news_response.data else []
            if story_ids:
                topic_news = supabase.table("single_news").select("short").in_("story_id", story_ids).execute()
                articles_content = "\n".join([news.get("short", "") for news in topic_news.data]) if topic_news.data else ""
            if not articles_content: # Fetch topic description as fallback
                 topic_info = supabase.table("topic").select("topic_long, topic_short").eq("topic_id", id).single().execute()
                 if topic_info.data:
                      articles_content = topic_info.data.get("topic_long") or topic_info.data.get("topic_short") or "此專題尚無內容。"
                 else:
                      articles_content = "無法獲取專題內容。"

        else: # Single news
            # Fetch single news content (remains the same)
            article = supabase.table("single_news").select("long").eq("story_id", id).single().execute()
            if article.data:
                articles_content = article.data.get("long", "無法獲取新聞內容。")
            else:
                 articles_content = "無法獲取新聞內容。"

    except Exception as e:
        logger.error(f"Error fetching content for category '{category}', ID '{id}', topic_flag={topic_flag}: {e}", exc_info=True)
        articles_content = "無法獲取相關內容。"

    # Define the instruction template (remains the same)
    original_instruction = f"""你是一位名為「{role}」的專家。

    以下是你的專業背景與人格設定：
    {detailed_background}

    你的任務是根據使用者所閱讀的新聞內容，提供具有深度與啟發性的專業見解，協助使用者突破「思維淺薄化」的困境。

    請遵守以下行為準則：
    1. **回覆語氣**：積極、專業、具啟發性，讓人感受到你樂於分享知識並引導思考。
    2. **表達風格**：簡明扼要，避免冗詞與贅字，讓讀者能快速吸收重點。
    3. **內容聚焦**：以使用者正在閱讀的內容為核心，結合你的專業背景進行分析、補充與延伸。
    4. **互動特質**：每次回答後，請主動提出一個值得延伸思考的問題或建議，鼓勵使用者深入討論。
    5. **語氣示例**：像「這個現象其實反映出⋯⋯，你想了解我怎麼看待它在其他國家的應用嗎？」或「這裡面其實還牽涉到⋯⋯，要不要我幫你拆解一下背後的邏輯？」
    6. **篇幅控制**：請將每次回覆限制在約 150～200 字之內（{output_language}），務必精煉、聚焦且資訊密度高。
    7. **回覆格式**：請使用Markdown 語法排版。用條列（`-` 或 `1.`）或段落分隔，讓文字更易讀。

    以下是使用者正在閱讀的內容：
    ---
    {articles_content}
    ---
    請根據上述資訊，以「{role}」這位專家的身份與使用者對話，如果你違反上述任何準則將受到嚴厲的懲罰。
    你的輸出必須嚴格符合 JSON Schema: {{ "Role": str, "Analyze": str }}
    """

    # Store the instruction using the category name as the key
    knowledge_base_dict[category] = original_instruction + language_instruction
    logger.info(f"Knowledge base set for category: '{category}' (dynamic or predefined).")


def get_knowledge_base(category, language="zh-TW"): # <<< MODIFIED slightly for clarity
    """Retrieves the system instruction for a given category."""
    if category in knowledge_base_dict and knowledge_base_dict[category] != -1:
        logger.info(f"Retrieved knowledge base for category: {category}")
        return knowledge_base_dict[category]
    else:
        # Handle cases where the knowledge base hasn't been set yet or category is unknown
        logger.warning(f"Knowledge base not set or category '{category}' unknown. Returning default/error prompt.")
        # Provide a generic fallback or raise an error
        output_language = language_map.get(language, "繁體中文 (Traditional Chinese)")
        language_instruction = f"\n\n# 語言規則\n- 你必須嚴格使用「{output_language}」來回覆所有內容。"
        fallback_instruction = f"我是一位通用助手。請告訴我你想討論什麼。\n\n# 輸出格式\n你的輸出必須嚴格符合 JSON Schema: {{ \"Role\": str, \"Analyze\": str }}"
        return fallback_instruction + language_instruction
        # Alternatively: raise ValueError("Knowledge base not set for category: {}".format(category))
