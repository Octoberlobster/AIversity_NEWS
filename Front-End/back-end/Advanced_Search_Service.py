import os
import json
from typing import List, Dict, Any
import google.generativeai as genai
from supabase import create_client, Client
import logging
from dotenv import load_dotenv

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

class SimpleNewsSearch:
    def __init__(self, gemini_api_key: str, supabase_url: str, supabase_key: str):
        """
        初始化簡化版新聞搜尋系統
        
        Args:
            gemini_api_key: Gemini API 金鑰
            supabase_url: Supabase 專案 URL
            supabase_key: Supabase API 金鑰
        """
        # 初始化 Gemini
        genai.configure(api_key=gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
        
        # 初始化 Supabase
        self.supabase: Client = create_client(supabase_url, supabase_key)

    def extract_keywords_with_gemini(self, query: str) -> List[str]:
        """
        使用 Gemini 從查詢中提取關鍵字
        
        Args:
            query: 搜尋查詢
            
        Returns:
            提取的關鍵字列表
        """
        prompt = f"""
        請從以下查詢中提取關鍵字，用於新聞標題搜尋。

        查詢: "{query}"

        要求：
        - 提取最重要的關鍵字
        - 每個關鍵字2-8個字
        - 用逗號分隔
        - 只返回關鍵字，不要其他說明
        - 最多5個關鍵字

        範例：如果查詢是"川普的關稅政策對台灣的影響"
        返回：川普,關稅,政策,台灣,影響
        """
        
        try:
            response = self.gemini_model.generate_content(prompt)
            
            if response.text:
                # 清理回應並提取關鍵字
                keywords_text = response.text.strip()
                keywords = [kw.strip() for kw in keywords_text.split(',') if kw.strip()]
                
                logger.info(f"提取的關鍵字: {keywords}")
                return keywords
            else:
                logger.warning("Gemini 沒有返回有效回應")
                return [query]  # 如果失敗，直接使用原始查詢
                
        except Exception as e:
            logger.error(f"Gemini API 錯誤: {e}")
            return [query]  # 如果失敗，直接使用原始查詢

    def search_by_keywords(self, keywords: List[str]) -> List[str]:
        """
        使用關鍵字在 Supabase 中搜尋新聞
        
        Args:
            keywords: 關鍵字列表
            
        Returns:
            匹配的 story_id 列表
        """
        try:
            # 建立搜尋查詢
            query_builder = self.supabase.table('single_news').select('story_id')
            
            # 使用 OR 邏輯搜尋所有關鍵字
            for i, keyword in enumerate(keywords):
                if i == 0:
                    query_builder = query_builder.ilike('news_title', f'%{keyword}%')
                else:
                    query_builder = query_builder.or_(f'news_title.ilike.%{keyword}%')
            
            # 執行查詢
            result = query_builder.execute()
            
            # 提取 story_id 列表
            story_ids = [row['story_id'] for row in result.data]
            
            logger.info(f"找到 {len(story_ids)} 筆相關新聞")
            return story_ids
            
        except Exception as e:
            logger.error(f"Supabase 查詢錯誤: {e}")
            return []

    def search(self, query: str) -> Dict[str, Any]:
        """
        執行搜尋並返回 JSON 格式結果
        
        Args:
            query: 搜尋查詢
            
        Returns:
            包含 story_id 列表的 JSON 格式結果
        """
        logger.info(f"開始搜尋: {query}")
        
        # 1. 使用 Gemini 提取關鍵字
        keywords = self.extract_keywords_with_gemini(query)
        
        # 2. 搜尋匹配的新聞
        story_ids = self.search_by_keywords(keywords)
        
        # 3. 組織結果
        result = {
            "query": query,
            "keywords": keywords,
            "count": len(story_ids),
            "story_ids": story_ids
        }
        
        logger.info(f"搜尋完成，找到 {len(story_ids)} 筆結果")
        return result

def search(query: str):
    """
    API 調用的主要函數
    """
    # 取得環境變數
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    try:
        logger.info(f"API 調用 - 查詢: {query}")
        
        # 檢查必要的環境變數
        if not all([GEMINI_API_KEY, SUPABASE_URL, SUPABASE_KEY]):
            logger.error("缺少必要的環境變數")
            return {
                "query": query,
                "keywords": [],
                "count": 0,
                "story_ids": [],
                "error": "服務配置錯誤"
            }
        
        # 初始化搜尋系統
        search_system = SimpleNewsSearch(GEMINI_API_KEY, SUPABASE_URL, SUPABASE_KEY)
        results = search_system.search(query)
        logger.info(f"API 調用成功，返回結果: {results}")
        return results
        
    except Exception as e:
        logger.error(f"API 調用錯誤: {e}")
        return {
            "query": query,
            "keywords": [],
            "count": 0,
            "story_ids": [],
            "error": str(e)
        }