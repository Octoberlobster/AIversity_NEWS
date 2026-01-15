# import tiktoken
from env import supabase,gemini_client
from typing import List, Dict, Any
from google.genai import types
from pydantic import BaseModel
import json
import os

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
    "topic": -1
}

def set_knowledge_base(prompt,category,topic_id = None):
    if category == "search":
        response = supabase.table("single_news").select("story_id,news_title,short,category,generated_date").execute()
        base=navigate_to_paragraphs(response.data, prompt)
        knowledge_base_dict["search"]= f"你是一位新聞搜尋助手，你目前的知識庫是：{base}，需要時參考這些資料來回答問題。並且為了考量閱讀者的閱讀喜好，請盡量回答簡短且精確的內容。此外如果你有想秀給使用者的新聞請使用news_id這個欄位填上知識庫中所屬的新聞號碼(例如:1,2,3,4...)，在推薦時不要超過五則新聞。"
        return
    elif category == "topic":
       # 先執行內部查詢，獲取 story_id 列表
        topic_news_response = supabase.table("topic_news_map").select("story_id").eq("topic_id", topic_id).execute()
        story_ids = [item["story_id"] for item in topic_news_response.data]  # 提取 story_id 列表

        # 使用提取的 story_id 列表進行查詢
        response = supabase.table("single_news").select("short").in_("story_id", story_ids).execute()

        knowledge_base_dict["topic"] = f"你是一位專家，並且你會考量使用者的閱讀習慣在回答時適時地分行與分段。你目前的知識庫是：{response.data}，需要時參考這些資料來回答問題。" + "\n\n請你像一般人一樣的聊天語氣回答問題，帶給使用者平易近人的體驗，回應的字數大約像是聊天那樣的形式，如果有超過一句話，可以使用markdown的語法來換行或分段。"
        return
    
    response = supabase.table("single_news").select("story_id,news_title,short,category,generated_date").eq("category", category).order("generated_date").execute()
    
    #用cleaned_news一篇一篇沒料
    # story_ids = [item["story_id"] for item in response.data]
    # response = supabase.table("cleaned_news").select("article_id,article_title,content").in_("story_id", story_ids).execute()
    #result = route_news_normal(prompt, response.data)
    #selected_ids = result["selected_ids"]
    #selected_news = {i: n for i, n in enumerate(response.data) if i in selected_ids}
    base = navigate_to_paragraphs(response.data, prompt)
    if category in knowledge_base_dict:
        knowledge_base_dict[category] = f"你是一位{category}的新聞專家。你目前的知識庫是：{base}，需要時參考這些資料來回答問題。\n請你像一般人一樣的聊天語氣回答問題，帶給使用者平易近人的體驗，並且你非常在乎使用者所以會積極關心和提出使用者下一步你可以為他做到什麼，回應的字數大約像是聊天那樣的形式，如果有超過一句話，可以使用markdown的語法來換行或分段。"
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