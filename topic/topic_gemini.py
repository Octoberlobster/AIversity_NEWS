"""簡單的 Gemini (Google GenAI) 包裝器

此模組提供一個輕量的 wrapper，方便在專案中呼叫 "gemini-2.5-pro" 模型。
功能：
- 讀取 env 中的 gemini client（若 env 提供）或依 API key 建立新的 client
- 支援簡單的重試（exponential backoff）與常見錯誤處理
- 回傳原始文字結果與更多元的回應資訊

用法範例：
	from topic.topic_gemini import GeminiClientWrapper
	g = GeminiClientWrapper()
	resp = g.generate_text("請給我一句友善的問候語。")
	print(resp["text"])  # 取得純文字
"""

import os
import time
import json
import logging
from typing import Optional, Any, Dict

try:
	from google import genai
	from google.genai import types
	from google.genai.errors import ServerError
except Exception:
	# 若沒有安裝 google-genai，讓 import error 在初始化時顯式出現
	genai = None
	types = None
	ServerError = Exception

from google.api_core.exceptions import ServiceUnavailable

from env import gemini_client  # repository 中可能有初始化的 client

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.StreamHandler())
LOG.setLevel(logging.INFO)


class GeminiClientWrapper:
	"""Wrapper for Google GenAI Gemini models (target: gemini-2.5-pro).

	主要提供 generate_text() 方法，會回傳字典：{'text': str, 'raw': Any}
	"""

	def __init__(self, client: Optional[Any] = None, model: str = "gemini-2.5-pro", max_retries: int = 5, initial_delay: float = 1.0):
		self.model = model
		self.max_retries = max_retries
		self.initial_delay = initial_delay

		if client:
			self.client = client
			LOG.info("使用傳入的 gemini client")
		elif gemini_client is not None:
			# repo 中若已由 env.py 初始化 client，則使用之
			self.client = gemini_client
			LOG.info("使用 env 中的 gemini_client")
		else:
			if genai is None:
				raise RuntimeError("google-genai SDK 未安裝，請安裝：pip install google-genai")
			api_key = os.getenv("GEMINI_API_KEY")
			if not api_key:
				raise RuntimeError("找不到 GEMINI_API_KEY，請在環境變數或 .env 中設定")
			self.client = genai.Client(api_key=api_key)
			LOG.info("已建立新的 Gemini client")

	def _call_model(self, prompt: str, **kwargs) -> Any:
		"""內部呼叫模型，抽象不同版本 API 的差異。

		這裡優先嘗試 client.models.generate_content(...)（較新 SDK 的風格），
		若不存在則嘗試 client.generate_text(...) 或 client.predict。
		返回原始 response 物件。
		"""
		# 儘量支援不同版本的 SDK
		if hasattr(self.client, "models") and hasattr(self.client.models, "generate_content"):
			return self.client.models.generate_content(
				model=self.model,
				contents=prompt,
				**kwargs,
			)

		# fallback: client.generate_text
		if hasattr(self.client, "generate_text"):
			return self.client.generate_text(model=self.model, prompt=prompt, **kwargs)

		# 最後的嘗試：client.predict
		if hasattr(self.client, "predict"):
			return self.client.predict(model=self.model, prompt=prompt, **kwargs)

		raise RuntimeError("提供的 gemini client 不支援已知的呼叫方法")

	def generate_text(self, prompt: str, return_json: bool = False) -> Dict[str, Any]:
		"""使用 gemini 產生文字，包含重試邏輯。

		參數:
			prompt: 要送給模型的文字提示
			return_json: 若為 True，嘗試解析回應為 JSON（若模型回傳 JSON）

		回傳:
			dict with keys: 'text' (str), 'raw' (原始回應物件或 dict)
		"""
		last_exc = None
		for attempt in range(self.max_retries):
			try:
				LOG.info(f"呼叫模型 {self.model} (嘗試 {attempt+1}/{self.max_retries})")
				resp = self._call_model(prompt)

				# 解析常見回應形式
				text = None
				raw = resp
				# 新版 SDK 回傳物件可能有 .text 屬性
				if hasattr(resp, "text") and isinstance(resp.text, str):
					text = resp.text.strip()
				else:
					# 部分版本回傳 choices/outputs 形式
					try:
						as_dict = resp if isinstance(resp, dict) else getattr(resp, "to_dict", lambda: None)()
					except Exception:
						as_dict = None

					if isinstance(as_dict, dict):
						# 嘗試找出文字欄位
						for key in ("text", "content", "output", "outputs", "choices"):
							if key in as_dict:
								text_candidate = as_dict.get(key)
								# 處理 choices 或 outputs
								if isinstance(text_candidate, list) and text_candidate:
									first = text_candidate[0]
									if isinstance(first, dict) and "text" in first:
										text = first.get("text")
									elif isinstance(first, str):
										text = first
								elif isinstance(text_candidate, str):
									text = text_candidate
								if text:
									break

				if text is None:
					# 最後嘗試把 resp 當作字串
					try:
						text = str(resp)
					except Exception:
						text = ""

				# 清理三重反引號包裹的 JSON 或 code block
				if text.startswith("```json") and text.rstrip().endswith("```"):
					text = text[text.find("\n") + 1: text.rfind("```")].strip()
				elif text.startswith("```") and text.rstrip().endswith("```"):
					text = text[text.find("\n") + 1: text.rfind("```")].strip()

				result = {"text": text, "raw": raw}
				if return_json:
					try:
						result["json"] = json.loads(text)
					except Exception:
						result["json"] = None

				return result

			except (ServerError, ServiceUnavailable, ConnectionError, TimeoutError) as e:
				last_exc = e
				if attempt == self.max_retries - 1:
					LOG.error("模型呼叫最終失敗，達到最大重試次數")
					raise
				delay = self.initial_delay * (2 ** attempt)
				LOG.warning(f"模型呼叫發生錯誤: {e}，{delay}s 後重試 (第 {attempt+1}/{self.max_retries})")
				time.sleep(delay)
			except Exception as e:
				# 對於非暫時性錯誤，一樣重試幾次，但最後會拋出
				last_exc = e
				if attempt == self.max_retries - 1:
					LOG.exception("不可恢復的錯誤，停止重試")
					raise
				delay = self.initial_delay * (2 ** attempt)
				LOG.warning(f"模型呼叫發生未知錯誤: {e}，{delay}s 後重試 (第 {attempt+1}/{self.max_retries})")
				time.sleep(delay)

		# 如果所有重試都失敗
		raise last_exc if last_exc is not None else RuntimeError("模型呼叫失敗，無可用例外資訊")


if __name__ == "__main__":
	# 簡單的測試與範例
	wrapper = None
	try:
		wrapper = GeminiClientWrapper()
	except Exception as e:
		LOG.error(f"初始化 GeminiClientWrapper 失敗: {e}")

	if wrapper:
		prompt = "請列出3個2025年9月~11月的美國大事件"
		try:
			out = wrapper.generate_text(prompt)
			print("--- result.text ---")
			print(out.get("text"))
			print("--- raw ---")
			print(out.get("raw"))
		except Exception as e:
			LOG.error(f"呼叫模型失敗: {e}")


