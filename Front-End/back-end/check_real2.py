import os
import json
from typing import List, Dict, Optional
from env import supabase, gemini_client
from google import genai
from google.genai import types

class NewsFactChecker:
    @staticmethod
    def get_news_by_story_id(story_id: str) -> Optional[List[Dict]]:
        """根據 story_id 從 Supabase 獲取特定新聞內容作為知識庫"""
        try:
            response = supabase.table('cleaned_news').select('*').eq('story_id', story_id).execute()
            if response.data:
                return response.data
            else:
                return None
        except Exception as e:
            print(f"獲取新聞資料時發生錯誤: {e}")
            return None

    @staticmethod
    def verify_statement_with_knowledge_base(statement: str, knowledge_base: List[Dict]) -> Dict:
        """使用 Gemini 根據知識庫驗證陳述的正確性"""
        
        # 構建知識庫內容
        kb_content = ""
        for i, news in enumerate(knowledge_base, 1):
            media = news.get('media', '未知媒體')
            title = news.get('article_title', '無標題')
            content = news.get('content', '')
            kb_content += f"報導 {i}：\n媒體：{media}\n標題：{title}\n內容：{content}\n\n"

        prompt = f"""
        你是一個專業的事實查核系統。請根據以下知識庫內容，判斷給定陳述的正確性。

        知識庫內容（這是你唯一的參考資料）：
        {kb_content}

        要查核的陳述：
        {statement}

        請嚴格按照以下規則進行判斷：
        1. 如果陳述內容在知識庫中有明確提到或可以合理推導出來，則判斷為正確
        2. 如果陳述內容在知識庫中沒有提到或與知識庫內容矛盾，則判斷為錯誤
        3. 只能基於知識庫內容進行判斷，不能使用外部知識

        你是一個 JSON 生成器。請務必只輸出一個有效的 JSON，格式如下：
        {{
            "is_correct": true或false,
            "confidence": 信心程度(0-100),
            "explanation": "詳細解釋原因",
            "supporting_sources": [
                {{
                    "media": "媒體名稱",
                    "title": "報導標題",
                    "content": "相關的具體敘述內容"
                }}
            ]
        }}

        只回傳 JSON，不要其他說明。
        """

        try:
            response = gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1)  # 降低溫度以提高一致性
            )

            raw_output = response.text.strip() if hasattr(response, "text") else ""
            if not raw_output:
                raise ValueError("Gemini 沒有回傳任何內容")

            # 清理輸出格式
            if raw_output.startswith("```"):
                raw_output = raw_output.strip("`")
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
                "explanation": f"系統錯誤：回傳格式不是合法 JSON: {e}",
                "supporting_sources": []
            }
        except Exception as e:
            print(f"Gemini 驗證時發生錯誤: {e}")
            return {
                "is_correct": False,
                "confidence": 0,
                "explanation": f"系統錯誤：驗證過程發生錯誤: {e}",
                "supporting_sources": []
            }

    def fact_check_by_story_id(self, statement: str, story_id: str) -> str:
        """根據 story_id 對應的 cleaned_news 作為知識庫進行事實查核"""
        print(f"正在查核陳述: {statement}")
        print(f"使用知識庫 story_id: {story_id}")
        
        # 獲取 story_id 對應的所有新聞作為知識庫
        knowledge_base = self.get_news_by_story_id(story_id)
        
        if not knowledge_base:
            return f"錯誤：找不到 story_id 為 {story_id} 的新聞資料，無法進行查核"
        
        print(f"知識庫包含 {len(knowledge_base)} 篇相關報導")
        
        # 使用知識庫進行驗證
        verification_result = self.verify_statement_with_knowledge_base(statement, knowledge_base)
        
        is_correct = verification_result.get('is_correct', False)
        confidence = verification_result.get('confidence', 0)
        explanation = verification_result.get('explanation', '')
        supporting_sources = verification_result.get('supporting_sources', [])

        # 根據結果格式化回答
        result = "🔍針對 " + "{" + statement + "}\n查核結果:\n"
        if is_correct:
            result += f"✅ 正確：此陳述在知識庫中有相關資料支持\n"
            result += f"🎯 信心程度：{confidence}%\n"
            
            if supporting_sources:
                result += "**📚 相關來源：**\n"
                for i, source in enumerate(supporting_sources, 1):
                    media = source.get('media', '未知媒體')
                    title = source.get('title', '無標題')
                    content = source.get('content', '')
                    
                    result += f"{i}. **{title}** \n*來源：{media}*\n"
                    if content:
                        result += f"   📝 相關敘述：{content}\n"
                    result += "\n"
        else:
            result += f"❌ 錯誤：此陳述在知識庫中沒有相關報導提到\n"
            result += f"🔍 詳細說明：{explanation}\n"
        
        return result

    def show_knowledge_base_summary(self, story_id: str):
        """顯示知識庫摘要"""
        knowledge_base = self.get_news_by_story_id(story_id)
        
        if not knowledge_base:
            print(f"找不到 story_id 為 {story_id} 的新聞資料")
            return
        
        print(f"\n📚 知識庫摘要 (story_id: {story_id}):")
        print("=" * 50)
        
        for i, news in enumerate(knowledge_base, 1):
            media = news.get('media', '未知媒體')
            title = news.get('article_title', '無標題')
            content_preview = news.get('content', '')[:100] + "..." if len(news.get('content', '')) > 100 else news.get('content', '')
            
            print(f"{i}. **{title}** *來源：{media}*")
            print(f"   內容預覽：{content_preview}")
            print()

    def interactive_fact_check(self):
        """互動式事實查核界面"""
        print("🔍 新聞事實查核系統")
        print("系統將根據指定 story_id 的 cleaned_news 作為知識庫進行查核")
        print("=" * 60)

        while True:
            statement = input("請輸入要查核的陳述: ").strip()
            if not statement:
                print("請輸入有效的陳述")
                continue
                        
            story_id = input("請輸入 story_id (作為知識庫): ").strip()
            if not story_id:
                print("請輸入有效的 story_id")
                continue
                        
            print("\n🔄 查核中...")
            result = self.fact_check_by_story_id(statement, story_id)
            print(f"\n📋 查核結果:")
            print("-" * 40)
            print(result)