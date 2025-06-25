import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import re
from supabase import create_client, Client
import jieba
import jieba.posseg as pseg
from sklearn.feature_extraction.text import TfidfVectorizer
import os

supabase_url = os.getenv("API_KEY_URL")
supabase_key = os.getenv("API_KEY_supa")
supabase: Client = create_client(supabase_url, supabase_key)

# 下載必要的 NLTK 資源
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger_eng')

# def extract_keywords_nltk_tfidf():
#     # 從 Supabase 取得新聞內容
#     response = (
#         supabase.table("generated_news")
#         .select("generated_id, content")
#         .execute()
#     )
    
#     # 預處理函數
#     def preprocess_text(text):
#         # 移除特殊字符和數字
#         text = re.sub(r'[^a-zA-Z\s]', '', text.lower())
        
#         # 分詞
#         tokens = nltk.word_tokenize(text)
        
#         # 詞性標註，只保留名詞和形容詞
#         pos_tags = nltk.pos_tag(tokens)
#         filtered_words = [
#             word for word, pos in pos_tags 
#             if pos in ['NN', 'NNS', 'NNP', 'NNPS', 'JJ', 'JJR', 'JJS']
#             and len(word) > 2  # 過濾太短的詞
#         ]
        
#         return ' '.join(filtered_words)
    
#     # 預處理所有文本
#     processed_texts = []
#     news_data = []
    
#     for news in response.data:
#         processed_text = preprocess_text(news['content'])
#         if processed_text.strip():  # 確保處理後的文本不為空
#             processed_texts.append(processed_text)
#             news_data.append(news)
    
#     if not processed_texts:
#         print("沒有有效的文本可以處理")
#         return []
    
#     # 建立 TF-IDF 向量化器
#     vectorizer = TfidfVectorizer(
#         max_features=1000,           # 最多保留1000個特徵
#         min_df=1,                    # 詞語至少出現1次
#         max_df=0.8,                  # 詞語最多出現在80%的文檔中
#         ngram_range=(1, 2),          # 包含單詞和雙詞組合
#         stop_words='english'         # 移除英文停用詞
#     )
    
#     # 計算 TF-IDF 矩陣
#     tfidf_matrix = vectorizer.fit_transform(processed_texts)
#     feature_names = vectorizer.get_feature_names_out()
    
#     results = []
    
#     # 為每個文檔提取關鍵字
#     for i, news in enumerate(news_data):
#         # 取得該文檔的 TF-IDF 分數
#         tfidf_scores = tfidf_matrix[i].toarray()[0]
        
#         # 建立詞語-分數對應
#         word_scores = list(zip(feature_names, tfidf_scores))
        
#         # 按分數排序並取前15個
#         word_scores.sort(key=lambda x: x[1], reverse=True)
#         top_keywords = [(word, score) for word, score in word_scores[:15] if score > 0]
        
#         results.append({
#             'news_id': news['id'],
#             'content_preview': news['content'][:150] + "...",
#             'keywords': top_keywords
#         })
    
#     return results

# # 執行 NLTK + TF-IDF 關鍵字提取
# nltk_tfidf_results = extract_keywords_nltk_tfidf()

# print("\n=== NLTK + TF-IDF 關鍵字提取結果 ===")
# for item in nltk_tfidf_results:
#     print(f"\n新聞 ID: {item['news_id']}")
#     print(f"內容預覽: {item['content_preview']}")
#     print("NLTK + TF-IDF 關鍵字:")
#     for keyword, score in item['keywords']:
#         print(f"  {keyword}: {score:.4f}")

def extract_chinese_keywords_nltk_tfidf():
    # 從 Supabase 取得中文新聞內容
    response = supabase.table("generated_news").select("generated_id, content").execute()
    
    def preprocess_chinese_text(text):
        # 使用 jieba 進行中文分詞和詞性標註
        words = pseg.cut(text)
        
        # 只保留名詞、動詞、形容詞
        filtered_words = [
            word for word, flag in words 
            if flag.startswith(('n', 'v', 'a')) and len(word) > 1
        ]
        
        return ' '.join(filtered_words)
    
    # 預處理所有中文文本
    processed_texts = []
    news_data = []
    
    for news in response.data:
        processed_text = preprocess_chinese_text(news['content'])
        if processed_text.strip():
            processed_texts.append(processed_text)
            news_data.append(news)
    
    # 中文 TF-IDF 向量化
    vectorizer = TfidfVectorizer(
        max_features=500,
        min_df=1,
        max_df=0.7,
        token_pattern=r'(?u)\b\w+\b',  # 支援中文字符
        ngram_range=(1, 2)
    )
    
    tfidf_matrix = vectorizer.fit_transform(processed_texts)
    feature_names = vectorizer.get_feature_names_out()
    
    results = []
    for i, news in enumerate(news_data):
        tfidf_scores = tfidf_matrix[i].toarray()[0]
        word_scores = list(zip(feature_names, tfidf_scores))
        word_scores.sort(key=lambda x: x[1], reverse=True)
        top_keywords = [(word, score) for word, score in word_scores[:10] if score > 0]
        
        results.append({
            'news_id': news['generated_id'],
            'keywords': top_keywords
        })
    
    return results

# 執行中文關鍵字提取
chinese_results = extract_chinese_keywords_nltk_tfidf()

print("\n=== 中文 NLTK + TF-IDF 結果 ===")
for item in chinese_results:
    print(f"\n新聞 ID: {item['news_id']}")
    print("中文關鍵字:")
    for keyword, score in item['keywords']:
        print(f"  {keyword}: {score:.4f}")