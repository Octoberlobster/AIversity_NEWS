# 智能文本分析與詞彙解釋程式使用指南

## 🎯 程式功能

這個程式可以：

1. **自動從JSON檔案中提取文字內容**
2. **智能識別困難詞彙**
3. **自動生成詞彙解釋和應用範例**
4. **輸出結構化的結果**

## 📁 檔案說明

### 主要程式檔案
- `smart_text_processor.py` - 完整版程式（需要API金鑰）
- `demo_processor.py` - 演示版程式（不需要API，使用預設資料）
- `quick_process.py` - 快速處理腳本

### 輔助檔案
- `word_explainer.py` - 詞彙解釋模組
- `sample_tech_news.json` - 範例輸入檔案
- `demo_result.json` - 演示結果檔案

## 🚀 使用方式

### 方式1：演示版（推薦新手）
不需要API金鑰，使用預設的詞彙識別和解釋：

```bash
python demo_processor.py
```

### 方式2：完整版（需要API金鑰）
```bash
# 互動模式
python quick_process.py

# 命令列模式
python quick_process.py input.json output.json

# 直接使用主程式
python smart_text_processor.py
```

### 方式3：作為模組使用
```python
from smart_text_processor import SmartTextProcessor

processor = SmartTextProcessor()
result = processor.process_json_file("your_file.json", "output.json")
```

## 📋 輸入檔案格式

程式可以處理任何JSON格式的檔案，例如：

```json
{
  "title": "文章標題",
  "content": "文章內容...",
  "articles": [
    {
      "title": "子文章標題",
      "summary": "摘要內容..."
    }
  ],
  "metadata": {
    "keywords": ["關鍵字1", "關鍵字2"]
  }
}
```

## 📤 輸出格式

程式會產生包含以下內容的結果：

```json
{
  "source_file": "來源檔案名稱",
  "processing_date": "處理時間",
  "extracted_texts_count": "提取的文字段數",
  "difficult_words_count": "困難詞彙數量",
  "difficult_words": ["困難詞彙列表"],
  "explanations": {
    "terms": [
      {
        "term": "詞彙名稱",
        "definition": "（示例）詞彙定義",
        "examples": [
          {
            "title": "應用例子",
            "text": "範例1\n\n範例2\n\n範例3"
          }
        ]
      }
    ]
  }
}
```

## 🔧 設定說明

### 環境設定
如要使用完整版功能，需要設定API金鑰：

1. 創建 `.env` 檔案
2. 添加以下內容：
```
GEMINI_API_KEY=your_api_key_here
```

### 依賴套件
```bash
pip install -r requirements.txt
```

主要依賴：
- `google-generativeai` - Gemini API
- `python-dotenv` - 環境變數管理

## 💡 使用技巧

### 1. 測試功能
先使用演示版測試程式功能：
```bash
python demo_processor.py
```

### 2. 處理大檔案
對於大型JSON檔案，程式會自動截取前8000字符進行分析。

### 3. 自訂困難詞彙
可以修改 `demo_processor.py` 中的 `tech_terms` 列表來自訂要識別的詞彙。

### 4. 批量處理
可以編寫腳本批量處理多個檔案：

```python
from smart_text_processor import SmartTextProcessor
import os

processor = SmartTextProcessor()
for filename in os.listdir("input_folder"):
    if filename.endswith(".json"):
        processor.process_json_file(
            f"input_folder/{filename}", 
            f"output_folder/{filename.replace('.json', '_result.json')}"
        )
```

## 🔍 範例執行結果

使用提供的範例檔案 `sample_tech_news.json`：

- **提取文字段數**: 13段
- **識別困難詞彙**: 15個（人工智慧、機器學習、深度學習等）
- **生成解釋**: 6個詞彙的完整解釋
- **處理時間**: 約30秒（實際時間取決於API回應速度）

## ⚠️ 注意事項

1. **API配額**: 使用完整版時請注意API使用量
2. **網路連線**: 需要穩定的網路連線來訪問Gemini API
3. **檔案大小**: 建議單次處理的文字不超過10,000字符
4. **語言支援**: 主要針對繁體中文優化

## 🛠️ 疑難排解

### 常見問題

**Q: 執行時出現API錯誤**
A: 檢查API金鑰是否正確設定，以及是否有足夠的配額

**Q: 無法識別困難詞彙**
A: 嘗試使用演示版，或檢查輸入檔案是否包含中文文字

**Q: 程式執行緩慢**
A: 這是正常現象，因為需要多次調用API。可以減少要處理的詞彙數量

**Q: 輸出檔案為空**
A: 檢查輸入JSON檔案格式是否正確，以及是否包含文字內容

## 📞 技術支援

如有問題，請檢查：
1. Python版本（建議3.8+）
2. 依賴套件是否正確安裝
3. API金鑰設定
4. 網路連線狀況

---

**祝您使用愉快！** 🎉
