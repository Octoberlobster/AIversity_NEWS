import os
import json
from typing import List, Dict, Any, Set
import google.generativeai as genai
from supabase import create_client, Client
import logging
from dotenv import load_dotenv
import difflib

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
        
        # 預定義的相似詞對照表
        self.similar_keywords_map = {
            # 英文 -> 中文
            'trump': ['川普', '特朗普', '川蒲'],
            'biden': ['拜登', '白登'],
            'taiwan': ['台灣', '臺灣'],
            'china': ['中國', '中华', '大陸'],
            'ai': ['人工智慧', 'AI', '人工智能'],
            'covid': ['新冠', '疫情', 'COVID', '新冠肺炎'],
            
            # 中文相似詞
            '川蒲': ['川普', '特朗普'],
            '拜豋': ['拜登'],
            '臺灣': ['台灣'],
            '大陆': ['大陸', '中國'],
            
            # 常見錯別字
            '川普': ['川蒲', '川卜'],
            '拜登': ['拜豋', '白登'],
            '台灣': ['臺灣', '台湾'],
        }

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

    def expand_keywords_with_similar(self, keywords: List[str]) -> Set[str]:
        """
        擴展關鍵字，包含相似詞
        
        Args:
            keywords: 原始關鍵字列表
            
        Returns:
            擴展後的關鍵字集合
        """
        expanded_keywords = set(keywords)  # 使用 set 避免重複
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # 1. 檢查預定義的相似詞對照表
            if keyword_lower in self.similar_keywords_map:
                expanded_keywords.update(self.similar_keywords_map[keyword_lower])
                logger.info(f"關鍵字 '{keyword}' 擴展為: {self.similar_keywords_map[keyword_lower]}")
            
            # 2. 檢查是否有其他關鍵字的相似詞包含當前關鍵字
            for main_key, similar_words in self.similar_keywords_map.items():
                if keyword_lower in [w.lower() for w in similar_words]:
                    expanded_keywords.add(main_key)
                    expanded_keywords.update(similar_words)
                    logger.info(f"關鍵字 '{keyword}' 匹配到相似詞群: {[main_key] + similar_words}")
                    break
        
        # 3. 使用 Gemini 動態擴展相似詞（可選）
        dynamic_similar = self.get_dynamic_similar_keywords(keywords)
        expanded_keywords.update(dynamic_similar)
        
        logger.info(f"原始關鍵字: {keywords}")
        logger.info(f"擴展後關鍵字: {list(expanded_keywords)}")
        
        return expanded_keywords

    def get_dynamic_similar_keywords(self, keywords: List[str]) -> List[str]:
        """
        使用 Gemini 動態生成相似關鍵字
        
        Args:
            keywords: 原始關鍵字列表
            
        Returns:
            動態生成的相似關鍵字列表
        """
        try:
            keywords_str = ', '.join(keywords)
            prompt = f"""
            請為以下關鍵字提供相似詞、同義詞、常見錯別字和不同寫法：

            關鍵字: {keywords_str}

            要求：
            - 包含中英文對照（如：trump -> 川普）
            - 包含常見錯別字（如：川蒲 -> 川普）
            - 包含繁簡體對照（如：臺灣 -> 台灣）
            - 包含同義詞（如：疫情 -> 新冠）
            - 每個原始關鍵字最多提供3個相似詞
            - 用逗號分隔所有相似詞
            - 只返回相似詞，不要解釋

            範例輸出：特朗普,川蒲,臺灣,台湾,疫情,COVID
            """
            
            response = self.gemini_model.generate_content(prompt)
            
            if response.text:
                similar_text = response.text.strip()
                similar_keywords = [kw.strip() for kw in similar_text.split(',') if kw.strip()]
                
                # 過濾掉原始關鍵字
                filtered_similar = [kw for kw in similar_keywords if kw not in keywords]
                
                logger.info(f"動態生成的相似關鍵字: {filtered_similar}")
                return filtered_similar
            else:
                return []
                
        except Exception as e:
            logger.error(f"動態相似詞生成錯誤: {e}")
            return []

    def search_by_keywords(self, keywords: Set[str]) -> List[str]:
        """
        使用 OR 邏輯搜尋新聞 - 包含任一關鍵字的新聞
        
        Args:
            keywords: 關鍵字集合
            
        Returns:
            匹配的 story_id 列表
        """
        try:
            if not keywords:
                return []
            
            # 建立 OR 查詢條件
            or_conditions = []
            for keyword in keywords:
                or_conditions.append(f'news_title.ilike.%{keyword}%')
            
            # 組合所有條件
            or_query = ','.join(or_conditions)
            
            # 執行查詢
            result = self.supabase.table('single_news').select('story_id').or_(or_query).execute()
            
            story_ids = [row['story_id'] for row in result.data]
            logger.info(f"使用 {len(keywords)} 個關鍵字，找到 {len(story_ids)} 筆相關新聞")
            return story_ids
            
        except Exception as e:
            logger.error(f"Supabase 查詢錯誤: {e}")
            return []

    def fuzzy_match_keywords(self, keywords: List[str], threshold: float = 0.7) -> Set[str]:
        """
        使用模糊匹配找出相似的關鍵字
        
        Args:
            keywords: 原始關鍵字列表
            threshold: 相似度閾值 (0-1)
            
        Returns:
            包含模糊匹配結果的關鍵字集合
        """
        expanded_keywords = set(keywords)
        
        # 從所有預定義的相似詞中找出模糊匹配
        all_predefined_words = set()
        for key, similar_list in self.similar_keywords_map.items():
            all_predefined_words.add(key)
            all_predefined_words.update(similar_list)
        
        for keyword in keywords:
            # 找出相似度超過閾值的詞
            matches = difflib.get_close_matches(
                keyword.lower(), 
                [w.lower() for w in all_predefined_words], 
                n=3, 
                cutoff=threshold
            )
            
            for match in matches:
                # 找到原始大小寫的詞
                for word in all_predefined_words:
                    if word.lower() == match:
                        expanded_keywords.add(word)
                        # 如果找到匹配，也添加其相似詞
                        if word in self.similar_keywords_map:
                            expanded_keywords.update(self.similar_keywords_map[word])
                        break
        
        return expanded_keywords

    def search(self, query: str, use_fuzzy_match: bool = True) -> Dict[str, Any]:
        """
        執行搜尋並返回 JSON 格式結果
        
        Args:
            query: 搜尋查詢
            use_fuzzy_match: 是否使用模糊匹配
            
        Returns:
            包含 story_id 列表的 JSON 格式結果
        """
        logger.info(f"開始搜尋: {query}")
        
        # 1. 使用 Gemini 提取關鍵字
        original_keywords = self.extract_keywords_with_gemini(query)
        
        # 2. 擴展關鍵字（包含相似詞）
        expanded_keywords = self.expand_keywords_with_similar(original_keywords)
        
        # 3. 可選：使用模糊匹配進一步擴展
        if use_fuzzy_match:
            fuzzy_expanded = self.fuzzy_match_keywords(original_keywords)
            expanded_keywords.update(fuzzy_expanded)
        
        # 4. 搜尋匹配的新聞
        story_ids = self.search_by_keywords(expanded_keywords)
        
        # 5. 組織結果
        result = {
            "query": query,
            "original_keywords": original_keywords,
            "expanded_keywords": list(expanded_keywords),
            "count": len(story_ids),
            "story_ids": story_ids
        }
        
        logger.info(f"搜尋完成，找到 {len(story_ids)} 筆結果")
        return result

def search(query: str, use_fuzzy_match: bool = True):
    """
    API 調用的主要函數
    
    Args:
        query: 搜尋查詢
        use_fuzzy_match: 是否使用模糊匹配
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
                "original_keywords": [],
                "expanded_keywords": [],
                "count": 0,
                "story_ids": [],
                "error": "服務配置錯誤"
            }
        
        # 初始化搜尋系統
        search_system = SimpleNewsSearch(GEMINI_API_KEY, SUPABASE_URL, SUPABASE_KEY)
        results = search_system.search(query, use_fuzzy_match)
        logger.info(f"API 調用成功，返回結果: {results}")
        return results
        
    except Exception as e:
        logger.error(f"API 調用錯誤: {e}")
        return {
            "query": query,
            "original_keywords": [],
            "expanded_keywords": [],
            "count": 0,
            "story_ids": [],
            "error": str(e)
        }