import google.generativeai as genai
import numpy as np
import re
from typing import List, Dict, Any
from env import supabase, api_key

#相似度門檻
SYSTEM_GOLDEN_THRESHOLD = 0.75
# 使用的 Embedding 模型
EMBEDDING_MODEL = "models/text-embedding-004"
genai.configure(api_key=api_key)


def chunk_text_by_paragraph(text: str) -> list[str]:
    if not text:
        return []
    chunks = re.split(r'\n\s*\n', text)
    return [chunk.strip() for chunk in chunks if chunk.strip()]

def get_embeddings_batch(texts: List[str], task_type: str) -> List[List[float]]:
    if not texts:
        return []
    try:
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=texts,
            task_type=task_type
        )
        return result['embedding']
    except Exception as e:
        print(f"批次取得 Embedding 失敗 (Task: {task_type}): {e}")
        return [[]] * len(texts)

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """
    計算兩個 embedding 向量的餘弦相似度。
    """
    v1_np = np.array(v1)
    v2_np = np.array(v2)
    norm_v1 = np.linalg.norm(v1_np)
    norm_v2 = np.linalg.norm(v2_np)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return np.dot(v1_np, v2_np) / (norm_v1 * norm_v2)

def attribute_sources_for_story(story_id: str) -> List[Dict[str, Any]]:
    """
    接收一個 story_id，自動從 Supabase 抓取資料，
    執行切割、向量化、比對，並回傳標註好的結果。
    (已更新為追蹤 article_id)
    """
    
    print(f"--- 開始自動歸因任務：{story_id} ---")
    
    # --- 步驟 1: 抓取資料與切割 ---
    try:
        # 抓取整合新聞
        single_news_data = supabase.table("single_news").select("long").eq("story_id", story_id).execute().data
        if not single_news_data or not single_news_data[0].get("long"):
            print("錯誤：在 Supabase 中找不到此 story_id 的 'single_news' 或 'long' 內容。")
            return []
        single_news_text = single_news_data[0].get("long")
        
        # 【修改 1】抓取來源新聞 (包含 article_id)
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
    source_texts_to_embed = []
    for item in cleaned_news_data:
        media = item.get("media")
        content = item.get("content")
        article_id = item.get("article_id") # 取得 article_id
        
        # 【修改 2】確保 article_id 也存在
        if not (content and media and article_id):
            print(f"警告：跳過一筆資料，缺少 media, content 或 article_id。")
            continue
            
        chunks = chunk_text_by_paragraph(content)
        for i, chunk_text in enumerate(chunks):
            source_chunks_db.append({
                "media": media,
                "article_id": article_id, # 【修改 2】儲存 article_id
                "chunk_id": f"{article_id}_p{i+1}", # chunk_id 也使用 article_id
                "text": chunk_text
            })
            source_texts_to_embed.append(chunk_text)

    # 處理整合新聞
    single_news_chunks_db = []
    generated_texts_to_embed = []
    single_news_chunks = chunk_text_by_paragraph(single_news_text)
    for i, chunk_text in enumerate(single_news_chunks):
        single_news_chunks_db.append({
            "chunk_id": f"{story_id}_part_{i+1}",
            "text": chunk_text
        })
        generated_texts_to_embed.append(chunk_text)

    if not source_texts_to_embed or not generated_texts_to_embed:
        print("錯誤：來源新聞或整合新聞切割後為空，任務中止。")
        return []
        
    print(f"步驟 1 完成：{len(source_chunks_db)} 個來源區塊，{len(single_news_chunks_db)} 個整合區塊。")

    # --- 步驟 2: 向量化 (此步驟不變) ---
    print("步驟 2 開始：正在向量化...")
    source_embeddings = get_embeddings_batch(source_texts_to_embed, "RETRIEVAL_DOCUMENT")
    generated_embeddings = get_embeddings_batch(generated_texts_to_embed, "RETRIEVAL_QUERY")
    
    for i, chunk in enumerate(source_chunks_db):
        chunk['embedding'] = source_embeddings[i]
    for i, chunk in enumerate(single_news_chunks_db):
        chunk['embedding'] = generated_embeddings[i]
        
    source_chunks_db = [c for c in source_chunks_db if c.get('embedding')]
    
    if not source_chunks_db:
        print("錯誤：所有來源區塊向量化失敗，任務中止。")
        return []
        
    print("步驟 2 完成：向量化成功。")

    # --- 步驟 3 & 4: 比對 & 套用門檻 ---
    print(f"步驟 3/4 開始：使用門檻 {SYSTEM_GOLDEN_THRESHOLD} 進行比對...")
    final_annotated_article = []

    for gen_chunk in single_news_chunks_db:
        gen_embedding = gen_chunk.get('embedding')
        
        if not gen_embedding:
            final_annotated_article.append({
                "generated_text": gen_chunk['text'],
                "sources_data": [] # 回傳空列表
            })
            continue

        # 【修改 3】使用一個列表來儲存 (media, article_id) 元組
        matched_sources_tuples = []
        
        for source_chunk in source_chunks_db:
            similarity = cosine_similarity(gen_embedding, source_chunk['embedding'])
            
            if similarity >= SYSTEM_GOLDEN_THRESHOLD:
                # 儲存 (媒體名稱, 文章ID)
                matched_sources_tuples.append(
                    (source_chunk['media'], source_chunk['article_id'])
                )
        
        # 使用 set() 來對元組 (tuple) 列表進行去重
        # ('TVBS', 'id-A') 和 ('TVBS', 'id-B') 會被保留
        # ('TVBS', 'id-A') 和 ('TVBS', 'id-A') 會被合併
        unique_sources = list(set(matched_sources_tuples))

        # 整理結果
        final_annotated_article.append({
            "generated_text": gen_chunk['text'],
            "sources_data": unique_sources # 回傳 (media, article_id) 的列表
        })
        
    print("--- 自動歸因任務完成 ---")
    return final_annotated_article

if __name__ == "__main__":
    
    print("--- 開始測試 ---")
    story_id_to_test = "4dc8514f-523f-46a5-b7e0-78cc320d7873"
    annotated_result = attribute_sources_for_story(story_id_to_test)
    
    # 【修改】更新 print 邏輯，同時顯示 media 和 article_id
    print("\n\n--- 最終標註結果 ---")
    if annotated_result:
        for item in annotated_result:
            print(item['generated_text'])
            
            # item['sources_data'] 是 [('TVBS', 'id_A'), ('CTWANT', 'id_B')]
            sources_data = item.get("sources_data", [])
            
            if sources_data:
                # --- 這是修改後的核心邏輯 ---
                # 建立一個包含 "媒體 (article_id)" 的字串列表
                source_strings_list = [f"{media} ({article_id})" for media, article_id in sources_data]
                
                # 使用 "、" 來串接
                source_names = "、".join(source_strings_list)
                # --- 修改結束 ---
                
                print(f"[引用來源：{source_names}]")
            else:
                print("[引用來源：無明確匹配]")
            print()
    else:
        print("此 story_id 未產生任何結果。")