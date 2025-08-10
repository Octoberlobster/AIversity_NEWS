# 新聞圖片生成器 (News Image Generator)

這是一個根據新聞內容自動生### 使用方法

### 基本使用
```bash
python main.py
```

程式會在當前目錄下創建 `output_images` 資料夾，並將所有生成的圖片和說明檔案存放在其中。

### 測試說明功能的工具。

## 🚀 功能特色

- ✅ **智能圖片生成**：根據新聞標題和摘要生成寫實風格的圖片
- ✅ **完整句子說明**：為每張圖片生成15字以內的完整中文說明
- ✅ **JSON元資料**：自動生成包含圖片路徑和說明的metadata檔案
- ✅ **分類管理**：按新聞類別自動整理圖片到不同資料夾
- ✅ **錯誤處理**：完善的重試機制和錯誤記錄

## 📋 系統需求

- Python 3.8+
- Google Gemini API Key
- 穩定的網路連線

## 🛠️ 安裝步驟

1. **安裝相依套件**
```bash
pip install -r requirements.txt
```

2. **設定API Key**
建立 `.env` 檔案並加入：
```
GEMINI_API_KEY=your_api_key_here
```

3. **準備新聞資料**
確保有 `cleaned_final_news1.json` 檔案，格式如下：
```json
[
  {
    "story_title": "新聞故事標題",
    "category": "政治",
    "articles": [
      {
        "article_title": "文章標題",
        "article_summary": "文章摘要",
        "id": "article_001"
      }
    ]
  }
]
```

## 🎯 使用方法

### 基本使用
```bash
python main.py
```

### 測試說明功能
```bash
python test_descriptions.py
```

### 自訂設定
編輯 `config.py` 檔案來調整：
- 輸入檔案路徑
- 輸出目錄
- 處理數量限制
- 說明文字長度等

## 📁 輸出結構

```
NewsImageGenerator_Official/
├── main.py
├── config.py
├── requirements.txt
├── README.md
├── cleaned_final_news1.json
├── generate_picture/
└── output_images/               # 生成的圖片輸出目錄
    ├── politics/                # 政治類新聞圖片
    │   ├── article_1.png
    │   └── article_2.png
    ├── technology/              # 科技類新聞圖片
    │   └── tech_news.png
    ├── image_metadata.json      # 圖片說明元資料
    └── errors.json             # 錯誤記錄 (如有)
```

## 📊 元資料格式

`image_metadata.json` 包含：
```json
{
  "total_images": 5,
  "generated_at": "2025-08-10 14:30:00",
  "images": [
    {
      "image_path": "output_images/politics/article_1.png",
      "description": "柯文哲譴責檢察官",
      "article_title": "完整文章標題",
      "category": "政治",
      "article_id": "article_001",
      "generated": true
    }
  ]
}
```

## ⚙️ 進階設定

### 說明文字規則
- 最大長度：15字（可在config.py調整）
- 自動識別人物、動作、事件
- 確保句子完整性，避免截斷
- 移除無關標記和網站名稱

### 圖片生成風格
- 寫實攝影風格
- 無文字內容
- 方形比例
- 高解析度PNG格式

## 🔧 故障排除

### 常見問題

1. **API Key錯誤**
   - 檢查 `.env` 檔案是否正確設定
   - 確認API Key有效性

2. **記憶體不足**
   - 減少 `MAX_ITEMS` 數量
   - 增加 `SLEEP_BETWEEN_CALLS` 間隔

3. **網路連線問題**
   - 增加 `RETRY_TIMES` 重試次數
   - 檢查網路穩定性

## 📝 開發資訊

- **版本**: 1.0.0
- **Python版本**: 3.8+
- **最後更新**: 2025年8月10日

## 📞 技術支援

如有問題，請檢查：
1. 所有依賴套件是否正確安裝
2. API Key是否設定正確
3. 輸入JSON檔案格式是否符合規範
4. 錯誤記錄檔案 `errors.json` 的內容
