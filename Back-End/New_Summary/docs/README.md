# 📰 New_Summary（精簡版）

只保留一鍵執行的 quick_run 流水線，從原始新聞資料生成「僅綜合報導」的最終輸出。

## 目錄結構

```
New_Summary/
├─ core/                 # 核心模組（請勿改動介面）
│  ├─ config.py          # 新聞處理設定（NewsProcessor）
│  ├─ report_config.py   # 報導生成設定（ReportGenerator）
│  ├─ news_processor.py  # 讀取 config 的處理器
│  └─ report_generator.py# 讀取 report_config 的生成器
├─ scripts/
│  ├─ quick_run.py       # 一鍵執行入口（推薦）
│  └─ run_complete_pipeline.py  # 供 quick_run 呼叫的流水線
├─ data/
│  └─ cleaned_final_news.json   # 輸入資料
└─ outputs/
   ├─ processed/         # 中間處理輸出
   ├─ reports/           # 最終綜合報導輸出
   └─ logs/              # 執行日誌
```

## 先決條件

- Python 3.10+（建議 3.11）
- 已安裝套件（見下方安裝步驟）
- 你已將 Gemini API Key 放在 New_Summary/.env：

```
GEMINI_API_KEY=你的API金鑰
```

## 安裝依賴

```
pip install -r docs/requirements.txt
```

（如無法使用 requirements.txt，可直接安裝最小依賴）

```
pip install google-generativeai python-dotenv
```

## 一鍵執行（推薦）

從專案根目錄或 New_Summary 內執行皆可：

```
cd Back-End/New_Summary/scripts
python quick_run.py
```

流程：
1) 讀取 `data/cleaned_final_news.json`
2) 產生中間檔 `outputs/processed/processed_articles_*.json`
3) 產生最終檔 `outputs/reports/final_comprehensive_reports_*.json`
4) 產生摘要報告 `*_summary.txt` 與 `*_pipeline_summary.txt`

## 調整參數（單一事實來源）

- 新聞處理相關：`core/config.py`
  - 模型：`GEMINI_MODEL`
  - 生成參數：`GENERATION_CONFIGS['analysis']`
  - 內容長度限制：`MAX_CONTENT_LENGTH`
  - 節流：`API_DELAY`
  - 路徑：`INPUT_FILE`、`OUTPUT_DIR`、`LOG_DIR`

- 報導生成相關：`core/report_config.py`
  - 模型：`GEMINI_MODEL`
  - 生成參數：`GENERATION_CONFIGS['comprehensive_report']`
  - 綜合報導長度規範：`COMPREHENSIVE_REPORT`
  - 路徑：`INPUT_DIR`、`OUTPUT_DIR`、`LOG_DIR`

所有核心類別已改為「讀取設定檔」，請勿在 `news_processor.py` / `report_generator.py` 內再硬編碼參數。

## 常見問題（Troubleshooting）

- 找不到 API Key：
  - 確認 `New_Summary/.env` 存在，且內容為 `GEMINI_API_KEY=...`
  - Windows 可能需重新開啟終端或直接執行 quick_run（程式會自行載入 .env）

- 報告沒有輸出到 outputs：
  - 目前已修正為固定輸出到 `outputs/processed` 與 `outputs/reports`
  - 若仍無檔案，檢查 `outputs/logs/*.log` 了解失敗原因

- 只想要「綜合報導」：
  - 已預設僅生成綜合報導，不會輸出個別文章摘要

## 授權與貢獻

此資料夾為精簡執行版本，若需擴充（UI、更多模式、品質檢核），建議以 `core/` 為中心進行模組化擴展。


