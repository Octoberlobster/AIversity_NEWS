import google.generativeai as genai
from supabase import create_client, Client
import jieba
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import LabelEncoder
import numpy as np

# 初始化
api_key = os.getenv("API_KEY_Gemini_PAY")
genai.configure(api_key=api_key)
api_key_supabase = os.getenv("API_KEY_Supabase")
supabase_url = os.getenv("SUPABASE_URL")
supabase: Client = create_client(supabase_url, api_key_supabase)
model = genai.GenerativeModel('gemini-1.5-pro-002', tools="google_search_retrieval")

# 停用詞與斷詞
def preprocess_text(text):
    with open("Stopwords-zhTW.txt", "r", encoding="utf-8") as f:
        stopwords = set([line.strip() for line in f])
    words = jieba.lcut(text)
    clean_words = [w for w in words if w not in stopwords and len(w) > 1]
    return clean_words

# 抓 event mapping
event_map_response = supabase.table("event_original_map").select("event_id, sourcecle_id").execute()
groups_id = {}
for row in event_map_response.data:
    groups_id.setdefault(row["event_id"], []).append(row["sourcecle_id"])

grouped_ids = set()
for ids in groups_id.values():
    grouped_ids.update(ids)

id2event = {sid: eid for eid, sids in groups_id.items() for sid in sids}

# 抓新聞
news_response = supabase.table("cleaned_news").select("sourcecle_id,content,sourcecle_media").execute()
all_news = news_response.data
labeled_data = [n for n in all_news if n["sourcecle_id"] in grouped_ids]
unlabeled_data = [n for n in all_news if n["sourcecle_id"] not in grouped_ids]

# 訓練資料
train_data, train_labels = [], []
for news in labeled_data:
    content = " ".join(preprocess_text(news["content"]))
    train_data.append(content)
    train_labels.append(id2event[news["sourcecle_id"]])

# TF-IDF + SVM 訓練
vectorizer = TfidfVectorizer(max_features=5000)
X_train = vectorizer.fit_transform(train_data)
le = LabelEncoder()
y_train = le.fit_transform(train_labels)
logreg = LogisticRegression(max_iter=1000)
logreg.fit(X_train, y_train)

# 處理未標記新聞：分類預測
X_unlabeled_raw = []
cleaned_unlabeled = []
for news in unlabeled_data:
    text = " ".join(preprocess_text(news["content"]))
    X_unlabeled_raw.append(news)
    cleaned_unlabeled.append(text)
X_unlabeled_vec = vectorizer.transform(cleaned_unlabeled)
probs = logreg.predict_proba(X_unlabeled_vec)
preds = logreg.predict(X_unlabeled_vec)

# 門檻設定（高可信度者納入現有群）
threshold = 0.6
accepted = []
rejected = []

for i, prob in enumerate(probs):
    max_prob = max(prob)
    if max_prob >= threshold:
        accepted.append({
            "news": X_unlabeled_raw[i],
            "event_id": le.inverse_transform([preds[i]])[0],
            "confidence": max_prob
        })
    else:
        rejected.append(X_unlabeled_raw[i])

# DBSCAN 對 rejected 重新分群
rejected_texts = [" ".join(preprocess_text(n["content"])) for n in rejected]
X_dbscan = vectorizer.transform(rejected_texts)
dbscan = DBSCAN(eps=0.8, min_samples=3, metric="cosine")
cluster_labels = dbscan.fit_predict(X_dbscan)

# 輸出結果
with open("clustered_data.txt", "w", encoding="utf-8") as f:
    f.write("=== SVM 預測結果（可信） ===\n")
    for r in accepted:
        f.write(f"[SVM-{r['event_id']} | {r['confidence']:.2f}]\n")
        f.write(r["news"]["content"] + "\n")
        f.write(r["news"]["sourcecle_media"] + "\n\n")

    f.write("\n=== DBSCAN 結果（新群） ===\n")
    for i, label in enumerate(cluster_labels):
        f.write(f"@Cluster-{label}@\n")
        f.write(rejected[i]["content"] + "\n")
        f.write(rejected[i]["sourcecle_media"] + "\n\n")
