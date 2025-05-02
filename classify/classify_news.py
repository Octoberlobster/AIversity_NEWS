from transformers import pipeline
import uuid
import json
import os

# Step 1: 初始化分類器
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Step 2: 目前已知事件列表
known_events = ["中華隊晉級"]
threshold = 0.5  # 信心門檻

# 讀取 JSON 檔案
with open("./cleaned_台灣新聞_2025_02_24_00.json", "r", encoding="utf-8") as file:
    data = json.load(file)

incoming_news = []
for item in data:
    content = item.get("content", "").strip()
    incoming_news.append(content)
# Step 3: 模擬新聞流進來
# incoming_news = [
#     "高雄男子張介宗因感情糾紛殺人",
#     "立法院發生大規模衝突，議員遭罷免聲浪四起",
#     "台北士林夜市爆發槍擊案，2死1傷",
#     "高雄小港區傳出重大工廠爆炸案"
# ]

# Step 4: 儲存已分類的新聞
classified_news = {}

# Step 5: 主邏輯
for news in incoming_news:
    print(f"\n📰 新聞：{news}")
    
    # 用 Zero-shot 分類
    result = classifier(news, candidate_labels=known_events)
    top_score = result['scores'][0]
    top_label = result['labels'][0]
    
    if top_score >= threshold:
        print(f"✅ 分類到既有事件：【{top_label}】 (信心={top_score:.2f})")
        classified_news[news] = top_label
    else:
        # 自動新增新事件
        new_event_name = news.split("，")[0]  # 取逗號前作新事件名，簡單命名
        if new_event_name not in known_events:
            known_events.append(new_event_name)
        print(f"⚡ 新事件誕生：【{new_event_name}】")
        classified_news[news] = new_event_name

# Step 6: 結果展示
print("\n📋 最後分類結果：")
for news, event in classified_news.items():
    print(f"- {event} ⬅ {news}")

print("\n🎯 目前已知事件列表：", known_events)
