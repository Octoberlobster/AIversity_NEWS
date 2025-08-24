# 📰 AIversity News Summary Pipeline

新聞處理與摘要生成的完整流水線，支援從 Supabase 資料庫讀取新聞資料，生成多版本摘要，並提取困難關鍵字解釋。

## 🎯 系統特色

- **智慧篩選**：只處理新增或變更的新聞資料，避免重複處理
- **多版本摘要**：自動生成極短版（30字）、短版（150字）、長版（300字）三種摘要
- **困難關鍵字提取**：自動識別並解釋專業術語、縮寫、技術名詞等
- **完整日誌系統**：各模組獨立日誌檔案，便於除錯和監控
- **資料庫整合**：支援 Supabase PostgreSQL 資料庫的完整 CRUD 操作

## 📁 目錄結構

```
New_Summary/
├─ core/                           # 核心模組
│  ├─ config.py                    # 新聞處理設定
│  ├─ report_config.py             # 報導生成設定
│  ├─ news_processor.py            # 新聞內容分析處理器
│  ├─ report_generator.py          # 綜合報導生成器
│  ├─ db_client.py                 # Supabase 資料庫客戶端
│  └─ difficult_keyword_extractor_final.py  # 困難關鍵字提取器
├─ scripts/
│  ├─ quick_run.py                 # 🚀 一鍵執行入口（推薦使用）
│  └─ run_complete_pipeline.py     # 完整流水線協調器
├─ outputs/
│  ├─ logs/                        # 執行日誌（按模組分類）
│  │  ├─ complete_pipeline.log     # 主流程日誌
│  │  ├─ db_client.log             # 資料庫操作日誌
│  │  ├─ news_processing.log       # 新聞處理日誌
│  │  ├─ report_generation.log     # 報導生成日誌
│  │  └─ keyword_extraction.log    # 關鍵字提取日誌
│  ├─ processed/                   # 中間處理結果
│  └─ reports/                     # 最終報導輸出
└─ docs/
   ├─ README.md                    # 本說明文件
   └─ requirements.txt             # Python 套件需求
```

## ⚙️ 系統需求

- **Python**: 3.10+ （建議 3.11 或 3.12）
- **資料庫**: Supabase PostgreSQL
- **API**: Google Gemini API

## 🛠️ 安裝與設定

### 1. 安裝依賴套件

```bash
pip install -r docs/requirements.txt
```

### 2. 環境變數設定

在專案根目錄建立 `.env` 檔案：

```env
# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# Supabase Database
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here
```

### 3. 資料庫表格結構

系統需要以下 Supabase 表格：

- `stories`: 新聞主題資訊
- `cleaned_news`: 清理後的新聞文章內容
- `single_news`: 生成的摘要資料（系統自動建立/更新）
- `term`: 困難關鍵字定義表
- `term_map`: 新聞與關鍵字的關聯表

## 🚀 使用方法

### 方法一：一鍵執行（推薦）

```bash
cd scripts
python quick_run.py
```

### 方法二：直接執行完整流水線

```bash
cd scripts  
python run_complete_pipeline.py
```

## 🔄 處理流程

系統採用四階段智慧處理流程：

### 階段一：新聞資料處理
- 從 Supabase `stories` 和 `cleaned_news` 表讀取資料
- 使用智慧篩選，只處理新增或文章數變更的 stories
- 透過 Gemini AI 分析每篇文章，提取關鍵資訊：
  - 核心摘要
  - 關鍵詞列表
  - 重要人物與機構
  - 地點資訊和時間線
  - 事件分類和信心度評分

### 階段二：報導生成
- 基於處理後的文章資料生成綜合報導
- 同步輸出三種長度版本：
  - **極短版**：約 30 字，適合推播通知
  - **短版**：約 150 字，適合摘要預覽
  - **長版**：約 300 字，適合詳細閱讀
- 整合多篇文章的關鍵資訊，去除重複內容

### 階段三：資料庫儲存
- 將生成的摘要儲存到 `single_news` 表
- 記錄處理時間和版本資訊
- 追蹤更新的 story_ids 供後續處理使用

### 階段四：困難關鍵字提取
- 分析摘要內容，識別困難關鍵字：
  - 專業術語（醫學、法律、科技等）
  - 外來語和縮寫
  - 特定領域概念
- 為每個關鍵字生成淺顯易懂的解釋和應用實例
- 儲存到 `term` 和 `term_map` 表供前端使用

## 📊 智慧篩選機制

系統具備智慧篩選功能，避免不必要的重複處理：

- **新 Stories**: 自動識別並處理
- **文章數變更**: 檢測到文章增減時重新處理
- **已處理且無變化**: 跳過處理，節省 API 資源
- **批次追蹤**: 記錄本次執行的更新項目

## ⚡ 效能優化

- **API 節流**: 自動控制 API 呼叫頻率，避免超出限制
- **批次處理**: 支援分批儲存，降低記憶體使用
- **錯誤重試**: 自動重試機制，提升系統穩定性
- **日誌分級**: 詳細的執行日誌，便於問題追蹤

## 🎛️ 參數調整

### 新聞處理參數（`core/config.py`）
- `GEMINI_MODEL`: AI 模型選擇
- `GENERATION_CONFIGS`: 各種生成模式的參數
- `API_DELAY`: API 呼叫間隔時間
- `MAX_CONTENT_LENGTH`: 文章內容最大處理長度
- `BATCH_SIZE`: 批次處理大小

### 報導生成參數（`core/report_config.py`）
- `COMPREHENSIVE_LENGTHS`: 三種摘要版本的字數限制
- `COMPREHENSIVE_REPORT`: 報導生成的篩選條件
- `QUALITY_CONTROL`: 品質控制設定

## 🔍 監控與除錯

### 日誌檔案說明
- `complete_pipeline.log`: 主流程執行記錄
- `db_client.log`: 資料庫操作記錄
- `news_processing.log`: 新聞分析處理記錄
- `report_generation.log`: 報導生成記錄
- `keyword_extraction.log`: 關鍵字提取記錄

### 常見問題排除

**API Key 問題**:
```bash
# 檢查環境變數
echo $GEMINI_API_KEY

# 確認 .env 檔案存在且格式正確
cat .env
```

**資料庫連線問題**:
```bash
# 測試 Supabase 連線
python -c "from core.db_client import SupabaseClient; SupabaseClient().test_connection()"
```

**記憶體或效能問題**:
- 調整 `BATCH_SIZE` 降低記憶體使用
- 增加 `API_DELAY` 避免速率限制
- 檢查日誌檔案確認處理進度

## 🔧 進階用法

### 僅處理特定 Stories
```python
from core.news_processor import NewsProcessor
from core.config import NewsProcessorConfig

processor = NewsProcessor()
# 處理前 5 個 stories
result = processor.process_all_stories(max_stories=5)
```

### 單獨執行關鍵字提取
```python
from core.difficult_keyword_extractor_final import DiffKeywordProcessor

processor = DiffKeywordProcessor()
# 為特定 story_ids 生成關鍵字
processor.run(story_ids=['story-id-1', 'story-id-2'])
```

### 自訂生成參數
```python
from core.report_generator import ReportGenerator

generator = ReportGenerator(
    model_name="gemini-2.5-pro",  # 使用更強的模型
    api_key="your_api_key"
)
```

## 🤝 貢獻指南

1. 所有核心邏輯位於 `core/` 目錄
2. 配置參數統一管理於 `*_config.py` 檔案
3. 新增功能請考慮向下相容性
4. 提交前請確保所有測試通過
5. 更新 README 說明新增的功能

## 📄 授權

此專案為內部使用，請遵循相關政策。


