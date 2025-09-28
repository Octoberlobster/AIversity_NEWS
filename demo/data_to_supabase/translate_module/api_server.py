# uvicorn api_server:app --reload

from fastapi import FastAPI, HTTPException

from pydantic import BaseModel
from typing import List
import os
import requests
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()

class Translator:
    def __init__(self):
        """
        初始化翻譯器：
        使用 .env 中的 GEMINI_API_KEY 作為 Google Translate API 金鑰。
        """
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError("未找到 GEMINI_API_KEY，請在 .env 檔案中設定")

    def __call__(self, text: str, target_language: str) -> str:
        """
        直接呼叫 Translator 類別實例來翻譯文字。
        :param text: 要翻譯的文字
        :param target_language: 目標語言代碼（如 'en', 'zh-TW'）
        :return: 翻譯後的文字
        """
        return self.translate_text(text, target_language)

    def translate_text(self, text: str, target_language: str) -> str:
        """
        使用 REST API 呼叫 Google Translate 翻譯文字。
        :param text: 要翻譯的文字
        :param target_language: 目標語言代碼（如 'zh-TW'）
        :return: 翻譯後的文字
        """
        url = f"https://translation.googleapis.com/language/translate/v2?key={self.api_key}"
        payload = {
            "q": text,
            "target": target_language,
            "format": "text"
        }
        try:
            resp = requests.post(url, data=payload, timeout=10)
            resp.raise_for_status()
            body = resp.json()
            translations = body.get("data", {}).get("translations", [])
            if not translations:
                raise ValueError("Translate API 回傳空結果")
            return translations[0].get("translatedText", "")
        except Exception as e:
            raise RuntimeError(f"使用 API key 呼叫翻譯失敗: {e}")

# 初始化 FastAPI 應用
app = FastAPI(
    title="翻譯 API",
    description="提供翻譯單一文字或陣列文字的 API",
    version="1.0.0",
)

# 初始化 Translator 實例
translator = Translator()

# 定義請求和回應的資料模型
class TranslationRequest(BaseModel):
    texts: List[str]  # 要翻譯的文字陣列
    target_language: str  # 目標語言代碼（例如 'en', 'zh-TW'）

class TranslationResponse(BaseModel):
    translated_texts: List[str]  # 翻譯後的文字陣列

@app.post("/translate_array/", response_model=TranslationResponse)
def translate_array_endpoint(request: TranslationRequest):
    """
    翻譯陣列中的所有字串。
    """
    try:
        # 呼叫 Translator 的翻譯功能
        translated_texts = [
            translator(text, request.target_language) for text in request.texts
        ]
        return TranslationResponse(translated_texts=translated_texts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻譯時發生錯誤: {str(e)}")