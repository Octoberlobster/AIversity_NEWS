# 圖片說明生成器使用說明

## 功能說明

`generate_image_descriptions_from_supabase.py` 是一個自動化工具，用於：

1. 從 Supabase `generated_image` 表讀取圖片資料（base64 編碼）
2. 解碼圖片為可分析的格式
3. 根據 `story_id` 從 `single_news` 表讀取完整新聞內容
4. 使用 Google Gemini Vision API 分析圖片內容並結合新聞生成簡短說明（15字以內）
5. 將生成的說明更新回 `generated_image` 表的 `description` 欄位

## 環境需求

### Python 版本
- Python 3.8 或以上

### 必要套件

安裝所需套件：

```bash
pip install supabase python-dotenv google-genai pillow
```

或使用 requirements.txt：

```bash
pip install -r requirements.txt
```

requirements.txt 內容：
```
supabase>=2.0.0
python-dotenv>=1.0.0
google-genai>=0.3.0
pillow>=10.0.0
```

## 設定環境變數

在專案根目錄建立 `.env` 檔案，並設定以下環境變數：

```env
# Supabase 設定
SUPABASE_URL=你的_supabase_url
SUPABASE_KEY=你的_supabase_key

# Google Gemini API 設定
GEMINI_API_KEY=你的_gemini_api_key
# 或使用
GOOGLE_API_KEY=你的_google_api_key
```

## 資料庫結構要求

### generated_image 表結構

必須包含以下欄位：
- `id` (int): 主鍵
- `story_id` (string): 關聯的新聞故事 ID
- `image` (text): base64 編碼的圖片資料
- `description` (text): 圖片說明（本程式會更新此欄位）

### single_news 表結構

必須包含以下欄位：
- `story_id` (string): 新聞故事 ID（與 generated_image 的 story_id 對應）
- `long` (text): 完整新聞內容
- `category` (string): 新聞類別（可選）

## 使用方法

### 基本使用

直接執行腳本處理所有圖片：

```bash
python generate_image_descriptions_from_supabase.py
```

### 調整參數

在 `main()` 函數中可以調整以下參數：

```python
# 限制處理數量（用於測試）
LIMIT = 10  # 只處理前 10 張圖片
# 或
LIMIT = None  # 處理所有圖片

# API 呼叫間隔時間（避免超過 API 限制）
SLEEP_TIME = 2.0  # 每次呼叫間隔 2 秒
```

### 進階設定

#### 修改 Gemini 模型

在 `ImageDescriptionGenerator.__init__()` 中修改：

```python
self.model_name = "gemini-2.0-flash-exp"  # 或其他支援 vision 的模型
```

#### 跳過已有說明的圖片

在 `process_images()` 方法中取消註解以下程式碼：

```python
# 如果已經有說明且不為空，跳過
if current_description and current_description.strip():
    print("⏭ 已有說明，跳過")
    skipped += 1
    continue
```

## 執行流程

1. **初始化連線**
   - 連接 Supabase 資料庫
   - 初始化 Gemini API 客戶端

2. **讀取圖片資料**
   - 從 `generated_image` 表讀取圖片記錄
   - 包含 id, story_id, image (base64), description 等欄位

3. **處理每張圖片**
   - 解碼 base64 圖片資料為 PIL Image 物件
   - 根據 story_id 從 `single_news` 表讀取完整新聞內容
   - 使用 Gemini Vision API 分析圖片和新聞內容
   - 生成 15 字以內的圖片說明

4. **更新資料庫**
   - 將生成的說明更新到 `generated_image` 表的 `description` 欄位

5. **輸出統計結果**
   - 顯示處理總數、成功數、失敗數、跳過數

## 輸出範例

```
圖片說明生成器
從 Supabase generated_image 表讀取圖片並生成說明

============================================================
開始處理圖片說明生成
============================================================

✓ Supabase 套件已載入
✓ Google Genai 套件已載入
正在讀取 generated_image 表...
✓ 成功讀取 10 筆圖片資料

處理進度: 1/10
------------------------------------------------------------
圖片 ID: 123
Story ID: story_456
目前說明: 
正在解碼圖片...
✓ 圖片解碼成功 (1024x768)
正在讀取 story_id=story_456 的新聞...
✓ 新聞內容長度: 1500 字
類別: 政治
正在生成圖片說明...
✓ 生成說明: 政治會議現場照片
正在更新資料庫...
✅ 成功更新圖片 123 的說明
等待 2.0 秒...

...

============================================================
處理完成
============================================================
總計: 10
成功: 9
失敗: 0
跳過: 1
============================================================
```

## 錯誤處理

### 常見錯誤

1. **環境變數未設定**
   ```
   EnvironmentError: 請在 .env 檔案中設定 SUPABASE_URL 和 SUPABASE_KEY
   ```
   解決方法：檢查 .env 檔案是否正確設定

2. **套件未安裝**
   ```
   ImportError: 請先安裝 supabase-py：pip install supabase
   ```
   解決方法：執行 `pip install supabase`

3. **圖片解碼失敗**
   ```
   ❌ 圖片解碼失敗
   ```
   可能原因：
   - base64 字串格式錯誤
   - 圖片資料損壞
   - 不支援的圖片格式

4. **找不到新聞**
   ```
   ⚠ 找不到 story_id=xxx 的新聞
   ```
   可能原因：
   - story_id 不存在於 single_news 表
   - 資料庫連線問題

5. **API 限制**
   - 如果遇到 API 速率限制，增加 `SLEEP_TIME` 參數
   - 建議設定為 2-5 秒之間

## 注意事項

1. **API 配額**
   - Gemini API 有每日/每分鐘呼叫限制
   - 建議先用小批次測試（設定 LIMIT=10）
   - 可透過 SLEEP_TIME 控制呼叫頻率

2. **圖片大小**
   - 大型圖片會增加處理時間和 API 成本
   - 建議先將圖片調整到適當大小再儲存到資料庫

3. **說明長度**
   - 程式會自動截斷超過 15 字的說明
   - 可在提示詞中調整限制

4. **資料備份**
   - 建議在大量更新前先備份資料庫
   - 可先用 LIMIT 參數測試少量資料

## 自訂說明生成邏輯

如需修改說明生成邏輯，可編輯 `generate_description_with_vision()` 方法中的 prompt：

```python
prompt = f"""請根據以下新聞內容和圖片，生成一個簡短的圖片說明。

新聞內容：
{news_content[:500]}

要求：
1. 說明必須在 15 個字以內（包含標點符號）
2. 必須準確描述圖片內容
3. 必須與新聞內容相關
4. 使用客觀、中立的語氣
5. 直接輸出說明文字，不要有任何前綴或後綴

範例格式：
- 政治事件相關場景
- 經濟會議現場照片
- 科技產品展示圖片
"""
```

## 授權

本程式為畢業專案的一部分，使用時請遵守相關授權條款。

## 聯絡資訊

如有問題或建議，請聯繫專案維護者。
