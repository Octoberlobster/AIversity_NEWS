import os
import requests
from env import translate_api_key

class Translator:
    def __init__(self):
        """
        初始化翻譯器：
        使用 .env 中的 translate_api_key 作為 Google Translate API 金鑰。
        """
        self.api_key = translate_api_key
        if not self.api_key:
            raise RuntimeError("未找到 translate_api_key，請在 .env 檔案中設定")

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