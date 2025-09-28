# 匯入必要的函式庫
from google.cloud import translate_v2 as translate
from dotenv import load_dotenv
import os

# --- 主要修改處 ---
# 載入 .env 檔案中的環境變數
# 這行程式碼會自動尋找同目錄下的 .env 檔案，並讀取其中的設定
load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
# --------------------

def translate_text(target_language: str, text: str) -> dict:
    """
    使用 Google Cloud Translation API 翻譯文字

    Args:
        target_language (str): 目標語言代碼 (例如 'en', 'ja', 'zh-TW')
        text (str): 要翻譯的文字

    Returns:
        dict: 包含翻譯結果的字典
    """
    try:
        # 實例化一個翻譯客戶端
        # 客戶端函式庫會自動從環境變數中尋找 GOOGLE_APPLICATION_CREDENTIALS
        translate_client = translate.Client()

        # 進行翻譯
        result = translate_client.translate(text, target_language=target_language)

        print(f"原文 ({result['detectedSourceLanguage']}): {result['input']}")
        print(f"翻譯 ({target_language}): {result['translatedText']}")
        
        return result

    except Exception as e:
        print(f"發生錯誤: {e}")
        return {}

# --- 主要執行區塊 (維持不變) ---
if __name__ == '__main__':
    # 範例 1：將中文翻譯成英文
    print("--- 範例 1: 中文 -> 英文 ---")
    text_to_translate_1 = "你好，世界！這是一個測試。"
    translate_text(target_language='en', text=text_to_translate_1)

    print("\n" + "="*30 + "\n")

    # 範例 2：將英文翻譯成日文
    print("--- 範例 2: 英文 -> 日文 ---")
    text_to_translate_2 = "Google Cloud Platform is powerful and easy to use."
    translate_text(target_language='ja', text=text_to_translate_2)

    print("\n" + "="*30 + "\n")

    # 範例 3：自動偵測來源語言，並翻譯成繁體中文
    print("--- 範例 3: 自動偵測 -> 繁體中文 ---")
    text_to_translate_3 = "La Tour Eiffel est le symbole de Paris."
    translate_text(target_language='zh-TW', text=text_to_translate_3)