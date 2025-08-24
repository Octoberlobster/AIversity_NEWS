# 圖片生成配置檔案
# 修改這些設定來自訂圖片生成行為

import os

class Config:
    # 基本設定
    INPUT_FILE = "final_comprehensive_reports_20250811_184840.json"        # 輸入的新聞JSON檔案
    OUTPUT_DIR = "generated_images_main"       # 輸出目錄
    MODEL_ID = "gemini-2.0-flash-preview-image-generation"  # AI模型ID

    # 處理設定
    MAX_ITEMS = None                    # 限制處理文章數量 (None = 全部)
    MAX_IMAGES_PER_ARTICLE = 1          # 每篇文章生成幾張圖片
    RETRY_TIMES = 3                     # 失敗重試次數
    SLEEP_BETWEEN_CALLS = 0.6           # API呼叫間隔（秒）

    # 路徑設定
    @classmethod
    def get_input_file_path(cls) -> str:
        """獲取輸入檔案的完整路徑"""
        return os.path.join(os.path.dirname(__file__), cls.INPUT_FILE)

    @classmethod
    def get_output_dir_path(cls) -> str:
        """獲取輸出目錄的完整路徑"""
        return os.path.join(os.path.dirname(__file__), cls.OUTPUT_DIR)

    # 說明文字設定
    MAX_DESCRIPTION_LENGTH = 15         # 圖片說明最大字數
    DESCRIPTION_STYLE = {
        "政治": "政治場景",
        "社會": "社會議題", 
        "國際": "國際事務",
        "財經": "財經事件",
        "科技": "科技發展",
        "環境": "環境議題",
        "體育": "體育活動",
        "default": "新聞事件"
    }
