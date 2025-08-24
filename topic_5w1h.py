from env import supabase,gemini_client
from typing import List, Dict, Any
from google.genai import types
from pydantic import BaseModel
import json
import os

# 指定的故事ID列表
story_ids = [
    "b4079db5-b56f-4749-ab1e-4ebd5e05cd35",
    "da5c7d40-3334-430c-a9b8-430d4ddd721a",
    "c9bb094c-e220-4b42-8588-eb1f26d63e6a",
    "b86c4c4d-040c-4267-accc-99bf8b023dee",
    "ddfaadb5-023c-4b18-aefc-f08ab96e31be",
    "20617fe1-673e-4ccc-af3d-c52c1d05a5e2",
    "c08007e9-b8fc-4d8f-8444-d30474ff41d8",
    "8475d517-5182-42d9-9bd6-3b03645a7898",
    "76b5bb8d-56dc-4a8f-860e-5d56b0bd96f6"
]

knowledge_base_dict = {
    "5W1H_Analysis": -1,
    "search": -1
}

def set_knowledge_base(prompt, category="5W1H_Analysis"):
    """
    設定知識庫，使用指定的 story_id 列表
    
    Args:
        prompt: 使用者提供的事件或主題
        category: 分析類型，預設為 5W1H_Analysis
    """
    if category == "search":
        # 如果是搜尋模式，從指定的story_id中搜尋
        response = supabase.table("single_news").select("news_title,short,category,generated_date,story_id").in_("story_id", story_ids).execute()
        base = navigate_to_paragraphs(response.data, prompt)
        knowledge_base_dict["search"] = f"你是一個專業的新聞與專題 AI 助手，你目前的知識庫是：{base}，需要時參考這些資料來回答問題。"
        return
    
    # 從指定的story_id獲取資料
    response = supabase.table("single_news").select("news_title,short,category,generated_date,story_id").in_("story_id", story_ids).execute()
    base = navigate_to_paragraphs(response.data, prompt)
    
    # 設定5W1H分析的系統提示
    knowledge_base_dict["5W1H_Analysis"] = f"""你是一個專業的新聞與專題 AI 助手，專門提供某一事件或議題的簡明完整分析。請根據使用者提供的事件或主題，回答以下問題，並以簡潔、條列多點式的方式呈現，資訊要具體且完整：

1. Who（誰）：事件的主要人物、組織或群體。
2. What（什麼）：事件的核心內容或行動。
3. When（何時）：事件發生的時間或期間。
4. Where（哪裡）：事件發生的地點或範圍。
5. Why（為什麼）：事件的原因、背景或動機。
6. How（如何發生）：事件的過程或運作方式。

要求：
- 內容必須正確且可驗證。
- 條列簡明扼要，不超過 5 行文字/每個 5W1H。
- 使用清楚、正式的新聞或報告風格語言。
- 不提供無關資訊或個人評論。

你目前的知識庫是：{base}，需要時參考這些資料來進行5W1H分析。

最後將結果輸出成json格式，並存放至 output_folder = "json/5W1H"。

例子輸入：大罷免
例子輸出：
{{
  "Who": ["某政黨議員", "罷免發起團體"],
  "What": ["發起對特定議員的罷免投票"],
  "When": ["2025年8月"],
  "Where": ["某縣市選區"],
  "Why": ["對議員施政不滿或爭議事件"],
  "How": ["依選舉法進行公民投票"]
}}"""

def get_knowledge_base(category="5W1H_Analysis"):
    """
    取得知識庫內容
    
    Args:
        category: 分析類型，預設為 5W1H_Analysis
    
    Returns:
        知識庫的系統提示內容
    """
    if category in knowledge_base_dict:
        return knowledge_base_dict[category]
    else:
        raise ValueError("Unknown category: {}".format(category))

class SelectedNews(BaseModel):
    news_ids: List[int]

class Analysis5W1H(BaseModel):
    """5W1H分析結果的資料結構"""
    Who: List[str]
    What: List[str]
    When: List[str]
    Where: List[str]
    Why: List[str]
    How: List[str]

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
        news_list: 多篇新聞，每篇格式為 {news_title, short, category, generated_date, story_id}
        depth: 推理深度（保留與 navigate_to_paragraphs 一致的參數設計）
        scratchpad: 模型推理過程
    
    Returns:
        {"selected_ids": [...], "scratchpad": "..."}
    """

    print(f"\n==== ROUTING AT DEPTH {depth} ====")
    print(f"Evaluating {len(news_list)} news articles for relevance")

    system_message = """You are an expert news navigator for 5W1H analysis. Your task is to:
1. Identify which news articles might contain information to answer the user's question for 5W1H analysis
2. Record your reasoning in a scratchpad for later reference
3. Choose articles that are most likely relevant for Who, What, When, Where, Why, How analysis. Be selective, but thorough.
"""

    # 把新聞轉成 chunks-like 結構
    user_message = f"QUESTION FOR 5W1H ANALYSIS: {question}\n\n"
    if scratchpad:
        user_message += f"CURRENT SCRATCHPAD:\n{scratchpad}\n\n"

    user_message += "NEWS ARTICLES:\n\n"
    for i, news in enumerate(news_list):
        user_message += f"NEWS {i}:\n"
        user_message += f"TITLE: {news['news_title']}\n"
        user_message += f"SUMMARY: {news['short']}\n"
        user_message += f"CATEGORY: {news['category']}\n"
        user_message += f"STORY_ID: {news.get('story_id', 'N/A')}\n\n"

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
    messages += "\nNow, select the relevant news articles for 5W1H analysis. Return JSON with news_ids."

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
    在多篇新聞中，逐步導覽並找到與問題最相關的新聞，專為5W1H分析優化。
    
    Args:
        news_list: 多篇新聞，每篇 dict 格式至少包含 {news_title, short, category, generated_date, story_id}
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
    selected_news = [n for i, n in enumerate(news_list) if i in selected_ids]

    if not selected_news:
        print("\nNo relevant news found for 5W1H analysis.")
        return {"paragraphs": [], "scratchpad": scratchpad}

    # 如果只需要一層，就直接回傳
    if max_depth == 1:
        print(f"\nReturning {len(selected_news)} relevant news for 5W1H analysis at depth 0")
        return {"paragraphs": selected_news, "scratchpad": scratchpad}

    # 如果要更深層（例如將一篇新聞再拆成更小的單位），
    # 可以在這裡進一步實作（但新聞通常不需要）
    return {"paragraphs": selected_news, "scratchpad": scratchpad}

def analyze_5W1H(topic: str) -> Dict[str, Any]:
    """
    執行5W1H分析的主要函數
    
    Args:
        topic: 要分析的事件或主題（例如："2025台灣大罷免"）
    
    Returns:
        5W1H分析結果的字典
    """
    # 設定知識庫
    set_knowledge_base(topic, "5W1H_Analysis")
    
    # 取得系統提示
    system_instruction = get_knowledge_base("5W1H_Analysis")
    
    # 讓AI進行5W1H分析
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"請對以下主題進行5W1H分析：{topic}",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=Analysis5W1H,
        )
    )
    
    try:
        analysis_result = response.parsed
        result_dict = {
            "Who": analysis_result.Who,
            "What": analysis_result.What,
            "When": analysis_result.When,
            "Where": analysis_result.Where,
            "Why": analysis_result.Why,
            "How": analysis_result.How
        }
        
        # 儲存到JSON檔案
        output_folder = "json/5W1H"
        os.makedirs(output_folder, exist_ok=True)
        
        filename = f"{output_folder}/{topic.replace(' ', '_')}_5W1H.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, ensure_ascii=False, indent=2)
        
        print(f"5W1H analysis saved to: {filename}")
        return result_dict
        
    except Exception as e:
        print(f"Error in 5W1H analysis: {e}")
        return {}

# 使用範例
if __name__ == "__main__":
    # 分析烏俄戰爭
    result = analyze_5W1H("烏俄戰爭")
    print(json.dumps(result, ensure_ascii=False, indent=2))