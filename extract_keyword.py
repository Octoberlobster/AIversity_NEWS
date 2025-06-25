from keybert import KeyBERT
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client
import os

# Supabase 設定
supabase_url = os.getenv("API_KEY_URL")
supabase_key = os.getenv("API_KEY_supa")
supabase: Client = create_client(supabase_url, supabase_key)

# def extract_keywords_with_keybert():
#     # 初始化 KeyBERT 模型
#     kw_model = KeyBERT()
    
#     # 從 Supabase 取得新聞內容
#     response = (
#         supabase.table("generated_news")
#         .select("generated_id, content")
#         .execute()
#     )
    
#     results = []
    
#     for news in response.data:
#         news_id = news['generated_id']
#         content = news['content']
        
#         # 使用 KeyBERT 提取關鍵字
#         # keyphrase_ngram_range: 設定 n-gram 範圍 (1,1)=單詞, (1,2)=單詞和雙詞組合
#         # stop_words: 停用詞設定，可以是 'english' 或自定義列表
#         # use_maxsum: 使用 Max Sum Similarity 來多樣化結果
#         # use_mmr: 使用 Maximal Marginal Relevance 來平衡相關性和多樣性
#         keywords = kw_model.extract_keywords(
#             content, 
#             keyphrase_ngram_range=(1, 1),  # 提取1-3個詞的片語
#             stop_words='english',          # 如果是英文新聞
#             use_maxsum=True,               # 增加關鍵字多樣性
#             nr_candidates=20,              # 候選關鍵字數量
#             top_n=10                       # 返回前10個關鍵字
#         )
        
#         results.append({
#             'news_id': news_id,
#             'content_preview': content[:150] + "...",
#             'keywords': keywords
#         })
    
#     return results

# # 執行 KeyBERT 關鍵字提取
# keybert_results = extract_keywords_with_keybert()

# print("=== KeyBERT 關鍵字提取結果 ===")
# for item in keybert_results:
#     print(f"\n新聞 ID: {item['news_id']}")
#     print(f"內容預覽: {item['content_preview']}")
#     print("KeyBERT 關鍵字:")
#     for keyword, score in item['keywords']:
#         print(f"  {keyword}: {score:.4f}")


def advanced_keybert_extraction():
    # 使用特定的 BERT 模型（支援中文）
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    kw_model = KeyBERT(model=model)
    
    # 從 Supabase 取得資料
    response = supabase.table("generated_news").select("content").execute()
    
    for i, news in enumerate(response.data):
        content = news['content']
        
        # 方法1: 使用 MMR (Maximal Marginal Relevance)
        keywords_mmr = kw_model.extract_keywords(
            content, 
            keyphrase_ngram_range=(1, 1), 
            stop_words=None,
            use_mmr=True, 
            diversity=0.5,  # 0-1之間，越高越多樣化
            top_n=10
        )
        
        # 方法2: 使用 Max Sum Similarity
        keywords_maxsum = kw_model.extract_keywords(
            content, 
            keyphrase_ngram_range=(1, 1), 
            stop_words=None,
            use_maxsum=True, 
            nr_candidates=20,
            top_n=10
        )
        
        print(f"\n=== 新聞 {i+1} ===")
        print("MMR 方法關鍵字:")
        for keyword, score in keywords_mmr:
            print(f"  {keyword}: {score:.4f}")
            
        print("Max Sum 方法關鍵字:")
        for keyword, score in keywords_maxsum:
            print(f"  {keyword}: {score:.4f}")

# 執行進階 KeyBERT
advanced_keybert_extraction()
