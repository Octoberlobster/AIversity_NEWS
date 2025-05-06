import google.generativeai as genai
from supabase import create_client, Client
import json
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from time import sleep
import os
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

api_key = os.getenv("API_KEY_Gemini_PAY")
genai.configure(api_key=api_key)

api_key_supabase = os.getenv("API_KEY_Supabase")
supabase_url = os.getenv("SUPABASE_URL")
supabase: Client = create_client(supabase_url, api_key_supabase)

model = genai.GenerativeModel('gemini-1.5-pro-002',tools="google_search_retrieval")

def preprocess_text(text):
    with open("Stopwords-zhTW.txt", "r", encoding="utf-8") as f:
        stopwords = set([line.strip() for line in f])
    words = jieba.lcut(text)
    clean_words = [w for w in words if w not in stopwords and len(w) > 1]
    return clean_words

event_map_response = (
    supabase.table("event_original_map")
    .select("event_id, sourcecle_id")
    .execute()
)
event_map_data = event_map_response.data
groups_id = {}
for i in range(len(event_map_data)):
    event_id = event_map_data[i]["event_id"]
    sourcecle_id = event_map_data[i]["sourcecle_id"]
    if event_id not in groups_id:
        groups_id[event_id] = []
    groups_id[event_id].append(sourcecle_id)


news_response = (
    supabase.table("cleaned_news")
    .select("sourcecle_id,title, content")
    .gte("date","2025-05-05T22:19:59")
    .execute()
)
all_news = news_response.data

grouped_ids = set()
for ids in groups_id.values():
    grouped_ids.update(ids)

labeled_data = [n for n in all_news if n["sourcecle_id"] in groups_id]
unlabeled_data = [n for n in all_news if n["sourcecle_id"] not in groups_id]
cleaned_data = []
     
    

for i in range(len(unlabeled_data)):
    title = unlabeled_data[i]["title"]
    content = unlabeled_data[i]["content"]
    text = title + content
    words = preprocess_text(text)
    cleaned_data.append(" ".join(words))
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(cleaned_data)

tfidf_matrix = StandardScaler().fit_transform(tfidf_matrix.toarray())
dbscan = DBSCAN(eps=0.85, min_samples=2, metric="cosine")
labels = dbscan.fit_predict(tfidf_matrix)
for i in range(len(labels)):
    with open("clustered_data.txt", "a", encoding="utf-8") as f:
        f.write("@"+str(labels[i]))
        f.write("\n")
        f.write(unlabeled_data[i]["title"])
        f.write("\n")
        f.write(unlabeled_data[i]["content"])
        f.write("\n")
        f.write("\n")
        

    


