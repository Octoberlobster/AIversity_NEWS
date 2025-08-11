# keyword_processor.py
import os
import json
import time
from typing import List, Dict, Any, Set
from dotenv import load_dotenv
from tqdm import tqdm
import google.generativeai as genai
from config import Config

class KeywordProcessor:
    """處理新聞關鍵字提取與解釋的核心類別"""
    
    def __init__(self):
        """初始化關鍵字處理器"""
        self.model = None
        self.api_config = Config.API_CONFIG
        self.proc_config = Config.PROCESSING_CONFIG
        self._setup_model()

    def _setup_model(self):
        """載入環境變數並初始化 Gemini 模型"""
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("錯誤：找不到 GEMINI_API_KEY，請在 .env 檔案中設定")
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(self.api_config['model_name'])
            print(f"✓ Gemini API ({self.api_config['model_name']}) 初始化成功")
        except Exception as e:
            print(f"✗ 初始化 Gemini 時發生錯誤: {e}")
            raise

    def is_ready(self) -> bool:
        """檢查模型是否已成功初始化"""
        return self.model is not None

    def _clean_response_text(self, text: str) -> str:
        """
        *** 已修正 ***
        清理 Gemini 回覆中的 markdown JSON 標籤
        """
        cleaned_text = text.strip()
        # 檢查並移除開頭的 markdown 標籤
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        elif cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        
        # 檢查並移除結尾的 markdown 標籤
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
            
        return cleaned_text.strip()

    def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        """呼叫 Gemini API 並處理回覆"""
        try:
            response = self.model.generate_content(prompt)
            # 使用修正後的清理函式
            cleaned_text = self._clean_response_text(response.text)
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            print(f"✗ JSON 解析錯誤: {e}\n原始回覆: {response.text}")
            return {}
        except Exception as e:
            print(f"✗ API 呼叫時發生錯誤: {e}")
            return {}

    def extract_keywords_from_text(self, text: str, title: str) -> List[str]:
        """從單篇文本中提取關鍵字"""
        prompt = f"""
        你是一位專業的知識編輯，擅長為大眾讀者解釋複雜概念。
        請從以下新聞內容中，提取 {self.proc_config['keywords_to_extract']} 個對一般大眾而言，最具專業性、技術性或較為艱深難懂的關鍵字。

        目標是篩選出讀者可能需要額外查詢才能完全理解文意的詞彙。
        這些關鍵字應優先考慮：
        - 專業術語 (例如：經濟學、科技、法律領域的術語)
        - 特定的事件或協議名稱
        - 不常見的組織或機構縮寫
        - 具有特定文化或歷史背景的專有名詞

        標題：{title}
        內容：{text}

        請嚴格以 JSON 格式回傳，格式如下：
        {{"keywords": ["關鍵字1", "關鍵字2", "..."]}}
        """

        result = self._call_gemini(prompt)
        time.sleep(self.api_config['call_delay_seconds'])
        return result.get('keywords', [])

    def get_word_explanation(self, word: str) -> Dict[str, Any]:
        """為單一詞彙產生解釋和範例"""
        prompt = f"""
        你是一位知識淵博的詞典編纂專家。
        針對以下詞彙，請提供約 {self.proc_config['explanation_word_limit']} 字的「名詞解釋」和「應用範例」。

        要解釋的詞彙是：「{word}」

        請嚴格依照以下 JSON 格式回傳，不要有任何 markdown 標籤或說明文字：
        {{
          "term": "{word}",
          "definition": "（在此填寫簡潔的名詞解釋）",
          "examples": [
            {{
              "title": "應用例子",
              "text": "（在此填寫應用範例，可包含換行\\n）"
            }}
          ]
        }}
        """
        result = self._call_gemini(prompt)
        time.sleep(self.api_config['call_delay_seconds'])
        return result

    def run(self, input_file: str, output_file: str):
        """執行完整的處理流程"""
        # 1. 讀取資料
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                news_data = json.load(f)
        except FileNotFoundError:
            print(f"✗ 錯誤：找不到輸入檔案 {input_file}")
            return
        
        # 2. 提取所有關鍵字
        print("\n=== 階段一：從新聞中提取關鍵字 ===")
        all_keywords: Set[str] = set()
        for story in tqdm(news_data, desc="處理新聞故事"):
            title = story.get('comprehensive_report', {}).get('title', '未知標題')
            versions = story.get('comprehensive_report', {}).get('versions', {})
            for version_type in self.proc_config['versions_to_process']:
                if version_type in versions:
                    content = versions[version_type]
                    keywords = self.extract_keywords_from_text(content, title)
                    all_keywords.update(keywords)
        
        unique_keywords = sorted(list(all_keywords))
        print(f"✓ 階段一完成：共提取 {len(unique_keywords)} 個不重複關鍵字。")

        # 3. 為關鍵字生成解釋
        print("\n=== 階段二：為關鍵字生成解釋與範例 ===")
        explained_terms = []
        for word in tqdm(unique_keywords, desc="生成詞彙解釋"):
            explanation = self.get_word_explanation(word)
            if explanation and "term" in explanation:
                explained_terms.append(explanation)
            else:
                print(f"⚠ 未能成功解釋詞彙：'{word}'")
        
        print(f"✓ 階段二完成：共成功解釋 {len(explained_terms)} 個詞彙。")
        
        # 4. 儲存最終結果
        final_output = {"terms": explained_terms}
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 處理完成！結果已儲存至：{output_file}")
