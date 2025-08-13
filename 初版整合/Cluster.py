import google.generativeai as genai
from supabase import create_client, Client
import json
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from time import sleep
import os
from sklearn.cluster import DBSCAN
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder
import uuid

api_key = str(os.getenv("API_KEY_Ge"))
genai.configure(api_key=api_key)

SUPABASE_URL         = os.getenv("API_KEY_URL")
SUPABASE_SERVICE_KEY = os.getenv("API_KEY_supa")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

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
    .select("sourcecle_id,content", "sourcecle_media")
    # .neq("sourcecle_media","UDN")
    # .neq("sourcecle_media","TTV")
    #.gte("date","2026-05-05T22:19:59")
    .execute()
)
all_news = news_response.data
news_dict = {}
for i in range(len(all_news)):
    news_dict[all_news[i]["sourcecle_id"]] = all_news[i]["content"]

grouped_ids = set()
for ids in groups_id.values():
    grouped_ids.update(ids)

# id2event = {}
# for event_id, ids in groups_id.items():
#     for sid in ids:
#         id2event[sid] = event_id

labeled_data = [n for n in all_news if n["sourcecle_id"] in groups_id]
unlabeled_data = [n for n in all_news if n["sourcecle_id"] not in groups_id]
vectorizer = TfidfVectorizer()
cleaned_data = []
# train_data = []
# train_labels = []

# for news in labeled_data:
#     content = news["content"]
#     clean_text = " ".join(preprocess_text(content))
#     train_data.append(clean_text)
#     train_labels.append(id2event[news["sourcecle_id"]])
# tfidf_matrix = vectorizer.fit_transform(train_data)
        
    

for i in range(len(unlabeled_data)):
    content = unlabeled_data[i]["content"]
    words = preprocess_text(content)
    cleaned_data.append(" ".join(words))
    

tfidf_matrix = vectorizer.fit_transform(cleaned_data)
dbscan = DBSCAN(eps=0.8, min_samples=5, metric='cosine')
labels = dbscan.fit_predict(tfidf_matrix)
# for i in range(len(labels)):
#     with open("clustered_data.txt", "a", encoding="utf-8") as f:
#         f.write("@"+str(labels[i])+"@")
#         f.write("\n")
#         f.write(unlabeled_data[i]["content"])
#         f.write("\n")
#         f.write(unlabeled_data[i]["sourcecle_media"])
#         f.write("\n")
new_event_id = {}
for i in range(len(labels)):
    if labels[i] == -1:
        continue
    if labels[i] not in new_event_id:
        new_event_id[labels[i]] = []
    new_event_id[labels[i]].append(unlabeled_data[i]["sourcecle_id"])

for i in new_event_id :
    index = 0
    all_articles = []
    for j in new_event_id[i]:
        index += 1
        all_articles.append(str(index)+".\n")
        all_articles.append(news_dict[j])
        all_articles.append("\n")
    all_articles_str = "".join(all_articles)
    print(all_articles)
    response = model.generate_content("請根據下列多篇類似的新聞文本生成一個最適合他們的事件名稱，" \
                                      "請你以 JSON 格式回傳，格式如下：" \
                                      "{"
                                        "\"title\": \"事件名稱\","
                                      "}"
                                        "以下是新聞文本："+all_articles_str
                                    )
    response = response.text
    response = response.replace('```json', '').replace('```', '').strip()
    response = json.loads(response)
    m_uuid = uuid.uuid4()
    event_insert = (
        supabase.table("event")
        .insert({"event_id":str(m_uuid),"event_title": response["title"]})
        .execute()
    )
    for j in new_event_id[i]:
        event_map_insert = (
            supabase.table("event_original_map")
            .insert({"event_id":str(m_uuid),"sourcecle_id":j})
            .execute()
        )
        

    


