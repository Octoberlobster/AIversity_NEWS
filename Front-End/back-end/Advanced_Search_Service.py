import os
import json
from typing import List, Dict, Any, Set
from google import genai  # ✅ 新版 Gemini SDK
from supabase import create_client, Client
import logging
from dotenv import load_dotenv
import difflib
import re

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

class SimpleNewsSearch:
    def __init__(self, gemini_api_key: str, supabase_url: str, supabase_key: str):
        """
        初始化簡化版新聞搜尋系統
        """
        # ✅ 初始化 Gemini Client（新版寫法）
        self.gemini_client = genai.Client(api_key=gemini_api_key)

        # 初始化 Supabase
        self.supabase: Client = create_client(supabase_url, supabase_key)

        # 擴展的相似詞對照表 - 處理錯字、同義詞、縮寫
        self.similar_keywords_map = {
            # 政治人物 - 處理縮寫和錯字
            'trump': ['川普', '特朗普', '川蒲', '川卜', '特普'],
            'biden': ['拜登', '白登', '拜豋', '白豋'],
            'taiwan': ['台灣', '臺灣', '台湾'],
            'china': ['中國', '中华', '大陸', '中国', '大陆'],
            
            # 台灣政治人物
            '賴清德': ['賴德', '賴總統', '賴總', '賴副總統', '賴副', '清德'],
            '賴德': ['賴清德'],
            '柯文哲': ['柯P', '柯市長', '柯主席', '文哲', '阿北'],
            '柯p': ['柯文哲', '柯P'],
            '侯友宜': ['侯市長', '友宜', '侯友'],
            '韓國瑜': ['韓總', '韓市長', '國瑜'],
            '蔡英文': ['小英', '英文', '蔡總統'],
            '馬英九': ['馬總統', '英九', '馬前總統'],
            '朱立倫': ['立倫', '朱主席'],
            '蘇貞昌': ['蘇院長', '貞昌'],
            
            # 政治術語
            '罷免': ['大罷免', '罷免案', '罷免投票'],
            '大罷免': ['罷免'],
            '選舉': ['大選', '選戰', '投票'],
            '公投': ['公民投票', '複決'],
            '立委': ['立法委員'],
            '市長': ['市府首長'],
            '縣長': ['縣府首長'],
            
            # 科技詞彙
            'ai': ['人工智慧', 'AI', '人工智能', 'A.I.'],
            '人工智慧': ['AI', '人工智能'],
            'chatgpt': ['ChatGPT', 'Chat GPT', 'GPT'],
            'openai': ['OpenAI', 'Open AI'],
            
            # 疫情相關
            'covid': ['新冠', '疫情', 'COVID', '新冠肺炎', '武漢肺炎'],
            '新冠': ['COVID', '疫情', '新冠肺炎'],
            '疫情': ['新冠', 'COVID'],
            
            # 經濟詞彙
            '股市': ['股票', '證券', '股價'],
            '房價': ['房市', '不動產', '房地產'],
            '通膨': ['通貨膨脹', '物價'],
            
            # 常見錯字和同義詞
            '川蒲': ['川普', '特朗普'],
            '拜豋': ['拜登'],
            '臺灣': ['台灣'],
            '大陆': ['大陸', '中國'],
            '川普': ['川蒲', '川卜', '特普'],
            '拜登': ['拜豋', '白登'],
            '台灣': ['臺灣', '台湾'],
            
            # 地名縮寫
            '台北': ['北市', '台北市'],
            '新北': ['新北市'],
            '台中': ['中市', '台中市'],
            '台南': ['南市', '台南市'],
            '高雄': ['高市', '高雄市'],
            '桃園': ['桃市', '桃園市'],
            
            # 其他常用詞
            '美國': ['美', 'USA', 'US'],
            '日本': ['日', '東京'],
            '韓國': ['韓', '南韓'],
            '香港': ['港'],
        }

        # 縮寫模式對照表 - 用於檢測可能的縮寫
        self.abbreviation_patterns = {
            r'賴德': '賴清德',
            r'柯P': '柯文哲',
            r'小英': '蔡英文',
            r'韓總': '韓國瑜',
            r'阿北': '柯文哲',
            r'北市': '台北市',
            r'中市': '台中市',
            r'南市': '台南市',
            r'高市': '高雄市',
        }

    def detect_abbreviations(self, text: str) -> List[str]:
        """檢測並擴展縮寫"""
        expanded = []
        for pattern, full_form in self.abbreviation_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                expanded.append(full_form)
                logger.info(f"檢測到縮寫 '{pattern}' -> '{full_form}'")
        return expanded

    def extract_keywords_with_gemini(self, query: str) -> List[str]:
        """使用 Gemini 從查詢中提取關鍵字"""
        prompt = f"""
        請從以下查詢中提取關鍵字，用於新聞標題搜尋。

        查詢: "{query}"

        要求：
        - 提取最重要的關鍵字
        - 每個關鍵字2-8個字
        - 包含人名、地名、事件名詞
        - 處理可能的縮寫（如：賴德 -> 賴清德）
        - 用逗號分隔
        - 只返回關鍵字，不要其他說明
        - 最多5個關鍵字

        範例：
        - "賴德 罷免" -> "賴清德, 罷免"
        - "大罷免案" -> "罷免, 罷免案"
        """
        try:
            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            if response.text:
                keywords = [kw.strip() for kw in response.text.strip().split(",") if kw.strip()]
                # 添加縮寫檢測
                abbreviated_keywords = self.detect_abbreviations(query)
                keywords.extend(abbreviated_keywords)
                # 去重
                keywords = list(set(keywords))
                logger.info(f"提取的關鍵字: {keywords}")
                return keywords
            else:
                logger.warning("Gemini 沒有返回有效回應")
                return [query]
        except Exception as e:
            logger.error(f"Gemini API 錯誤: {e}")
            return [query]

    def get_dynamic_similar_keywords(self, keywords: List[str]) -> List[str]:
        """使用 Gemini 動態生成相似關鍵字"""
        try:
            keywords_str = ", ".join(keywords)
            prompt = f"""
            請為以下關鍵字提供相似詞、同義詞、常見錯別字和不同寫法：

            關鍵字: {keywords_str}

            要求：
            - 包含中英文對照（如：trump -> 川普）
            - 包含常見錯別字（如：川蒲 -> 川普）
            - 包含繁簡體對照（如：臺灣 -> 台灣）
            - 包含同義詞（如：疫情 -> 新冠）
            - 包含縮寫（如：賴德 -> 賴清德）
            - 包含敬語變化（如：賴總統 -> 賴清德）
            - 每個原始關鍵字最多提供5個相似詞
            - 用逗號分隔所有相似詞
            - 只返回相似詞，不要解釋

            範例：
            罷免 -> 大罷免, 罷免案, 罷免投票
            賴清德 -> 賴德, 賴總統, 賴總, 清德
            """
            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            if response.text:
                similar_keywords = [kw.strip() for kw in response.text.strip().split(",") if kw.strip()]
                filtered = [kw for kw in similar_keywords if kw not in keywords]
                logger.info(f"動態生成的相似關鍵字: {filtered}")
                return filtered
            else:
                return []
        except Exception as e:
            logger.error(f"動態相似詞生成錯誤: {e}")
            return []

    def expand_keywords_with_similar(self, keywords: List[str]) -> Set[str]:
        """擴展關鍵字，包含相似詞"""
        expanded = set(keywords)
        
        # 處理每個關鍵字
        for keyword in keywords:
            keyword_lower = keyword.lower()
            keyword_clean = keyword.strip()
            
            # 直接匹配
            if keyword_lower in self.similar_keywords_map:
                expanded.update(self.similar_keywords_map[keyword_lower])
                logger.info(f"關鍵字 '{keyword}' 擴展為: {self.similar_keywords_map[keyword_lower]}")
            
            # 完全匹配（考慮大小寫）
            if keyword_clean in self.similar_keywords_map:
                expanded.update(self.similar_keywords_map[keyword_clean])
                logger.info(f"關鍵字 '{keyword}' 完全匹配擴展為: {self.similar_keywords_map[keyword_clean]}")
            
            # 反向匹配 - 檢查是否為某個主詞的相似詞
            for main_key, similar_words in self.similar_keywords_map.items():
                if keyword_lower in [w.lower() for w in similar_words]:
                    expanded.add(main_key)
                    expanded.update(similar_words)
                    logger.info(f"關鍵字 '{keyword}' 匹配到相似詞群: {[main_key] + similar_words}")
                    break
                    
                # 完全匹配檢查
                if keyword_clean in similar_words:
                    expanded.add(main_key)
                    expanded.update(similar_words)
                    logger.info(f"關鍵字 '{keyword}' 完全匹配到相似詞群: {[main_key] + similar_words}")
                    break
        
        # Gemini 動態相似詞
        dynamic_keywords = self.get_dynamic_similar_keywords(keywords)
        expanded.update(dynamic_keywords)
        
        return expanded

    def search_by_keywords(self, keywords: Set[str]) -> List[str]:
        """使用 OR 邏輯搜尋新聞"""
        try:
            if not keywords:
                return []
            
            # 建構 OR 查詢條件
            or_conditions = []
            for kw in keywords:
                # 對於每個關鍵字，建立不區分大小寫的 LIKE 查詢
                or_conditions.append(f'news_title.ilike.%{kw}%')
            
            or_query = ",".join(or_conditions)
            result = self.supabase.table("single_news").select("story_id").or_(or_query).execute()
            story_ids = [row["story_id"] for row in result.data]
            logger.info(f"使用 {len(keywords)} 個關鍵字，找到 {len(story_ids)} 筆相關新聞")
            logger.info(f"搜尋關鍵字: {list(keywords)}")
            return story_ids
        except Exception as e:
            logger.error(f"Supabase 查詢錯誤: {e}")
            return []

    def fuzzy_match_keywords(self, keywords: List[str], threshold: float = 0.65) -> Set[str]:
        """使用模糊匹配找出相似的關鍵字 - 降低閾值以提高匹配率"""
        expanded = set(keywords)
        
        # 建立所有可能的詞彙集合
        all_words = set()
        for key, sims in self.similar_keywords_map.items():
            all_words.add(key)
            all_words.update(sims)
        
        # 對每個關鍵字進行模糊匹配
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # 使用 difflib 進行模糊匹配
            matches = difflib.get_close_matches(
                keyword_lower, 
                [w.lower() for w in all_words], 
                n=5,  # 增加匹配數量
                cutoff=threshold
            )
            
            for match in matches:
                # 找到匹配的原始單詞
                for word in all_words:
                    if word.lower() == match:
                        expanded.add(word)
                        logger.info(f"模糊匹配: '{keyword}' -> '{word}' (相似度: {difflib.SequenceMatcher(None, keyword_lower, match).ratio():.2f})")
                        
                        # 如果這個詞是主鍵，添加其所有相似詞
                        if word in self.similar_keywords_map:
                            expanded.update(self.similar_keywords_map[word])
                        break
            
            # 額外的部分匹配邏輯 - 處理包含關係
            for word in all_words:
                word_lower = word.lower()
                if len(keyword) >= 2 and len(word) >= 2:
                    # 檢查是否為子字串關係
                    if keyword_lower in word_lower or word_lower in keyword_lower:
                        expanded.add(word)
                        logger.info(f"部分匹配: '{keyword}' <-> '{word}'")
                        if word in self.similar_keywords_map:
                            expanded.update(self.similar_keywords_map[word])
        
        return expanded

    def search(self, query: str, use_fuzzy_match: bool = True) -> Dict[str, Any]:
        """執行搜尋並返回 JSON 格式結果"""
        logger.info(f"開始搜尋: {query}")
        
        # 第一步：提取關鍵字
        original_keywords = self.extract_keywords_with_gemini(query)
        
        # 第二步：擴展相似詞
        expanded_keywords = self.expand_keywords_with_similar(original_keywords)
        
        # 第三步：模糊匹配（如果啟用）
        if use_fuzzy_match:
            fuzzy_keywords = self.fuzzy_match_keywords(original_keywords)
            expanded_keywords.update(fuzzy_keywords)
        
        # 第四步：搜尋新聞
        story_ids = self.search_by_keywords(expanded_keywords)
        
        result = {
            "query": query,
            "original_keywords": original_keywords,
            "expanded_keywords": sorted(list(expanded_keywords)),  # 排序便於查看
            "count": len(story_ids),
            "story_ids": story_ids,
        }
        
        logger.info(f"搜尋完成，找到 {len(story_ids)} 筆結果")
        logger.info(f"關鍵字擴展: {len(original_keywords)} -> {len(expanded_keywords)}")
        
        return result


def search(query: str, use_fuzzy_match: bool = True):
    """API 調用的主要函數"""
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    try:
        logger.info(f"API 調用 - 查詢: {query}")
        
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