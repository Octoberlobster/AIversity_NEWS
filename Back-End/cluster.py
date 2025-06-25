from supabase import create_client, Client 
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
import os
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_distances
from hdbscan import HDBSCAN

# 從環境變數讀取 Supabase 連線資訊並建立客戶端
api_key_supabase = os.getenv("API_KEY_Supabase")
supabase_url = os.getenv("SUPABASE_URL")
supabase: Client = create_client(supabase_url, api_key_supabase)

with open("Stopwords-zhTW.txt", "r", encoding="utf-8") as f:
    stopwords = set([line.strip() for line in f])

def preprocess_text(text):
    """
    文本前處理函式：
    - 讀取停用詞表
    - 使用 jieba 對輸入文字進行分詞
    - 過濾停用詞與單字
    - 回傳分詞後的乾淨詞列表
    """
    words = jieba.lcut(text)
    # 過濾停用詞與長度小於等於 1 的詞
    clean_words = [w for w in words if w not in stopwords and len(w) > 1]
    return clean_words


# 從 Supabase 讀取事件映射資料 (event_id 對應 sourcecle_id)
event_map_response = (
    supabase.table("event_original_map")
    .select("event_id, sourcecle_id")
    .execute()
)
event_map_data = event_map_response.data  # 取得查詢結果資料

# 將查詢結果整理成字典：{ event_id: [sourcecle_id, ...], ... }
groups_id = {}
for row in event_map_data:
    event_id = row["event_id"]
    sourcecle_id = row["sourcecle_id"]
    if event_id not in groups_id:
        groups_id[event_id] = []
    groups_id[event_id].append(sourcecle_id)

# 從 Supabase 讀取指定日期後的新聞資料
news_response = (
    supabase.table("cleaned_news")
    .select("sourcecle_id, title, content")
    .execute()
)
all_news = news_response.data  # 取得所有新聞資料

# 建立已標記與未標記的資料列表
grouped_ids = set(sum(groups_id.values(), []))
# labeled_data 保留已在 groups_id 中的新聞
labeled_data = [n for n in all_news if n["sourcecle_id"] in grouped_ids]
# unlabeled_data 保留不在 groups_id 中的新聞
unlabeled_data = [n for n in all_news if n["sourcecle_id"] not in grouped_ids]

# 準備存放清理後的文本
cleaned_data = []

# 對每篇未標記新聞進行文本清理與向量化前置處理
for item in unlabeled_data:
    title = item["title"]
    content = item["content"]
    text = title + content  # 合併標題與內文
    words = preprocess_text(text)  # 前處理斷詞
    cleaned_data.append(" ".join(words))  # 加入清理後文字列表

# 建立 TF-IDF 向量器並對所有清理後文本做向量化
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(cleaned_data)

# 將稀疏矩陣轉成密集陣列，並做標準化處理
tfidf_matrix = StandardScaler().fit_transform(tfidf_matrix.toarray())

# 使用 DBSCAN 演算法以餘弦距離分群
dbscan = DBSCAN(eps=0.925, min_samples=3, metric="cosine")
labels = dbscan.fit_predict(tfidf_matrix)  # labels 中的 -1 表示離群點

# 將分群結果與對應新聞寫入檔案
with open("clustered_data.txt", "a", encoding="utf-8") as f:
    for idx, label in enumerate(labels):
        f.write(f"@{label}\n")  # 分群標籤
        f.write(unlabeled_data[idx]["title"] + "\n")  # 新聞標題
        f.write(unlabeled_data[idx]["content"] + "\n\n")  # 新聞內文
