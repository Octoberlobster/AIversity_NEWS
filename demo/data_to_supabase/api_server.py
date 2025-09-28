# api_server.py

# 匯入必要的函式庫
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from google.cloud import translate_v2 as translate

# --- 初始化設定 ---

# 載入 .env 檔案中的環境變數
load_dotenv()

# 實例化 FastAPI 應用
# 我們可以提供一些元數據，這些會顯示在 API 文件中
app = FastAPI(
    title="Google Translation API Wrapper",
    description="一個封裝了 Google Cloud Translation API 的簡單服務",
    version="1.0.0",
)

# 實例化一個翻譯客戶端
# 建議在全域範圍內實例化一次，而不是在每個請求中都重新建立
try:
    translate_client = translate.Client()
except Exception as e:
    # 如果在啟動時就無法建立客戶端(例如憑證問題)，直接讓服務失敗會比較好
    raise RuntimeError(f"無法初始化 Google Translate Client: {e}") from e


# --- 定義 API 的資料模型 (Request & Response) ---

class TranslationRequest(BaseModel):
    """定義傳入 API 的請求內容"""
    text: str
    target_language: str
    
    # Pydantic v2 的範例寫法
    class Config:
        json_schema_extra = {
            "example": {
                "text": "こんにちは、世界",
                "target_language": "zh-TW"
            }
        }


class TranslationResponse(BaseModel):
    """定義從 API 回傳的內容"""
    original_text: str
    translated_text: str
    detected_source_language: str
    target_language: str


# --- API 端點 (Endpoints) ---

@app.get("/")
def read_root():
    """根目錄端點，用於確認服務是否正常運行"""
    return {"message": "歡迎使用翻譯 API，請訪問 /docs 查看可用的端點。"}


@app.post("/translate/", response_model=TranslationResponse)
def create_translation(request: TranslationRequest):
    """
    接收文字和目標語言，回傳翻譯結果。
    這是一個 POST 端點，因為它會 "建立" 一個新的翻譯結果。
    """
    try:
        # 呼叫 Google Cloud API 進行翻譯
        result = translate_client.translate(
            request.text, 
            target_language=request.target_language
        )
        
        # 組合我們的標準化回傳格式
        response_data = TranslationResponse(
            original_text=result['input'],
            translated_text=result['translatedText'],
            detected_source_language=result['detectedSourceLanguage'],
            target_language=request.target_language
        )
        
        return response_data
        
    except Exception as e:
        # 如果在翻譯過程中發生錯誤 (例如，無效的語言代碼)，
        # 回傳一個 HTTP 400 錯誤
        raise HTTPException(status_code=400, detail=f"翻譯時發生錯誤: {str(e)}")