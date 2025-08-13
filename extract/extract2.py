import jieba
import jieba.posseg as pseg
from sklearn.feature_extraction.text import TfidfVectorizer
import re
from supabase import create_client, Client
import os

# 初始化 Supabase 連線
supabase_url = os.getenv("API_KEY_URL")
supabase_key = os.getenv("API_KEY_supa")
supabase: Client = create_client(supabase_url, supabase_key)

# 載入自訂停用詞（可擴充）
STOPWORDS = set([
    '的', '是', '在', '和', '與', '及', '對', '也', '了', '都', '將', '就', '而', '到',
    '目前', '其中', '表示', '指出', '不過', '可能', '因此', '例如', '其中', '相關',
    '政府', '問題', '情況', '需要', '進行', '具有', '包括', '成為', '或者'
])

# 可選：加入特定詞組到 jieba 詞庫，例如「萊克多巴胺」、「食藥署」
jieba.add_word("萊克多巴胺")
jieba.add_word("進口豬肉")
jieba.add_word("食藥署")
jieba.add_word("食品安全")
jieba.add_word("產地標示")

def preprocess_chinese_text(text):
    words = pseg.cut(text)
    filtered_words = []

    for word, flag in words:
        # 過濾：停用詞 + 詞長 + 詞性 + 數字
        if (
            word not in STOPWORDS and
            len(word) > 1 and
            not word.isdigit() and
            flag.startswith(('n', 'vn', 'ns', 'nt', 'nz', 'v', 'a'))  # 名詞、動詞、形容詞類
        ):
            filtered_words.append(word)
    
    return ' '.join(filtered_words)

def extract_chinese_keywords_nltk_tfidf():
    response = supabase.table("generated_news").select("generated_id, title, content, event_id").execute()

    processed_texts = []
    news_data = []

    for news in response.data:
        processed_text = preprocess_chinese_text(news['content'])
        if processed_text.strip():
            processed_texts.append(processed_text)
            news_data.append(news)

    vectorizer = TfidfVectorizer(
        max_features=500,
        min_df=1,
        max_df=0.8,
        ngram_range=(1, 2),
        token_pattern=r'(?u)\b\w+\b'
    )

    tfidf_matrix = vectorizer.fit_transform(processed_texts)
    feature_names = vectorizer.get_feature_names_out()

    results = []
    for i, news in enumerate(news_data):
        tfidf_scores = tfidf_matrix[i].toarray()[0]
        word_scores = list(zip(feature_names, tfidf_scores))
        word_scores.sort(key=lambda x: x[1], reverse=True)

        # 篩選前10個具有代表性的關鍵詞（分數大於0）
        top_keywords = [(word, score) for word, score in word_scores[:10] if score > 0]

        results.append({
            'news_id': news['generated_id'],
            'keywords': top_keywords
        })
        keywords_str = ' '.join([word for word, score in top_keywords])
        combined_str = news['title'] + ' ' + keywords_str
        print(f"新聞 ID: {news['generated_id']}, 關鍵字: {combined_str}")
        insert_keywords_to_event(news['event_id'], combined_str)
    return results

def insert_keywords_to_event(event_id, keywords_str):
    data = {
        "event_id": event_id,
        "keyword": keywords_str
    }
    result = supabase.table("event_keyword_map").insert(data).execute()
    return result

# 執行
chinese_results = extract_chinese_keywords_nltk_tfidf()

print("\n=== 中文 NLTK + TF-IDF 關鍵字提取結果 ===")
for item in chinese_results:

    print(f"\n新聞 ID: {item['news_id']}")
    print("中文關鍵字:")
    for keyword, score in item['keywords']:
        print(f"  {keyword}: {score:.4f}")
