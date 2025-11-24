import re
import json
from typing import List, Dict, Any
from env import supabase, gemini_client
from pydantic import BaseModel
from google.genai import types

class AttributionResponse(BaseModel):
    matching_chunk_ids: List[str]

GENERATIVE_MODEL = "gemini-2.5-flash-lite" 

def chunk_text_by_paragraph(text: str) -> list[str]:
    if not text:
        return []
    chunks = re.split(r'\n\s*\n', text)
    return [chunk.strip() for chunk in chunks if chunk.strip()]

def attribute_sources_for_story(story_id: str) -> List[Dict[str, Any]]:
    """
    接收一個 story_id，自動從 Supabase 抓取資料，
    為「整合稿的每一段」呼叫 Gemini API 進行比對，並回傳標註好的結果。
    """
    
    print(f"--- 開始自動歸因任務 (Call Gemini API)：{story_id} ---")
    
    # --- 步驟 1: 抓取資料與切割 (與前一版相同) ---
    try:
        single_news_data = supabase.table("single_news").select("long").eq("story_id", story_id).execute().data
        if not single_news_data or not single_news_data[0].get("long"):
            print("錯誤：在 Supabase 中找不到此 story_id 的 'single_news' 或 'long' 內容。")
            return []
        single_news_text = single_news_data[0].get("long")
        
        cleaned_news_data = supabase.table("cleaned_news").select("media, content, article_id").eq("story_id", story_id).execute().data
        if not cleaned_news_data:
            print("錯誤：在 Supabase 中找不到此 story_id 的 'cleaned_news'。")
            return []
            
    except Exception as e:
        print(f"錯誤：從 Supabase 讀取資料失敗: {e}")
        return []

    print(f"總共抓取到 {len(cleaned_news_data)} 筆來源新聞資料。")

    # 處理來源新聞
    source_chunks_db = []
    source_context_string = "" # 用來建立給 API 看的「來源資料庫」字串
    chunk_id_to_source_map = {} # 用來將 API 回傳的 chunk_id 轉回 (media, article_id)

    for item in cleaned_news_data:
        media = item.get("media")
        content = item.get("content")
        article_id = item.get("article_id")
        
        if not (content and media and article_id):
            print(f"警告：跳過一筆資料，缺少 media, content 或 article_id。")
            continue
            
        chunks = chunk_text_by_paragraph(content)
        for i, chunk_text in enumerate(chunks):
            # 建立一個在本次任務中唯一的 chunk_id
            chunk_id = f"{article_id}_p{i+1}"
            
            source_chunks_db.append({
                "media": media,
                "article_id": article_id,
                "chunk_id": chunk_id,
                "text": chunk_text
            })
            
            # 建立給 Prompt 用的資料庫字串
            source_context_string += f"[{chunk_id}]: {chunk_text}\n\n"
            # 建立 Python 映射表
            chunk_id_to_source_map[chunk_id] = (media, article_id)

    # 處理整合新聞
    single_news_chunks_db = []
    single_news_chunks = chunk_text_by_paragraph(single_news_text)
    for i, chunk_text in enumerate(single_news_chunks):
        single_news_chunks_db.append({
            "chunk_id": f"{story_id}_part_{i+1}",
            "text": chunk_text
        })

    if not source_chunks_db or not single_news_chunks_db:
        print("錯誤：來源新聞或整合新聞切割後為空，任務中止。")
        return []
        
    print(f"步驟 1 完成：{len(source_chunks_db)} 個來源區塊，{len(single_news_chunks_db)} 個整合區塊。")

    # --- 步驟 2 & 3: 迭代呼叫 Gemini API 進行比對 ---

    # 這是我們的「歸因提示」模板
    USER_PROMPT_TEMPLATE = """
    【任務開始】

    **1. 原始來源區塊 (資料庫):**
    {source_context}

    **2. 待分析的整合段落:**
    {generated_paragraph}

    **3. 你的分析與歸因:**
    請嚴格按照你的核心原則，分析「待分析的整合段落」中的所有事實，並在「原始來源區塊」中找出所有支持這些事實的 `chunk_id`。

    **4. 輸出:**
    請僅回傳 JSON 物件。
    """
    
    SYSTEM_INSTRUCTION = """
    你是一個嚴謹的新聞歸因（Attribution）專家。
    你的任務是逐一分析「待分析整合段落」中的**每一項事實主張 (claim)**，
    然後在「原始來源區塊」中，找出**所有**包含了該項主張的**具體證據**。

    **核心原則：**
    1.  **基於事實，而非主題：** 絕對不要因為兩個區塊都在談論「徐國勇」或「光復節」就進行匹配。匹配的唯一依據是「整合段落」中的**具體事實**（例如：「蔣萬安反問...」）是否**直接出現**在「來源區塊」中。
    2.  **接受轉述 (Paraphrasing)：** 整合段落可能是對來源的「改寫」或「總結」。例如，來源的「...賴清德是哪一國的總統？」和整合的「...反問總統賴清德的國籍...」是**有效匹配**。
    3.  **100% 嚴謹：** 如果一個來源區塊**沒有**包含整合段落中的任何具體事實，**絕對不能**將其列入。
    4.  **格式：** 永遠嚴格遵守使用者提供的 JSON 格式和 `response_schema`。
    """
    
    print("步驟 2/3 開始：迭代呼叫 Gemini API 進行比對...")
    final_annotated_article = []

    for gen_chunk in single_news_chunks_db:
        print(f"  > 正在分析整合區塊: {gen_chunk['chunk_id']}...")
        
        # 1. 建構完整的提示
        prompt = USER_PROMPT_TEMPLATE.format(
            source_context=source_context_string,
            generated_paragraph=gen_chunk['text']
        )
        
        config = types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=AttributionResponse,
                temperature=0.0
            )
        # 2. 呼叫 Gemini API
        try:
            response = gemini_client.models.generate_content(
                model=GENERATIVE_MODEL,
                contents=prompt,
                config=config
            )
            
            # 3. 解析 JSON 回應
            response_data = json.loads(response.text)
            matching_chunk_ids = response_data.get("matching_chunk_ids", [])
            
            # 4. 將 API 回傳的 chunk_ids 轉換回 (media, article_id)
            matched_sources_tuples = []
            for chunk_id in matching_chunk_ids:
                if chunk_id in chunk_id_to_source_map:
                    matched_sources_tuples.append(chunk_id_to_source_map[chunk_id])
                else:
                    print(f"    > 警告：Gemini 回傳了未知的 chunk_id: {chunk_id}")
            
            # 5. 去除重複的 (media, article_id)
            unique_sources = list(set(matched_sources_tuples))
            
            # 6. 整理結果
            final_annotated_article.append({
                "generated_text": gen_chunk['text'],
                "sources_data": unique_sources
            })
            print(f"    > 完成。找到 {len(unique_sources)} 個唯一來源。")

        except Exception as e:
            print(f"    > 錯誤：API 呼叫或 JSON 解析失敗: {e}")
            final_annotated_article.append({
                "generated_text": gen_chunk['text'],
                "sources_data": [] # 失敗時回傳空列表
            })

    print("--- 自動歸因任務完成 ---")
    return final_annotated_article

def format_attribution_to_json(annotated_result: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    將歸因結果轉換為資料庫所需的 JSON 格式
    格式: {"part1": ["article_id1", "article_id2"], "part2": [...], ...}
    """
    result = {}
    for i, item in enumerate(annotated_result, 1):
        sources_data = item.get("sources_data", [])
        # 提取所有 article_id (去除 media，只保留 article_id)
        article_ids = [article_id for media, article_id in sources_data]
        result[f"part{i}"] = article_ids
    return result

def save_attribution_to_db(story_id: str, attribution_json: Dict[str, List[str]]) -> bool:
    """
    將歸因結果儲存到 Supabase 資料庫
    更新 single_news 表的 attribution 欄位
    """
    try:
        print(f"正在儲存歸因結果到資料庫 (story_id: {story_id})...")
        
        # 將字典轉換為 JSON 字串
        attribution_json_str = json.dumps(attribution_json, ensure_ascii=False)
        
        # 更新資料庫
        response = supabase.table("single_news").update({
            "attribution": attribution_json_str
        }).eq("story_id", story_id).execute()
        
        if response.data:
            print(f"✓ 歸因結果已成功儲存到資料庫！")
            return True
        else:
            print(f"✗ 儲存失敗：沒有找到對應的 story_id")
            return False
            
    except Exception as e:
        print(f"✗ 儲存到資料庫時發生錯誤: {e}")
        return False
    
def check_generated(story_id: str) -> bool:
    """
    檢查 single_news 表中的 attribution 欄位是否有內容
    """
    try:
        single_news_data = supabase.table("single_news").select("attribution").eq("story_id", story_id).execute().data
        if not single_news_data or not single_news_data[0].get("attribution"):
            print("此 story_id 尚未生成歸因結果。")
            return False
        return True
    except Exception as e:
        print(f"錯誤：從 Supabase 讀取資料失敗: {e}")
        return False

if __name__ == "__main__":
    
    print("--- 開始測試 (方法二：Call Gemini API) ---")
    all_require = []
    batch_size = 1000
    start = 0

    while True:
        temp = supabase.table("single_news").select("story_id").order("generated_date", desc=True).range(start, start + batch_size - 1).execute()
        if not temp.data:
            break
        all_require.extend(temp.data)
        start += batch_size
    
    # 步驟 1: 執行歸因分析
    for item in all_require:
        # story_id_to_test = "bad3db95-1117-4b10-8675-80827b3a5102"
        # story_id_to_test = "4dc8514f-523f-46a5-b7e0-78cc320d7873"
        story_id_to_test = item['story_id']
        generate = check_generated(story_id_to_test)
        
        #如果已生成，跳過
        if generate:
            print(f"{story_id_to_test} 已生成。")
            continue
        
        annotated_result = attribute_sources_for_story(story_id_to_test)
    
        print("\n\n--- 最終標註結果 ---")
        if annotated_result:
            for i, item in enumerate(annotated_result, 1):
                print(f"Part {i}:")
                print(item['generated_text'])
                
                sources_data = item.get("sources_data", [])
                
                if sources_data:
                    # 建立一個包含 "媒體 (article_id)" 的字串列表
                    source_strings_list = [f"{media} ({article_id})" for media, article_id in sources_data]
                    
                    # 使用 "、" 來串接
                    source_names = "、".join(source_strings_list)
                    
                    print(f"[引用來源：{source_names}]")
                else:
                    print("[引用來源：無明確匹配]")
                print()
            
            # 步驟 2: 轉換為 JSON 格式
            attribution_json = format_attribution_to_json(annotated_result)
            print(attribution_json)
            print("\n--- 轉換為資料庫格式 ---")
            print(json.dumps(attribution_json, ensure_ascii=False, indent=2))
            
            # 步驟 3: 儲存到資料庫
            print("\n--- 儲存到資料庫 ---")
            save_attribution_to_db(story_id_to_test, attribution_json)
        else:
            print("此 story_id 未產生任何結果。")