# Gemini 新聞分類器

基於 Google Gemini 2.0 Flash Exp 的智慧新聞分類系統，採用兩階段分類策略。

## 功能概述

這個新的分類器實現了您提出的兩步驟分類方法：

### 步驟1：Topic 分類到 Category
- 將 topic 的標題和內容丟給 Gemini 模型
- 讓 AI 判斷該 topic 最適合歸屬於哪個新聞類別
- 支援的類別：Politics、Taiwan News、International News、Science & Technology、Lifestyle & Consumer、Sports、Entertainment、Business & Finance、Health & Wellness

### 步驟2：新聞分類到 Topic
- 從資料庫中抓取指定 category 的所有 single_news
- 將新聞的標題 (news_title) 和簡介 (short) 提供給 Gemini
- 讓 AI 判斷哪些新聞與該 topic 相關，並評估相關程度

## 檔案結構

```
├── gemini_news_classifier.py      # 主要分類器實作
├── test_gemini_classifier.py      # 測試和使用範例
├── requirements.txt               # 更新後的依賴套件
└── README_gemini_classifier.md    # 說明文件（本檔案）
```

## 安裝依賴

```bash
pip install -r requirements.txt
```

新增的套件：
- `google-generativeai==0.8.3` - Google Gemini API 客戶端

## 環境設定

確保您的 `.env` 檔案包含以下變數：

```env
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key  
GEMINI_API_KEY=your-gemini-api-key
```

## 使用方法

### 1. 基本使用

```python
import asyncio
from gemini_news_classifier import GeminiNewsClassifier

async def main():
    classifier = GeminiNewsClassifier()
    
    # 對單個 topic 進行完整分類
    result = await classifier.full_classification_pipeline("topic-id")
    print(result)

asyncio.run(main())
```

### 2. 分步驟使用

```python
# 步驟1：判斷 topic 屬於哪個 category
category = await classifier.step1_classify_topic_to_category(
    topic_title="人工智慧發展趨勢",
    topic_content="探討AI技術的最新發展..."
)

# 步驟2：在該 category 中找相關新聞
topic_info = {
    "topic_id": "uuid",
    "topic_title": "人工智慧發展趨勢",
    "topic_content": "..."
}
related_news = await classifier.step2_classify_news_to_topic(category, topic_info)
```

### 3. 批量處理

```python
# 對所有 topics 進行分類
results = await classifier.classify_all_topics()
```

## 測試程式

執行測試程式來了解分類器的功能：

```bash
python test_gemini_classifier.py
```

測試程式包含：
1. 獲取資料庫中的 topics
2. 測試 topic 到 category 的分類
3. 完整分類流程測試
4. 批量分類測試

## 主要類別和方法

### GeminiNewsClassifier

#### 主要方法

- `step1_classify_topic_to_category(topic_title, topic_content)` - 步驟1分類
- `step2_classify_news_to_topic(category, topic_info)` - 步驟2分類  
- `full_classification_pipeline(topic_id)` - 完整分類流程
- `classify_all_topics()` - 批量分類所有topics

#### 輔助方法

- `_get_news_by_category(category)` - 獲取指定類別的新聞
- `_classify_news_batch(news_batch, topic_info)` - 批次分類新聞
- `_call_gemini_async(prompt)` - 非同步呼叫 Gemini API

## 輸出格式

### 完整分類流程輸出

```json
{
    "success": true,
    "topic_info": {
        "topic_id": "uuid",
        "topic_title": "topic標題",
        "topic_short": "topic簡介"
    },
    "assigned_category": "科技",
    "classified_news_count": 15,
    "classified_news": [
        {
            "story_id": "uuid",
            "news_title": "新聞標題",
            "short": "新聞簡介",
            "category": "科技",
            "relevance": "high",
            "reason": "相關原因",
            "topic_id": "uuid"
        }
    ]
}
```

## 優勢

相比原始的 `news_classifier.py`：

1. **更智慧的分類**：使用 Gemini 的語言理解能力，而非單純的向量相似度
2. **兩階段精確分類**：先確定大分類，再進行細分，提高準確度
3. **自然語言解釋**：AI 會提供分類理由，便於理解和驗證
4. **更好的擴展性**：容易調整 prompt 來改善分類邏輯
5. **彈性處理**：可以處理各種複雜的新聞內容和 topic 描述

## 注意事項

1. **API 費用**：Gemini API 按使用量收費，大量調用需考慮成本
2. **速度考量**：網路 API 呼叫比本地計算慢，適合離線批次處理
3. **錯誤處理**：已包含完整的錯誤處理機制
4. **頻率限制**：批量處理時自動添加延遲避免 API 限制

## 未來改進

1. 可以增加更多新聞類別
2. 實作分類結果的自動儲存到資料庫
3. 添加分類信心度評分
4. 支援多語言新聞分類
5. 實作分類結果的人工驗證機制
