# 詞彙解釋模組 (Word Explanation Module)

這個模組用於自動產生困難詞彙的解釋和應用範例。

## 檔案說明

### 核心檔案
- `word_explainer.py` - 主要模組檔案，包含 WordExplainer 類別
- `__init__.py` - 模組初始化檔案
- `examples.py` - 使用範例
- `explain_words.py` - 原始腳本版本（向後相容）
- `difficult_words.json` - 輸入檔案範例
- `.env` - 環境變數檔案（包含 GEMINI_API_KEY）
- `requirements.txt` - Python 依賴套件清單

### 測試檔案
- `test_explain_words.py` - 測試程式（使用模擬資料）
- `word_explanations_test.json` - 測試輸出範例

## 安裝與使用

### 1. 安裝依賴
```bash
pip install -r requirements.txt
```

### 2. 設定 API 金鑰
在 `.env` 檔案中設定您的 Gemini API 金鑰：
```
GEMINI_API_KEY=your_api_key_here
```

## 使用方式

### 方式 1: 使用類別（推薦）

```python
from word_explainer import WordExplainer

# 初始化
explainer = WordExplainer()

# 解釋單個詞彙
result = explainer.explain_words("人工智慧")

# 解釋多個詞彙
result = explainer.explain_words(["機器學習", "深度學習"])

# 從檔案讀取並處理
result = explainer.explain_from_file("difficult_words.json", "output.json")
```

### 方式 2: 使用便利函數

```python
from word_explainer import explain_words, explain_from_file

# 快速解釋詞彙
result = explain_words("區塊鏈")

# 從檔案處理
result = explain_from_file("input.json", "output.json")
```

### 方式 3: 自定義 API 金鑰

```python
from word_explainer import WordExplainer

# 直接提供 API 金鑰
explainer = WordExplainer(api_key="your_api_key_here")
result = explainer.explain_words("量子計算")
```

### 方式 4: 腳本方式（原版）

```bash
python explain_words.py
```

## API 參考

### WordExplainer 類別

#### `__init__(self, api_key=None, model_name='gemini-1.5-pro-latest')`
初始化詞彙解釋器

#### `explain_words(self, words, delay=1.0, verbose=True)`
解釋詞彙列表
- `words`: 詞彙字串或列表
- `delay`: API 呼叫間延遲（秒）
- `verbose`: 是否顯示進度

#### `explain_from_file(self, input_file, output_file=None, verbose=True)`
從檔案讀取並解釋詞彙

#### `save_to_file(data, filename, verbose=True)` (靜態方法)
儲存結果到檔案

#### `create_sample_input(words, filename)` (靜態方法)
創建範例輸入檔案

## 輸出格式

程式會產生以下格式的 JSON：

```json
{
  "terms": [
    {
      "term": "詞彙名稱",
      "definition": "（示例）詞彙的定義說明",
      "examples": [
        {
          "title": "應用例子",
          "text": "範例句子1\n\n範例句子2\n\n範例句子3"
        }
      ]
    }
  ]
}
```

## 範例執行

查看 `examples.py` 檔案以獲得更多使用範例：

```bash
python examples.py
```

## 注意事項

- 確保有足夠的 Gemini API 配額
- 程式會在每次 API 呼叫間等待以避免超過速率限制
- 如果遇到 API 錯誤，程式會跳過該詞彙並繼續處理下一個
- 支援自定義 API 金鑰和模型名稱
- 提供詳細的錯誤處理和進度顯示
