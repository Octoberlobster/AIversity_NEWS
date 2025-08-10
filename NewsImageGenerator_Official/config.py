# 圖片生成配置檔案
# 修改這些設定來自訂圖片生成行為

# 基本設定
INPUT_JSON = "1.json"               # 輸入的新聞JSON檔案（新格式）
OUTPUT_DIR = "output_images1"                   # 輸出目錄 (會在當前目錄下創建)
MODEL_ID = "gemini-2.0-flash-preview-image-generation"  # AI模型ID

# 處理設定
MAX_ITEMS = 1                       # 限制處理文章數量 (先測試3篇，確認正常後再增加)
MAX_IMAGES_PER_ARTICLE = 1          # 每篇文章生成幾張圖片
RETRY_TIMES = 3                     # 失敗重試次數
SLEEP_BETWEEN_CALLS = 0.1           # API呼叫間隔（秒）- 增加間隔確保穩定

# 說明文字設定
MAX_DESCRIPTION_LENGTH = 15         # 圖片說明最大字數
DESCRIPTION_STYLE = {
    "政治": "政治場景",
    "社會": "社會議題", 
    "國際": "國際事務",
    "財經": "財經事件",
    "科技": "科技發展",
    "科學與科技": "科技發展",    # 新格式的類別名稱
    "環境": "環境議題",
    "體育": "體育活動",
    "娛樂": "娛樂新聞",        # 新格式可能的類別
    "健康": "健康議題",        # 新格式可能的類別
    "default": "新聞事件"
}
