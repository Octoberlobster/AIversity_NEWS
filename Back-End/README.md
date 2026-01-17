# 新聞處理自動化系統

## 系統概述

本系統是一個完整的新聞爬取、分析、分類和發佈的自動化管道。所有腳本通過 `Schedule.py` 進行協調執行，支持並行處理以提高效率。

---

## 🔄 執行流程

### 1️⃣ **資料爬取階段**
獲取新聞源數據

| 腳本 | 功能 |
|-----|------|
| `Crawler/craw.py` | 爬取 Google News 新聞資源 |

---

### 2️⃣ **新聞生成階段**
處理和清理新聞數據

| 腳本 | 功能 |
|-----|------|
| `New_Summary/scripts/quick_run.py` | 新聞摘要生成 |
| `Supabase_error_fix/news_notitle.py` | 刪除標題缺失的新聞 |

---

### 3️⃣ **分析生成階段**
生成圖片和多維度分析

#### 3.1 類別圖片生成
| 腳本 | 功能 |
|-----|------|
| `Category_images/generate_categories_from_single_news.py` | 從單一新聞生成類別 |
| `Category_images/generate_picture_to_supabase/generate_from_supabase.py` | 生成圖片並上傳到 Supabase |

#### 3.2 內容分析
| 腳本 | 功能 |
|-----|------|
| `Analyze/Position_flag.py` | 識別新聞是否具立場 |
| `Analyze/Who_talk.py` | 選出適合的專家進行後續討論 |
| `Analyze/Suicide_flag.py` | 檢測自殺相關內容標籤 |
| `Analyze/Pros_and_cons.py` | 生成贊成/反對的觀點分析 |
| `Analyze/Pro_Analyze.py` | 專業級專家分析處理 |

#### 3.3 來源歸因分析
| 腳本 | 功能 |
|-----|------|
| `Attribution/Attribution_gemini.py` | 使用 Gemini 進行來源歸因 |

#### 3.4 數據修復
| 腳本 | 功能 |
|-----|------|
| `Supabase_error_fix/who_talk_false.py` | 修復專家識別錯誤 |

---

### 4️⃣ **相關內容關聯階段**
識別和連結相關新聞

| 腳本 | 功能 |
|-----|------|
| `Relative/Relative_News.py` | 找出相關新聞 |
| `Supabase_error_fix/relative_false.py` | 修復相關性匹配錯誤 |
| `Relative/Relative_Topics.py` | 找出相關專題 |

---

### 5️⃣ **翻譯階段**
多語言翻譯處理

| 腳本 | 功能 |
|-----|------|
| `Translate/Translate.py` | 新聞內容翻譯 |

---

### 6️⃣ **排名和熱點階段**
識別熱點和排名新聞

| 腳本 | 功能 |
|-----|------|
| `Toptennews/Toptennews.py` | 生成每日十大新聞排名 |

---

### 7️⃣ **專題處理階段**

#### 每日執行任務
| 腳本 | 功能 |
|-----|------|
| `Topic/topic_get_title.py` | 獲取新專題標題 |
| `Topic/Classfication.py` | 專題分類 |
| `Topic/complete_news_grouper.py` | 完整新聞分組 |
| `Topic/topic_group_update.py` | 更新專題組 |
| `Topic/topic_summary.py` | 生成專題摘要 |
| `Topic/Pro_Analyze_Topic.py` | 專題級分析 |
| `Topic/topic_5w1h_2.py` | 提取 5W1H 要素 |
| `Topic/topic_report.py` | 生成專題報告 |
| `Topic/translate_topic.py` | 專題翻譯 |

#### 每週執行任務
| 腳本 | 功能 |
|-----|------|
| `Topic/complete_news_grouper.py` | 完整新聞分組（週期性） |
| `Topic/topic_summary.py` | 生成專題摘要（週期性） |
| `Topic/Pro_Analyze_Topic.py` | 專題級分析（週期性） |
| `Topic/topic_5w1h_2.py` | 提取 5W1H 要素（週期性） |
| `Topic/topic_report.py` | 生成專題報告（週期性） |
| `Topic/translate_topic.py` | 專題翻譯（週期性） |

---

## 📋 核心模塊說明

### 📁 Analyzer（分析模塊）
- **目的**：對新聞內容進行多維度分析
- **包含**：立場識別、專家選取、自殺內容檢測、觀點分析等

### 📁 Attribution（歸因模塊）
- **目的**：確定新聞的信息來源和歸因
- **技術**：使用 Gemini AI 進行智能歸因

### 📁 Category_images（圖片和分類模塊）
- **目的**：生成新聞類別和相應的視覺內容
- **功能**：自動生成分類圖片並上傳到 Supabase

### 📁 Crawler（爬蟲模塊）
- **目的**：從各種來源爬取新聞
- **源頭**：Google News

### 📁 New_Summary（新聞摘要模塊）
- **目的**：生成新聞摘要和關鍵信息
- **包含**：快速處理、錯誤修復等

### 📁 Relative（相關性模塊）
- **目的**：識別新聞之間的相關性
- **功能**：新聞關聯、專題關聯、錯誤修復

### 📁 Topic（專題模塊）
- **目的**：進行專題級別的新聞分組和分析
- **功能**：分類、分組、摘要、分析、報告生成等

### 📁 Toptennews（排名模塊）
- **目的**：識別和排名熱點新聞
- **功能**：生成每日十大新聞

### 📁 Translate（翻譯模塊）
- **目的**：多語言翻譯支持
- **功能**：新聞和專題翻譯

### 📁 Supabase_error_fix（數據修復模塊）
- **目的**：修復在其他處理過程中發現的數據錯誤
- **修復項**：缺失標題、發言人錯誤、相關性匹配錯誤等

---

## 🚀 執行方式

### 基本使用
```bash
python Schedule.py
```

### 並行執行說明
- **默認配置**：使用 CPU 核心數作為最大並行進程數
- **修改並行數**：編輯 `Schedule.py` 中的 `max_workers` 參數
- **當前設置**：`max_workers=1`（順序執行）

### 日誌記錄
- 所有執行日誌都會被記錄
- 日誌格式：`[時間] - [級別] - [訊息]`
- 腳本執行狀態：✅ 成功 / ❌ 失敗

---

## ⚙️ 依賴要求

- Python 3.7+
- 各模塊所需的 Python 包（見各模塊的 `requirements.txt` 或 `env.py`）
- Supabase 訪問權限
- Google News 爬蟲權限
- Gemini API 密鑰

#### Back-End 環境變數
在 `Back-End` 目錄下創建 `.env` 檔案，並配置所需的 API 金鑰和數據庫連線等變數。
```
# Back-End/.env
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_TRANSLATE_API_KEY=your_google_translate_api_key_here
SUPABASE_KEY=your_supabase_key_here
SUPABASE_URL=your_supabase_url_here
```

**注意**：所有 Back-End 中的模組和子目錄（Topic、Translate、Toptennews 等）都會自動讀取 `Back-End/.env` 中的環境變數，無需在各子目錄重複配置。

---

## 📝 配置文件

各模塊包含 `env.py` 文件用於環境變量配置：
- `Back-End/env.py`
- `Attribution/env.py`
- `Supabase_error_fix/env.py`
- `Topic/env.py`
- `Toptennews/env.py`
- `Translate/env.py`
- `Front-End/back-end/env.py`

---

## 🔍 故障排查

| 問題 | 可能原因 | 解決方案 |
|------|--------|--------|
| 腳本無法運行 | 缺少依賴包 | 檢查環境配置和 requirements.txt |
| Supabase 連接失敗 | API 密鑰錯誤 | 驗證 env.py 中的配置 |
| 翻譯失敗 | API 限制 | 檢查翻譯服務配額 |
| 並行執行衝突 | 資源競爭 | 降低 max_workers 數值 |

---

## 📊 數據流

```
Google News
    ↓
爬取 (Crawler)
    ↓
新聞生成 (New_Summary)
    ↓
分析 (Analyze, Attribution)
    ↓
圖片生成 (Category_images)
    ↓
相關性識別 (Relative)
    ↓
翻譯 (Translate)
    ↓
排名 (Toptennews)
    ↓
專題處理 (Topic)
    ↓
數據修復 (Supabase_error_fix)
    ↓
發布系統
```

---

## 📞 維護建議

- 定期檢查日誌文件
- 監控 API 使用配額
- 定期備份 Supabase 數據
- 更新爬蟲策略以應對網站變化
- 優化並行執行參數以平衡速度和穩定性

---

**最後更新**: 2026年1月16日
