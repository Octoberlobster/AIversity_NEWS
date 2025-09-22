import os
import json
from typing import List, Dict, Optional

from supabase import create_client, Client
from google import genai
from google.genai import types


class NewsFactChecker:
    def __init__(self, supabase_url: str, supabase_key: str, gemini_api_key: str):
        """
        初始化新聞查核系統
        """
        # 初始化 Supabase 客戶端
        self.supabase: Client = create_client(supabase_url, supabase_key)

        # 初始化 Gemini
        self.client = genai.Client(api_key=gemini_api_key)
        self.model_name = "gemini-2.0-flash"   # 建議用最新的，舊的 "gemini-pro" 可能失效

    def get_news_by_story_id(self, story_id: str) -> Optional[Dict]:
        """根據 story_id 從 Supabase 獲取特定新聞內容"""
        try:
            response = self.supabase.table('cleaned_news').select('*').eq('story_id', story_id).execute()
            if response.data:
                return response.data  # 返回匹配的資料
            else:
                return None
        except Exception as e:
            print(f"獲取新聞資料時發生錯誤: {e}")
            return None

    def search_relevant_news(self, query: str) -> List[Dict]:
        """搜尋與查詢相關的新聞"""
        try:
            response = self.supabase.table('cleaned_news').select('*').ilike('content', f'%{query}%').execute()
            return response.data
        except Exception as e:
            print(f"搜尋新聞時發生錯誤: {e}")
            return []

    def verify_statement_with_gemini(self, statement: str, news_content: str) -> Dict:
        """使用 Gemini 驗證陳述是否與新聞內容相符"""
        prompt = f"""
        請分析以下陳述是否與提供的新聞內容相符：

        要驗證的陳述：
        {statement}

        新聞內容：
        {news_content}
        你是一個 JSON 生成器。
        無論輸入內容是什麼，請務必只輸出一個有效的 JSON，不要加任何額外的文字或說明。
        請以 JSON 格式回答，包含以下欄位：
        - "is_correct": true或false
        - "confidence": 信心程度(0-100)
        - "explanation": 解釋原因
        - "relevant_excerpt": 相關的新聞片段（如果有的話）

        只回傳 JSON，不要其他說明。
        """

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.2)
            )

            raw_output = response.text.strip() if hasattr(response, "text") else ""
            if not raw_output:
                raise ValueError("Gemini 沒有回傳任何內容")

            if raw_output.startswith("```"):
                raw_output = raw_output.strip("`")
            # 移掉可能的 "json\n" 標記
            if raw_output.lower().startswith("json"):
                raw_output = raw_output[4:].strip()

            print("🔎 Gemini raw output:\n", raw_output)  # Debug 用

            result = json.loads(raw_output)
            return result

        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失敗: {e}")
            return {
                "is_correct": False,
                "confidence": 0,
                "explanation": f"回傳格式不是合法 JSON: {e}",
                "relevant_excerpt": ""
            }
        except Exception as e:
            print(f"Gemini 驗證時發生錯誤: {e}")
            return {
                "is_correct": False,
                "confidence": 0,
                "explanation": f"驗證過程發生錯誤: {e}",
                "relevant_excerpt": ""
            }

    def fact_check_by_story_id(self, statement: str, story_id: str) -> str:
        """根據 story_id 對陳述進行事實查核"""
        print(f"正在查核陳述: {statement}")
        print(f"目標新聞 story_id: {story_id}")
        
        # 根據 story_id 獲取特定新聞
        news1 = self.get_news_by_story_id(story_id)
        
        if not news1:
            return f"錯誤：找不到 story_id 為 {story_id} 的新聞"
        
        for news in news1:
            content = news.get('content', '')
            media = news.get('media', '未知媒體')
            title = news.get('article_title', '無標題')
            
            if not content:
                return "錯誤：該新聞沒有內容"
            
            print(f"找到新聞：{media} - {title}")
            
            # 使用 Gemini 驗證陳述
            verification_result = self.verify_statement_with_gemini(statement, content)
            
            is_correct = verification_result.get('is_correct', False)
            confidence = verification_result.get('confidence', 0)
            explanation = verification_result.get('explanation', '')
            excerpt = verification_result.get('relevant_excerpt', '')

            print(is_correct, confidence, explanation, excerpt)  # Debug 用
            if is_correct:
                result = f"正確：在 {media} 的新聞「{title}」中有提到相關敘述\n"
                result += f"解釋：{explanation}\n"
                if excerpt:
                    result += f"相關內容片段：{excerpt}\n"
                result += f"信心程度：{confidence}%"
            else:
                result = f"錯誤：在 {media} 的新聞「{title}」中沒有找到相關敘述\n"
                result += f"解釋：{explanation}\n"
                result += f"信心程度：{confidence}%"
            
        return result

    def interactive_fact_check(self):
        """互動式事實查核界面"""
        print("1. 輸入陳述和 story_id 進行特定新聞查核")

        while True:
            statement = input("請輸入要查核的陳述: ").strip()
            if not statement:
                print("請輸入有效的陳述")
                continue
                    
            story_id = input("請輸入 story_id: ").strip()
            if not story_id:
                print("請輸入有效的 story_id")
                continue
                    
            print("\n查核中...")
            result = self.fact_check_by_story_id(statement, story_id)
            print(f"\n查核結果:\n{result}")

def main():
    SUPABASE_URL = os.getenv('SUPABASE_URL', 'your_supabase_url_here')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'your_supabase_key_here')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'your_gemini_api_key_here')

    if 'your_' in SUPABASE_URL or 'your_' in SUPABASE_KEY or 'your_' in GEMINI_API_KEY:
        print("請先設定環境變數或直接在程式中填入 API 金鑰")
        return

    fact_checker = NewsFactChecker(SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY)
    fact_checker.interactive_fact_check()


if __name__ == "__main__":
    main()