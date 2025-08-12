from env import supabase
import json
import os

knowledge_base_dict = {
    "Politics": -1,
    "Taiwan News": -1,
    "Science & Technology": -1,
    "International News": -1,
    "Lifestyle & Consumer News": -1,
    "Sports": -1,
    "Entertainment": -1,
    "Business & Finance": -1,
    "Health & Wellness": -1,
}

category_map = {
    "政治": "Politics",
    "台灣": "Taiwan News",
    "國際": "International News",
    "科學與科技": "Science & Technology",
    "生活": "Lifestyle & Consumer News",
    "體育": "Sports",
    "娛樂": "Entertainment",
    "商業財經": "Business & Finance",
    "健康": "Health & Wellness",
}

def set_knowledge_base(json_input):
    with open(json_input, "r", encoding="utf-8") as f:
        data = json.load(f)
    contents = []
    for item in data:
        category = item["category"]
        for article in item["articles"]:
            contents.append(article["content"])
    #目前邏輯上有點問題，進來的category會都一樣
    category = category_map.get(category)
    if category in knowledge_base_dict:
        knowledge_base_dict[category] = f"你是一位{category}的新聞專家，你目前的知識庫是：{contents}，需要時參考這些資料來回答問題。"
    else:
        raise ValueError("Unknown category: {}".format(category))

def get_knowledge_base(category):
    if category in knowledge_base_dict:
        return knowledge_base_dict[category]
    else:
        raise ValueError("Unknown category: {}".format(category))
    
# set_knowledge_base("./demo/news-platform/chatroom/cleaned_final_new.json")
# print(get_knowledge_base("Science & Technology"))  