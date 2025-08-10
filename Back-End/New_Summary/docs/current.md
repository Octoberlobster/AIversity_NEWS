# 新聞處理與報導生成系統 - 當前狀態

## 系統概述

本專案提供「新聞故事→AI處理→綜合報導」的一鍵流水線，現在已能同時輸出綜合報導的三種長度：極短（約15秒）、短（約1–2分鐘）、長（約3–5分鐘）。

## 目的與結果

透過 Gemini 生成式模型：
- **處理原始新聞故事**（彙整多篇同題文章、抽取重點）
- **只輸出綜合報導**（不再預設輸出單篇文章摘要）
- 同步生成三種綜合報導長度：**極短 / 短 / 長**

## 主要執行方式

### 入口指令
在 `Back-End/New_Summary/scripts` 目錄下執行：
```bash
python quick_run.py
```

### 執行流程
1. 讀入 `data/cleaned_final_news.json`
2. 先做新聞處理（processed階段）
3. 再做報導生成（reports階段）
4. 產出：
   - `outputs/processed/*.json`：處理後的文章數據
   - `outputs/reports/*.json`：綜合報導結果
   - 對應的 `.txt` 摘要報告

## 目錄結構與重要檔案

```
Back-End/New_Summary/
├── core/
│   ├── news_processor.py      # 故事/文章處理與前置分析
│   ├── report_generator.py    # 綜合報導生成（含三種長度版本）
│   ├── report_config.py       # 報導生成設定（長度規範、生成參數、路徑）
│   └── config.py              # 處理階段設定（路徑、生成參數、API相關）
├── scripts/
│   ├── quick_run.py           # 一鍵執行整條流水線
│   └── run_complete_pipeline.py # 流水線主控（被quick_run呼叫）
├── data/
│   └── cleaned_final_news.json # 輸入資料
├── outputs/
│   ├── processed/             # 文章處理結果
│   ├── reports/               # 綜合報導輸出（JSON與簡報TXT）
│   └── logs/                  # 執行日誌
├── docs/
│   ├── README.md              # 簡易使用文件
│   ├── requirements.txt       # 最小依賴
│   └── current.md             # 本文件
└── .env                       # 環境變數（固定位置）
```

## 環境與金鑰設定

### 環境變數
- `.env` 檔案固定放在 `Back-End/New_Summary/.env`
- 主要環境變數：`GEMINI_API_KEY`
- 所有檔案皆以「相對於檔案自身位置」載入 `.env`，避免工作目錄不同造成失敗

### 依賴安裝
```bash
pip install -r Back-End/New_Summary/docs/requirements.txt
```

## 生成設定（重點配置）

### 檔案位置
`core/report_config.py`

### 長度規範設定
```python
COMPREHENSIVE_LENGTHS = {
    "ultra_short": {  # 約15秒可讀
        "min_chars": 80,
        "max_chars": 140
    },
    "short": {        # 約1~2分鐘
        "min_chars": 300,
        "max_chars": 600
    },
    "long": {         # 約3~5分鐘
        "min_chars": 900,
        "max_chars": 1500
    }
}
```

### 生成參數設定
```python
GENERATION_CONFIGS = {
    "comprehensive_ultra_short": {
        "temperature": 0.2,
        "max_output_tokens": 220,
        "top_p": 0.7,
        "top_k": 20
    },
    "comprehensive_short": {
        "temperature": 0.25,
        "max_output_tokens": 700,
        "top_p": 0.8,
        "top_k": 25
    },
    "comprehensive_long": {
        "temperature": 0.3,
        "max_output_tokens": 2000,
        "top_p": 0.85,
        "top_k": 25
    }
}
```

## 輸出JSON結構

### 檔案位置
`outputs/reports/final_comprehensive_reports_*.json`

### 關鍵結構
```json
{
  "story_info": {
    "story_index": 1,
    "story_title": "完整報導",
    "category": "...",
    "total_articles": 42
  },
  "comprehensive_report": {
    "title": "長版標題（相容用）",
    "content": "長版內文（相容用）",
    "versions": {
      "ultra_short": {
        "title": "極短標題",
        "content": "極短內文...",
        "article_count": 42,
        "generated_at": "2025-08-10T19:23:48"
      },
      "short": {
        "title": "短版標題",
        "content": "短版內文...",
        "article_count": 42,
        "generated_at": "2025-08-10T19:23:48"
      },
      "long": {
        "title": "長版標題",
        "content": "長版內文...",
        "article_count": 42,
        "generated_at": "2025-08-10T19:23:48"
      }
    },
    "article_count": 42,
    "generated_at": "2025-08-10T19:23:48"
  }
}
```

### 結構說明
- `title/content`：維持「長版」內容以相容既有使用端
- `versions`：包含三種版本的完整內容
  - `ultra_short`：極短版（約15秒）
  - `short`：短版（約1–2分鐘）
  - `long`：長版（約3–5分鐘）

## 系統特色

### 已解決的技術問題
1. **Markdown包裝問題**：修正Gemini回傳被markdown code block包裝造成的JSON解析失敗
2. **路徑相對化**：所有路徑改為相對於檔案位置，確保從任何目錄執行都正確
3. **環境變數載入**：統一`.env`載入機制，避免路徑問題
4. **輸出優化**：僅保留「綜合報導」，符合使用需求

### 當前功能
- ✅ 一鍵執行完整流水線
- ✅ 三種長度綜合報導同時生成
- ✅ 完整的日誌追蹤
- ✅ 結構化JSON輸出
- ✅ 人類可讀的TXT摘要報告

## 可調整配置

### 修改報導長度
編輯 `core/report_config.py` 中的 `COMPREHENSIVE_LENGTHS`：
- 調整 `min_chars` 和 `max_chars`
- 修改 `description` 說明

### 修改生成參數
編輯 `core/report_config.py` 中的 `GENERATION_CONFIGS`：
- `temperature`：創意程度（0.1-1.0）
- `max_output_tokens`：最大輸出長度
- `top_p` 和 `top_k`：多樣性控制

### 啟用個別文章摘要
如需同時輸出個別文章摘要，可在相關程式中設定：
```python
process_story_reports(generate_individual=True)
```
（目前預設關閉）

## 前端整合建議

### 顯示三種版本
直接讀取JSON中的 `comprehensive_report.versions`：
```javascript
const ultraShort = story.comprehensive_report.versions.ultra_short;
const short = story.comprehensive_report.versions.short;
const long = story.comprehensive_report.versions.long;
```

### 相容性考量
主要欄位 `comprehensive_report.title` 和 `comprehensive_report.content` 仍維持長版內容，確保既有程式碼不受影響。

## 日誌與除錯

### 日誌位置
`outputs/logs/` 目錄包含詳細執行日誌

### 常見問題
1. **API金鑰錯誤**：檢查 `.env` 檔案中的 `GEMINI_API_KEY`
2. **路徑問題**：確保在 `scripts/` 目錄下執行 `quick_run.py`
3. **依賴缺失**：執行 `pip install -r docs/requirements.txt`

## 系統狀態

- ✅ **核心功能完成**：三種長度綜合報導同時生成
- ✅ **測試驗證**：一鍵流水線正常執行並產出報告
- ✅ **相容性維護**：保持主欄位結構不變
- ✅ **文件更新**：README.md 和 requirements.txt 已同步更新

## 後續擴展建議

1. **版本選擇器**：可加入選項只輸出特定版本給外部系統
2. **批次處理**：支援指定story範圍處理
3. **格式擴展**：支援HTML、Markdown等其他輸出格式
4. **快取機制**：避免重複處理相同內容
5. **多語言支援**：擴展至其他語言的新聞處理

---

**最後更新**：2025-08-10  
**當前版本**：多版本綜合報導生成系統  
**狀態**：穩定運行，可投入使用
