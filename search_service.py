import google.generativeai as genai
from supabase import create_client, Client
import os
import json
import asyncio
from typing import List, Dict, Optional
import re

class SearchService:
    def __init__(self):
        # 初始化 Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # 初始化 Supabase
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase: Client = create_client(supabase_url, supabase_key)
    
    async def search_news(self, query: str) -> Dict:
        """主要搜尋方法"""
        try:
            # 1. 使用 Gemini 分析搜尋關鍵字
            search_terms = await self.analyze_search_query(query)
            
            # 2. 在資料庫中搜尋新聞
            search_results = await self.search_in_database(query, search_terms)
            
            # 3. 移除重複結果
            unique_results = self.remove_duplicates(search_results)
            
            return {
                "query": query,
                "results": unique_results,
                "searchTermsUsed": search_terms,
                "totalFound": len(unique_results)
            }
        
        except Exception as e:
            print(f"搜尋錯誤: {str(e)}")
            raise e
    
    async def analyze_search_query(self, query: str) -> Dict:
        """使用 Gemini 分析搜尋關鍵字"""
        try:
            prompt = f"""
            用戶搜尋關鍵字: "{query}"
            
            請分析這個搜尋關鍵字，並生成相關的搜尋詞彙和同義詞，用於新聞搜尋。
            回傳格式為 JSON，包含以下欄位：
            {{
                "keywords": ["關鍵字1", "關鍵字2", "關鍵字3"],
                "synonyms": ["同義詞1", "同義詞2"],
                "categories": ["可能相關的新聞分類"]
            }}
            
            請確保回傳的是有效的 JSON 格式，不要包含其他文字。
            """
            
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            gemini_response = response.text
            
            # 清理回應文本，移除可能的 markdown 代碼塊標記
            cleaned_response = self.clean_json_response(gemini_response)
            
            try:
                search_terms = json.loads(cleaned_response)
                return search_terms
            except json.JSONDecodeError as e:
                print(f"Gemini 回應解析失敗: {e}")
                print(f"原始回應: {gemini_response}")
                # 使用原始關鍵字作為備選
                return {
                    "keywords": [query],
                    "synonyms": [],
                    "categories": []
                }
        
        except Exception as e:
            print(f"Gemini API 調用失敗: {e}")
            return {
                "keywords": [query],
                "synonyms": [],
                "categories": []
            }
    
    def clean_json_response(self, response: str) -> str:
        """清理 Gemini 回應，提取 JSON 部分"""
        # 移除 markdown 代碼塊標記
        response = re.sub(r'```json\n?', '', response)
        response = re.sub(r'```\n?', '', response)
        
        # 尋找 JSON 物件
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json_match.group()
        
        return response.strip()
    
    async def search_in_database(self, original_query: str, search_terms: Dict) -> List[Dict]:
        """在資料庫中搜尋新聞"""
        try:
            search_results = []
            
            # 組合所有搜尋詞
            all_search_terms = [
                original_query,
                *search_terms.get("keywords", []),
                *search_terms.get("synonyms", [])
            ]
            
            # 移除空值和重複值
            all_search_terms = list(set([term.strip() for term in all_search_terms if term and term.strip()]))
            
            # 1. 先用原始查詢搜尋
            primary_results = await self.query_supabase(original_query)
            search_results.extend(primary_results)
            
            # 2. 如果結果不夠，使用其他關鍵字搜尋
            if len(search_results) < 10 and len(all_search_terms) > 1:
                for term in all_search_terms[1:]:  # 跳過原始查詢
                    additional_results = await self.query_supabase(term)
                    search_results.extend(additional_results)
                    
                    # 如果已經有足夠結果，停止搜尋
                    if len(search_results) >= 20:
                        break
            
            return search_results
        
        except Exception as e:
            print(f"資料庫搜尋錯誤: {e}")
            return []
    
    async def query_supabase(self, search_term: str) -> List[Dict]:
        """執行 Supabase 查詢"""
        try:
            # 使用 OR 條件搜尋標題、內容、摘要
            response = self.supabase.table('news').select('*').or_(
                f'title.ilike.%{search_term}%,'
                f'content.ilike.%{search_term}%,'
                f'summary.ilike.%{search_term}%'
            ).order('published_at', desc=True).limit(10).execute()
            
            return response.data if response.data else []
        
        except Exception as e:
            print(f"Supabase 查詢錯誤: {e}")
            return []
    
    def remove_duplicates(self, results: List[Dict]) -> List[Dict]:
        """移除重複的搜尋結果"""
        seen_ids = set()
        unique_results = []
        
        for result in results:
            result_id = result.get('id')
            if result_id and result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)
        
        return unique_results