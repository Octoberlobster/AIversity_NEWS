"""
困難關鍵字提取器 - 可存入資料庫版本
從 Supabase single_news 表讀取資料，提取困難關鍵字並生成解釋，可存入資料庫

用法:
  python difficult_keyword_extractor_final.py [limit]

請在 word_analysis_system/.env 設定 GEMINI_API_KEY、SUPABASE_URL 與 SUPABASE_KEY
"""

import os
import json
import time
import sys
import uuid
import logging
from typing import List, Dict, Any, Set, Optional
from dotenv import load_dotenv
from tqdm import tqdm
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class DiffKeywordConfig:
    """困難關鍵字處理器設定"""
    
    # API 設定
    API_CONFIG = {
        'model_name': 'gemini-2.5-flash-lite',
        'call_delay_seconds': 1,  # API 呼叫間隔
        'max_retries': 3,
    }
    
    # 處理設定
    PROCESSING_CONFIG = {
        'explanation_word_limit': 50,  # 解釋字數限制
        'default_limit': None,  # 預設讀取筆數限制
    }
    
    # 資料庫設定
    DB_CONFIG = {
        'table_name': 'single_news',
        'select_fields': ['story_id', 'news_title', 'ultra_short', 'short', 'long'],
        'primary_content_field': 'long',  # 主要用於提取關鍵字的欄位
        'title_field': 'news_title',
        'term_map_table': 'term_map',
        'term_map_fields': ['story_id', 'term_id'],
        'term_table': 'term',
        'term_fields': ['term_id', 'term', 'definition', 'example'],
    }
    
    # 輸出設定
    OUTPUT_CONFIG = {
        'save_to_file': False,
        'output_filename': 'difficult_keywords_output.json',
        'terminal_width': 80,
    }


class DiffKeywordProcessor:
    """困難關鍵字提取與解釋的核心類別"""

    def __init__(self):
        """初始化困難關鍵字處理器"""
        self.client = None
        self.supabase_client = None
        self.api_config = DiffKeywordConfig.API_CONFIG
        self.proc_config = DiffKeywordConfig.PROCESSING_CONFIG
        self.db_config = DiffKeywordConfig.DB_CONFIG
        self._setup_model()
        self._setup_supabase()

    def _setup_model(self):
        """載入環境變數並初始化 Gemini Client"""
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("錯誤：找不到 GEMINI_API_KEY，請在 .env 檔案中設定")

        try:
            # 使用新版 google-genai client
            self.client = genai.Client(api_key=api_key)
            logger.info(f"✓ Gemini Client 初始化成功，使用模型 {self.api_config['model_name']}")
        except Exception as e:
            logger.error(f"✗ 初始化 Gemini Client 時發生錯誤: {e}")
            raise

    def is_ready(self) -> bool:
        """檢查模型和資料庫連線是否已成功初始化"""
        return self.client is not None and self.supabase_client is not None

    def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        """呼叫 Gemini API 並處理回覆（新版 SDK）"""
        for attempt in range(self.api_config['max_retries']):
            try:
                response = self.client.models.generate_content(
                    model=self.api_config['model_name'],
                    contents=[{"role": "user", "parts": [{"text": prompt}]}],
                    config=types.GenerateContentConfig()
                )
                cleaned_text = self._clean_response_text(response.text)
                return json.loads(cleaned_text)
            except json.JSONDecodeError as e:
                logger.warning(f"✗ JSON 解析錯誤 (嘗試 {attempt + 1}/{self.api_config['max_retries']}): {e}")
                if attempt == self.api_config['max_retries'] - 1:
                    logger.error(f"原始回覆: {response.text}")
                    return {}
            except Exception as e:
                logger.warning(f"✗ API 呼叫時發生錯誤 (嘗試 {attempt + 1}/{self.api_config['max_retries']}): {e}")
                if attempt == self.api_config['max_retries'] - 1:
                    return {}
                time.sleep(2)
        return {}

    def _setup_supabase(self):
        """載入環境變數並初始化 Supabase 連線"""
        load_dotenv()
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise EnvironmentError("錯誤：找不到 SUPABASE_URL 或 SUPABASE_KEY，請在 .env 檔案中設定")
        
        try:
            from supabase import create_client
            self.supabase_client = create_client(supabase_url, supabase_key)
            logger.info(f"✓ Supabase 連線 ({supabase_url}) 初始化成功")
        except Exception as e:
            logger.error(f"✗ 初始化 Supabase 時發生錯誤: {e}")
            logger.error("請確認已安裝 supabase-py：pip install supabase-py postgrest-py")
            raise

    def _clean_response_text(self, text: str) -> str:
        """清理 Gemini 回覆中的 markdown JSON 標籤"""
        cleaned_text = text.strip()
        # 檢查並移除開頭的 markdown 標籤
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        elif cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        
        # 檢查並移除結尾的 markdown 標籤
        if cleaned_text.endswith("```json"):
            cleaned_text = cleaned_text[:-7]
        elif cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
            
        return cleaned_text.strip()

    def fetch_combined_data(self, limit: Optional[int] = None, story_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """讀取並合併 single_news 和 term_map 資料"""
        logger.info("=== 讀取合併資料 ===")
        
        # 讀取 single_news 資料
        logger.info("讀取 single_news 資料...")
        try:
            table_name = self.db_config['table_name']
            fields = ','.join(self.db_config['select_fields'])
            
            query = self.supabase_client.table(table_name).select(fields)
            if story_ids:
                query = query.in_('story_id', story_ids)
            
            if limit:
                query = query.limit(limit)
                logger.info(f"限制讀取前 {limit} 筆")
            else:
                logger.info("讀取所有資料")
            
            resp = query.execute()
            
            if getattr(resp, 'error', None):
                logger.error(f"讀取 {table_name} 失敗: {resp.error}")
                return []
            
            news_data = resp.data or []
            logger.info(f"成功讀取 {len(news_data)} 筆新聞資料")
            
        except Exception as e:
            logger.error(f"讀取新聞資料時發生錯誤: {e}")
            return []
        
        # 讀取 term_map 資料
        logger.info("讀取 term_map 資料...")
        try:
            # 直接查詢 term_map，然後再查詢 term
            term_map_resp = self.supabase_client.table(self.db_config['term_map_table']).select('story_id,term_id').execute()
            
            if getattr(term_map_resp, 'error', None):
                print(f"讀取 {self.db_config['term_map_table']} 失敗: {term_map_resp.error}")
                term_map = {}
            else:
                term_map_data = term_map_resp.data or []
                print(f"成功讀取 {len(term_map_data)} 筆 term_map 資料")
                
                # 獲取所有 term_id 對應的 term 名稱
                term_ids = list(set([row.get('term_id') for row in term_map_data if row.get('term_id')]))
                if term_ids:
                    terms_resp = self.supabase_client.table(self.db_config['term_table']).select('term_id,term').in_('term_id', term_ids).execute()
                    
                    if getattr(terms_resp, 'error', None):
                        print(f"讀取 term 表失敗: {terms_resp.error}")
                        term_id_to_term = {}
                    else:
                        term_data = terms_resp.data or []
                        term_id_to_term = {row['term_id']: row['term'] for row in term_data if row.get('term_id') and row.get('term')}
                else:
                    term_id_to_term = {}
                
                # 組織成 story_id -> terms 的字典
                term_map = {}
                for row in term_map_data:
                    story_id = row.get('story_id')
                    term_id = row.get('term_id')
                    term_name = term_id_to_term.get(term_id)

                    if story_id and term_name:
                        if story_id not in term_map:
                            term_map[story_id] = []
                        term_map[story_id].append(term_name)

                logger.info(f"組織 term_map: {len(term_map)} 個不同的 story_id")
            
        except Exception as e:
            logger.error(f"讀取 term_map 資料時發生錯誤: {e}")
            term_map = {}
        
        # 合併資料
        combined_data = []
        for news in news_data:
            story_id = news.get('story_id')
            existing_terms = term_map.get(story_id, [])
            
            # 將 existing_terms 添加到新聞資料中
            news_with_terms = news.copy()
            news_with_terms['existing_terms'] = existing_terms
            combined_data.append(news_with_terms)
        
        logger.info(f"合併完成: {len(combined_data)} 筆新聞資料")
        return combined_data

    def extract_keywords_from_text(self, text: str, title: str) -> List[str]:
        """從單篇文本中提取困難關鍵字"""
        prompt = f"""
        你是一位專業的知識編輯，擅長為高中生讀者解釋複雜概念。
        請從以下新聞內容中，**篩選**出對高中生而言可能需要額外查詢、查字典的詞彙。

        **篩選標準：高中生需要額外查詢的詞彙**
        **選出高中生在課堂上較少接觸，需要額外查詢才能完全理解的詞彙**
        
        必須符合以下條件之一的詞彙：
        - 專業術語：醫學專業術語（如「免疫系統」、「基因突變」）、法律專業術語（如「著作權法」、「智慧財產權」）、工程技術術語（如「半導體」、「人工智慧」）
        - 學術概念：需要進一步學習才能理解的概念（如「通貨膨脹」、「溫室效應」、「量子物理」）
        - 國際組織或專業機構：較新或複雜的組織（如「世界貿易組織」、「國際貨幣基金」、「WHO」、「UNESCO」）
        - 新興科技術語：近年出現的科技詞彙（如「區塊鏈」、「虛擬實境」、「機器學習」、「物聯網」）
        - 金融經濟術語：高中經濟課程較少涉及的概念（如「量化寬鬆」、「匯率操縱」、「期貨市場」）
        - 國際政治術語：需要背景知識的政治概念（如「多邊主義」、「地緣政治」、「制裁措施」）
        - 複雜的社會科學概念：如「社會流動」、「文化多元主義」、「可持續發展」
        
        **不要提取的詞彙：**
        - 高中生日常會使用的詞彙（如「學習」、「工作」、「生活」）
        - 高中課程中常見的基礎概念（如「民主」、「自由」、「環保」、「科技」）
        - 簡單的地名、人名、公司名（除非是需要特殊背景知識的）
        - 日常新聞中常見的詞彙（如「政府」、「經濟」、「社會」、「發展」）
        - 基礎數學、科學概念（如「百分比」、「溫度」、「重力」）
        - 一般商業詞彙（如「公司」、「市場」、「消費者」）

        **判斷原則：**
        - 如果一個高中生在日常對話或基礎課程中能理解，就不要選
        - 如果需要額外查詢資料或字典才能完全理解其含義和重要性，就要選
        - 如果是專業領域的入門概念，且高中課程不常涉及，就要選

        標題：{title}
        內容：{text}

        請篩選出高中生需要額外查詢的專業術語或複雜概念。
        請嚴格以 JSON 格式回傳，格式如下：
        {{"keywords": ["關鍵字1", "關鍵字2", "..."]}}
        """
        result = self._call_gemini(prompt)
        time.sleep(self.api_config['call_delay_seconds'])
        return result.get('keywords', [])

    def get_word_explanation(self, word: str) -> Dict[str, Any]:
        """為單一詞彙產生解釋和實際應用實例"""
        prompt = f"""
        你是一位知識淵博的詞典編纂專家，擅長用具體實例說明概念。
        針對以下詞彙，請提供約 {self.proc_config['explanation_word_limit']} 字的「名詞解釋」和「應用實例」。

        要解釋的詞彙是：「{word}」

        「應用實例」部分，請不要用完整的句子造句。請直接列出該詞彙會被使用到的具體場景、技術或產品。
        格式請像這樣，列舉幾個實際例子：
        - **範例輸入：** 人工智慧
        - **期望的應用實例輸出：** 語音助手（如 Siri、Alexa）、推薦系統、自動駕駛汽車、醫療影像分析。

        請嚴格依照以下 JSON 格式回傳，不要有任何 markdown 標籤或說明文字：
        {{
            "term": "{word}",
            "definition": "（在此填寫簡潔的名詞解釋）",
            "examples": [
                {{
                    "title": "應用實例",
                    "text": "（在此條列式填寫具體的應用場景或產品，而非造句）"
                }}
            ]
        }}
        """
        result = self._call_gemini(prompt)
        time.sleep(self.api_config['call_delay_seconds'])
        return result

    def get_word_explanation_from_context(self, word: str, context: str, title: str = "") -> Dict[str, Any]:
        """根據文章內容為詞彙產生解釋（按照指定格式）"""
        prompt = f"""
        你是一位專業的教育編輯，擅長為高中生解釋複雜概念。
        
        請根據以下新聞內容，為指定的詞彙「{word}」提供適合高中生理解的詳細解釋。
        
        新聞標題：{title}
        新聞內容：{context}
        
        要解釋的詞彙：「{word}」
        
        請提供：
        1. 詳細解釋（100-150字）：用高中生能理解的語言說明該詞彙的含義、背景、重要性等
        2. 相關應用例子（3-5個）：列出該詞彙的具體應用場景、相關產品或實際例子，讓高中生容易理解和記憶
        
        **語言要求：**
        - 避免過於艱深的專業術語
        - 用具體的例子和類比來說明抽象概念
        - 解釋要清晰易懂，適合高中生閱讀理解
        
        請嚴格依照以下 JSON 格式回傳，不要有任何 markdown 標籤或說明文字：
        {{
            "term": "{word}",
            "explanation": "適合高中生理解的詳細解釋（100-150字）",
            "examples": [
                "具體應用例子1",
                "具體應用例子2", 
                "具體應用例子3",
                "具體應用例子4",
                "具體應用例子5"
            ]
        }}
        
        應用例子格式要求：
        - 每個例子要具體明確，使用高中生熟悉的事物
        - 可以包含知名品牌、日常應用、學校可能接觸到的情境
        - 例子要與該詞彙直接相關且容易理解
        - 提供3-5個例子（可以少於5個，但至少3個）
        
        範例格式：
        - term: "人工智慧"
        - explanation: "人工智慧是讓電腦模擬人類思考和學習能力的技術。就像人類能夠學習、推理和做決定一樣，人工智慧讓機器也能執行這些任務..."
        - examples: ["手機的語音助手Siri", "Netflix的電影推薦系統", "Google翻譯", "自動駕駛汽車", "棋類遊戲AI"]
        """
        result = self._call_gemini(prompt)
        time.sleep(self.api_config['call_delay_seconds'])
        return result
    
    def test_word_explanation_by_story_id(self, story_id: str, save_to_db: bool = False):
        """測試功能：根據指定的 story_id 生成詞彙解釋
        
        Args:
            story_id: 要處理的新聞 ID
            save_to_db: 是否將結果存入資料庫
        """
        print(f"\n=== 測試詞彙解釋功能 (story_id: {story_id}) ===")
        if save_to_db:
            print("🔄 模式：生成詞彙解釋並存入資料庫")
        else:
            print("📋 模式：僅生成詞彙解釋預覽")
        
        # 1. 從 single_news 表讀取指定 story_id 的資料
        try:
            table_name = self.db_config['table_name']
            fields = ','.join(self.db_config['select_fields'])
            
            resp = self.supabase_client.table(table_name).select(fields).eq('story_id', story_id).execute()
            
            if getattr(resp, 'error', None):
                print(f"✗ 讀取新聞失敗: {resp.error}")
                return
            
            news_data = resp.data
            if not news_data:
                print(f"✗ 找不到 story_id: {story_id}")
                return
            
            news = news_data[0]
            title = news.get(self.db_config['title_field'], '未知標題')
            content = news.get(self.db_config['primary_content_field'], '')
            
            if not content:
                print(f"✗ story_id {story_id} 的內容為空")
                return
            
            print(f"✓ 成功讀取新聞: {title[:50]}...")
            print(f"✓ 內容長度: {len(content)} 字")
            
        except Exception as e:
            print(f"✗ 讀取新聞資料時發生錯誤: {e}")
            return
        
        # 2. 提取困難關鍵字
        print(f"\n--- 步驟 1: 提取困難關鍵字 ---")
        keywords = self.extract_keywords_from_text(content, title)
        
        if not keywords:
            print("✗ 未找到困難關鍵字")
            return
        
        print(f"✓ 找到 {len(keywords)} 個困難關鍵字:")
        for i, keyword in enumerate(keywords, 1):
            print(f"  {i}. {keyword}")
        
        # 3. 為每個關鍵字生成基於文意的解釋
        print(f"\n--- 步驟 2: 生成詞彙解釋 ---")
        explanations = {}
        
        for keyword in keywords:
            print(f"\n正在為「{keyword}」生成解釋...")
            explanation = self.get_word_explanation_from_context(keyword, content, title)
            
            if explanation and explanation.get('term'):
                explanations[keyword] = explanation
                print(f"✓ 成功生成解釋")
            else:
                print(f"✗ 未能生成解釋")
        
        # 4. 輸出結果
        print(f"\n" + "=" * 80)
        print(f"測試結果摘要")
        print("=" * 80)
        print(f"新聞標題: {title}")
        print(f"story_id: {story_id}")
        print(f"提取關鍵字數: {len(keywords)}")
        print(f"成功解釋數: {len(explanations)}")
        
        # 詳細顯示每個詞彙的解釋
        print(f"\n" + "="*60)
        print("生成的詞彙解釋")
        print("="*60)
        
        for i, (word, explanation) in enumerate(explanations.items(), 1):
            term = explanation.get('term', word)
            explanation_text = explanation.get('explanation', '無解釋')
            examples = explanation.get('examples', [])
            
            print(f"\n【詞彙 {i}】")
            print(f"{term}")
            print(f"{explanation_text}")
            if examples:
                examples_text = "、".join(examples)
                print(f"{examples_text}")
            print("-" * 40)
        
        # 5. 如果選擇存入資料庫，執行資料庫操作
        if save_to_db and explanations:
            print(f"\n--- 步驟 3: 存入資料庫 ---")
            
            # 準備 term_map 資料
            new_combinations = []
            for keyword in keywords:
                new_combinations.append({
                    'story_id': story_id,
                    'term': keyword
                })
            
            # 準備 term 資料
            new_terms = []
            for word, explanation in explanations.items():
                explanation_text = explanation.get('explanation', '')
                examples = explanation.get('examples', [])
                examples_text = "、".join(examples) if examples else ""  # 將例子列表轉為字串
                
                new_terms.append({
                    'term_id': str(uuid.uuid4()),  # 生成唯一的 term_id
                    'term': word,
                    'definition': explanation_text,
                    'example': examples_text  # 將例子列表存入 example 欄位
                })
            
            # 檢查現有資料並執行插入
            print("檢查現有資料...")
            
            # 檢查 term_map 重複性
            existing_term_map = self._check_existing_single_term_map(story_id, keywords)
            filtered_combinations = [combo for combo in new_combinations 
                                   if (combo['story_id'], combo['term']) not in existing_term_map]
            
            # 檢查 term 重複性
            existing_terms = self._check_existing_single_terms(list(explanations.keys()), explanations, {'story_id': story_id})
            filtered_terms = [term for term in new_terms 
                            if term['term'] not in existing_terms]
            
            print(f"準備插入 term_map: {len(filtered_combinations)} 筆")
            print(f"準備插入 term: {len(filtered_terms)} 筆")
            
            # 執行插入
            if filtered_terms:
                term_success = self.insert_term_data(filtered_terms)
            else:
                term_success = True
                print("所有詞彙已存在於 term 表中")
            
            if filtered_combinations:
                term_map_success = self.insert_term_map_data(filtered_combinations)
            else:
                term_map_success = True
                print("所有組合已存在於 term_map 表中")
            
            # 顯示最終結果
            if term_success and term_map_success:
                print("✅ 資料庫儲存完成！")
            else:
                print("❌ 部分資料儲存失敗")
        
        return explanations
    
    def _check_existing_single_term_map(self, story_id: str, keywords: List[str]) -> Set:
        """檢查單一 story_id 的現有 term_map 組合"""
        try:
            table_name = self.db_config['term_map_table']
            resp = self.supabase_client.table(table_name).select('story_id,term').eq('story_id', story_id).execute()
            
            if getattr(resp, 'error', None):
                print(f"讀取現有 term_map 失敗: {resp.error}")
                return set()
            
            existing_combinations = set()
            for row in resp.data or []:
                story_id_val = row.get('story_id')
                term = row.get('term')
                if story_id_val and term:
                    existing_combinations.add((story_id_val, term))
            
            return existing_combinations
            
        except Exception as e:
            print(f"檢查現有 term_map 時發生錯誤: {e}")
            return set()
    
    def _check_existing_single_terms(self, keywords: List[str], explanations: Dict = None, story_context: Dict = None) -> Set:
        """檢查單一詞彙列表的現有 term，並根據文意判斷是否需要重新生成"""
        try:
            table_name = self.db_config['term_table']
            
            # 使用 in_ 查詢檢查多個詞彙，同時獲取完整定義資訊
            resp = self.supabase_client.table(table_name).select('term,definition,example').in_('term', keywords).execute()
            
            if getattr(resp, 'error', None):
                print(f"讀取現有 term 失敗: {resp.error}")
                return set()
            
            existing_terms = set()
            for row in resp.data or []:
                term = row.get('term')
                existing_definition = row.get('definition', '')
                
                if term and explanations and term in explanations:
                    # 如果有新解釋，檢查文意是否相符
                    new_explanation = explanations[term]
                    is_contextually_appropriate = self._check_definition_context_match(
                        term, existing_definition, new_explanation, story_context
                    )
                    
                    if is_contextually_appropriate:
                        existing_terms.add(term)
                        print(f"詞彙 '{term}' 現有定義符合文意，將重用")
                    else:
                        print(f"詞彙 '{term}' 現有定義不符文意，將重新生成")
                        # 不加入 existing_terms，這樣會被視為新詞彙重新生成
                elif term:
                    # 沒有新解釋的情況，直接加入現有詞彙
                    existing_terms.add(term)
            
            return existing_terms
            
        except Exception as e:
            print(f"檢查現有 term 時發生錯誤: {e}")
            return set()

    def insert_term_map_data(self, new_combinations: List[Dict[str, str]]) -> bool:
        """將新的 term_map 組合插入資料庫 (使用 term_id)"""
        if not new_combinations:
            print("沒有 term_map 資料需要插入")
            return True
        
        print("\n=== 開始插入 term_map 資料 ===")
        print(f"準備插入 {len(new_combinations)} 筆資料到 {self.db_config['term_map_table']} 表")
        
        success_count = 0
        error_count = 0
        
        try:
            table_name = self.db_config['term_map_table']
            
            # 批次插入
            batch_size = 100  # 每批插入100筆
            for i in range(0, len(new_combinations), batch_size):
                batch = new_combinations[i:i + batch_size]
                
                try:
                    resp = self.supabase_client.table(table_name).insert(batch).execute()
                    
                    if getattr(resp, 'error', None):
                        print(f"批次 {i//batch_size + 1} 插入失敗: {resp.error}")
                        error_count += len(batch)
                    else:
                        batch_success = len(batch)
                        success_count += batch_success
                        print(f"✓ 批次 {i//batch_size + 1}: 成功插入 {batch_success} 筆")
                
                except Exception as e:
                    print(f"✗ 批次 {i//batch_size + 1} 發生錯誤: {e}")
                    error_count += len(batch)
        
        except Exception as e:
            print(f"✗ 插入 term_map 時發生錯誤: {e}")
            return False
        
        print("\nterm_map 插入結果:")
        print(f"  成功: {success_count} 筆")
        print(f"  失敗: {error_count} 筆")
        
        return error_count == 0

    def insert_term_data(self, new_terms: List[Dict[str, str]]) -> Dict[str, str]:
        """
        將新的關鍵字定義插入 term 表
        返回 term -> term_id 的映射
        """
        if not new_terms:
            print("沒有 term 資料需要插入")
            return {}
        
        print("\n=== 開始插入 term 資料 ===")
        print(f"準備插入 {len(new_terms)} 筆資料到 {self.db_config['term_table']} 表")
        
        success_count = 0
        error_count = 0
        term_to_id_map = {}
        
        try:
            table_name = self.db_config['term_table']
            
            # 為每個詞彙生成 term_id
            terms_with_id = []
            for term_data in new_terms:
                term_id = str(uuid.uuid4())
                term_with_id = {
                    'term_id': term_id,
                    'term': term_data['term'],
                    'definition': term_data['definition'],
                    'example': term_data.get('example', '')
                }
                terms_with_id.append(term_with_id)
                term_to_id_map[term_data['term']] = term_id
            
            # 批次插入
            batch_size = 50  # term 表資料較大，每批插入50筆
            for i in range(0, len(terms_with_id), batch_size):
                batch = terms_with_id[i:i + batch_size]
                
                try:
                    resp = self.supabase_client.table(table_name).insert(batch).execute()
                    
                    if getattr(resp, 'error', None):
                        print(f"批次 {i//batch_size + 1} 插入失敗: {resp.error}")
                        error_count += len(batch)
                        # 移除失敗的詞彙映射
                        for failed_term in batch:
                            term_to_id_map.pop(failed_term['term'], None)
                    else:
                        batch_success = len(batch)
                        success_count += batch_success
                        print(f"✓ 批次 {i//batch_size + 1}: 成功插入 {batch_success} 筆")
                
                except Exception as e:
                    print(f"✗ 批次 {i//batch_size + 1} 發生錯誤: {e}")
                    error_count += len(batch)
                    # 移除失敗的詞彙映射
                    for failed_term in batch:
                        term_to_id_map.pop(failed_term['term'], None)
        
        except Exception as e:
            print(f"✗ 插入 term 時發生錯誤: {e}")
            return {}
        
        print("\nterm 插入結果:")
        print(f"  成功: {success_count} 筆")
        print(f"  失敗: {error_count} 筆")
        print(f"  生成映射: {len(term_to_id_map)} 個")
        
        return term_to_id_map

    def check_existing_term_combinations(self, story_keywords: Dict, term_to_id_map: Dict[str, str]) -> List[Dict[str, str]]:
        """檢查並準備需要插入到 term_map 的新組合 (使用 term_id)"""
        print("\n=== 檢查 term_map 重複性 ===")
        
        # 先取得現有的所有 term_map 組合
        try:
            table_name = self.db_config['term_map_table']
            query = self.supabase_client.table(table_name).select('story_id,term_id')
            resp = query.execute()
            
            if getattr(resp, 'error', None):
                print(f"讀取 {table_name} 失敗: {resp.error}")
                return []
            
            existing_combinations = set()
            for row in resp.data or []:
                story_id = row.get('story_id')
                term_id = row.get('term_id')
                if story_id and term_id:
                    existing_combinations.add((story_id, term_id))
            
            print(f"現有 term_map 組合數量: {len(existing_combinations)}")
            
        except Exception as e:
            print(f"讀取現有 term_map 資料時發生錯誤: {e}")
            return []
        
        # 檢查哪些組合是新的
        new_combinations = []
        
        for story_id, story_data in story_keywords.items():
            new_keywords = story_data.get("new_keywords", [])
            
            for keyword in new_keywords:
                term_id = term_to_id_map.get(keyword)
                if term_id:
                    combination = (story_id, term_id)
                    if combination not in existing_combinations:
                        new_combinations.append({
                            'story_id': story_id,
                            'term_id': term_id
                        })
                else:
                    print(f"警告: 找不到詞彙 '{keyword}' 的 term_id")
        
        print(f"準備插入的新組合數量: {len(new_combinations)}")
        return new_combinations
    
    def _check_definition_context_match(self, word: str, existing_definition: str, new_explanation: Dict, story_context: Dict = None) -> bool:
        """
        使用 AI 判斷現有定義是否符合當前文意
        
        Args:
            word: 要檢查的詞彙
            existing_definition: 資料庫中現有的定義
            new_explanation: 新生成的解釋內容
            story_context: 故事上下文（可選）
        
        Returns:
            bool: True 表示現有定義符合文意，False 表示需要重新生成
        """
        new_definition = new_explanation.get('definition', '')
        
        # 如果沒有新定義或現有定義，直接返回 False
        if not new_definition or not existing_definition:
            return False
        
        prompt = f"""
        你是一位專業的語言學專家，擅長判斷詞彙在不同語境下的含義是否相符。
        
        請比較以下兩個關於詞彙「{word}」的定義，判斷它們是否指向相同的概念和含義：
        
        【現有定義】
        {existing_definition}
        
        【新文意定義】
        {new_definition}
        
        比較要點：
        1. 核心概念是否相同（例如「IP」可能指「智慧財產權」或「網際網路協定」，這是不同概念）
        2. 應用領域是否一致（例如「雲端」在氣象學和資訊科技中含義不同）
        3. 技術層面是否匹配（例如「演算法」在數學和程式設計中的具體含義）
        4. 使用語境是否相符（例如「平台」在建築和網路服務中的意思）
        
        判斷標準：
        - 如果兩個定義指向同一個概念，只是表達方式略有不同 → 相符
        - 如果兩個定義指向完全不同的概念或領域 → 不相符
        - 如果一個定義比另一個更具體或更廣泛，但核心概念相同 → 相符
        - 如果存在歧義但主要含義相同 → 相符
        
        請嚴格以 JSON 格式回傳：
        {{
            "is_match": true/false,
            "reason": "簡短說明判斷理由（不超過50字）"
        }}
        """
        
        try:
            result = self._call_gemini(prompt)
            is_match = result.get('is_match', False)
            reason = result.get('reason', '無法判斷')
            
            print(f"   AI 判斷結果: {'相符' if is_match else '不相符'} - {reason}")
            return is_match
            
        except Exception as e:
            print(f"   AI 判斷時發生錯誤: {e}，預設為不相符")
            return False
        
    def check_existing_terms(self, word_explanations: Dict, story_context: Dict = None) -> tuple[List[Dict[str, str]], Dict[str, str]]:
        """
        檢查並準備需要插入到 term 表的新關鍵字定義
        根據文意比對現有定義，如果不符合就重新生成
        返回: (新詞彙列表, 詞彙到term_id的映射)
        """
        print("\n=== 檢查 term 表重複性與文意符合度 ===")
        
        # 先取得現有的所有 term 完整資料
        try:
            table_name = self.db_config['term_table']
            query = self.supabase_client.table(table_name).select('term,term_id,definition,example')
            resp = query.execute()
            
            if getattr(resp, 'error', None):
                print(f"讀取 {table_name} 失敗: {resp.error}")
                return [], {}
            
            existing_terms = {}  # term -> {'term_id': str, 'definition': str, 'example': str}
            for row in resp.data or []:
                term = row.get('term')
                term_id = row.get('term_id')
                definition = row.get('definition', '')
                example = row.get('example', '')
                if term and term_id:
                    existing_terms[term] = {
                        'term_id': term_id,
                        'definition': definition,
                        'example': example
                    }
            
            print(f"現有 term 表中的關鍵字數量: {len(existing_terms)}")
            
        except Exception as e:
            print(f"讀取現有 term 資料時發生錯誤: {e}")
            return [], {}
        
        # 檢查哪些關鍵字是新的或需要重新生成
        new_terms = []
        term_to_id_map = {}
        
        for word, explanation in word_explanations.items():
            if word in existing_terms:
                # 詞彙已存在，檢查定義是否符合文意
                existing_data = existing_terms[word]
                existing_definition = existing_data['definition']
                
                print(f"\n檢查詞彙 '{word}' 的文意符合度...")
                
                # 使用 AI 比對現有定義與當前文意是否相符
                is_contextually_appropriate = self._check_definition_context_match(
                    word, existing_definition, explanation, story_context
                )
                
                if is_contextually_appropriate:
                    # 現有定義符合文意，使用現有的 term_id
                    term_to_id_map[word] = existing_data['term_id']
                    print(f"✓ 詞彙 '{word}' 現有定義符合文意，使用現有 term_id: {existing_data['term_id']}")
                else:
                    # 現有定義不符合文意，需要重新生成並插入新的定義
                    term_id = str(uuid.uuid4())
                    
                    # 從解釋中提取定義和應用
                    definition = explanation.get('definition', '')
                    examples = explanation.get('examples', [])
                    example_text = examples[0].get('text', '') if examples else ''
                    
                    new_terms.append({
                        'term': word,
                        'definition': definition,
                        'example': example_text
                    })
                    
                    term_to_id_map[word] = term_id
                    print(f"⚠ 詞彙 '{word}' 現有定義不符文意，將生成新定義 (新 term_id: {term_id})")
                    print(f"   原定義: {existing_definition[:50]}...")
                    print(f"   新定義: {definition[:50]}...")
            else:
                # 全新的詞彙，需要插入
                term_id = str(uuid.uuid4())
                
                # 從解釋中提取定義和應用
                definition = explanation.get('definition', '')
                examples = explanation.get('examples', [])
                example_text = examples[0].get('text', '') if examples else ''
                
                new_terms.append({
                    'term': word,
                    'definition': definition,
                    'example': example_text
                })
                
                term_to_id_map[word] = term_id
                print(f"+ 新詞彙 '{word}' 準備插入 (term_id: {term_id})")
        
        print(f"\n準備插入的新關鍵字數量: {len(new_terms)}")
        print(f"總詞彙映射數量: {len(term_to_id_map)}")
        return new_terms, term_to_id_map

    def run(self, limit: Optional[int] = None, story_ids: Optional[List[str]] = None):
        """執行完整的困難關鍵字提取流程"""
        if not self.is_ready():
            logger.error("✗ 系統未就緒，無法執行")
            return

        logger.info("=" * 80)
        logger.info("  困難關鍵字提取系統 - 可存入資料庫版本")
        logger.info("=" * 80)

        # 1. 讀取並合併 Supabase single_news 和 term_map 資料
        news_data = self.fetch_combined_data(limit, story_ids)
        if not news_data:
            logger.warning("未取得任何資料")
            return

        # 2. 提取所有關鍵字，並根據 story_id 組織
        logger.info("=== 階段一：從新聞中提取困難關鍵字 ===")
        story_keywords = {}
        all_keywords: Set[str] = set()
        
        content_field = self.db_config['primary_content_field']
        title_field = self.db_config['title_field']
        
        for news in tqdm(news_data, desc="處理新聞"):
            story_id = news.get('story_id')
            if story_id is None:
                continue

            title = news.get(title_field, '未知標題')
            content = news.get(content_field, '')
            existing_terms = news.get('existing_terms', [])
            
            if not content:
                print(f"⚠ story_id {story_id} 的 {content_field} 欄位為空，跳過")
                continue
            
            # 提取關鍵字
            keywords = self.extract_keywords_from_text(content, title)
            
            # 合併新提取的關鍵字和現有的 terms
            all_story_keywords = list(set(keywords + existing_terms))
            
            # 更新總關鍵字集合
            all_keywords.update(all_story_keywords)
            
            # 將關鍵字加入對應的 story_id
            story_keywords[story_id] = {
                "title": title,
                "keywords": all_story_keywords,
                "new_keywords": keywords,
                "existing_terms": existing_terms
            }

        unique_keywords = sorted(list(all_keywords))
        logger.info(f"✓ 階段一完成：共提取 {len(unique_keywords)} 個不重複關鍵字。")

        # 3. 為關鍵字生成解釋
        logger.info("=== 階段二：為關鍵字生成解釋與範例 ===")
        word_explanations = {}
        for word in tqdm(unique_keywords, desc="生成詞彙解釋"):
            explanation = self.get_word_explanation(word)
            if explanation and "term" in explanation:
                word_explanations[word] = explanation
            else:
                logger.warning(f"⚠ 未能成功解釋詞彙：'{word}'")
        
        logger.info(f"✓ 階段二完成：共成功解釋 {len(word_explanations)} 個詞彙。")

        # 4. 檢查並準備插入資料
        logger.info("=== 階段三：檢查重複性並準備插入 ===")
        # 準備故事上下文資訊供 AI 判斷使用
        story_context = {
            'story_keywords': story_keywords,
            'total_stories': len(story_keywords)
        }
        
        new_terms, term_to_id_map = self.check_existing_terms(word_explanations, story_context)
        
        # 5. 執行資料庫插入
        logger.info("=== 階段四：執行資料庫插入 ===")
        
        # 先插入 term 表（關鍵字定義）
        if new_terms:
            term_id_map_from_insert = self.insert_term_data(new_terms)
            # 合併新插入的詞彙 term_id 映射
            term_to_id_map.update(term_id_map_from_insert)
            term_success = len(term_id_map_from_insert) > 0
        else:
            print("沒有新詞彙需要插入到 term 表")
            term_success = True
        
        # 然後準備 term_map 關聯
        new_combinations = self.check_existing_term_combinations(story_keywords, term_to_id_map)
        
        # 再插入 term_map 表（story_id 和 term_id 的關聯）
        term_map_success = self.insert_term_map_data(new_combinations)

        # 6. 顯示最終結果
        logger.info("=" * 80)
        logger.info("  執行完成摘要")
        logger.info("=" * 80)
        logger.info(f"✓ 處理新聞數量: {len(story_keywords)}")
        logger.info(f"✓ 不重複關鍵字: {len(unique_keywords)}")
        logger.info(f"✓ 成功解釋詞彙: {len(word_explanations)}")
        
        if new_terms:
            status = "✓ 成功" if term_success else "✗ 失敗"
            logger.info(f"{status} 插入 term 表: {len(new_terms)} 個新關鍵字")
        
        if new_combinations:
            status = "✓ 成功" if term_map_success else "✗ 失敗"
            logger.info(f"{status} 插入 term_map 表: {len(new_combinations)} 筆新組合")
        
        logger.info("=" * 80)


def main():
    """主程式入口"""
    print("=" * 80)
    print("  困難關鍵字提取系統 - 可存入資料庫版本")
    print("=" * 80)
    
    # 解析指令列參數
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        
        # 檢查是否為測試模式
        if first_arg == "test" and len(sys.argv) > 2:
            story_id = sys.argv[2]
            
            # 檢查是否要存入資料庫
            save_to_db = False
            if len(sys.argv) > 3 and sys.argv[3] == "--save":
                save_to_db = True
                print(f"✓ 測試模式: 使用 story_id = {story_id} (存入資料庫)")
            else:
                print(f"✓ 測試模式: 使用 story_id = {story_id} (僅預覽)")
            
            try:
                processor = DiffKeywordProcessor()
                if processor.is_ready():
                    processor.test_word_explanation_by_story_id(story_id, save_to_db)
                else:
                    print("✗ 系統未就緒，無法執行測試")
            except EnvironmentError as e:
                print(f"✗ 環境錯誤：{e}")
                print("請檢查您的 .env 設定檔。")
            except Exception as e:
                print(f"✗ 發生未預期的錯誤：{e}")
            
            return
        
        # 一般模式：解析 limit 參數
        try:
            limit = int(first_arg)
            print(f"✓ 設定讀取限制: {limit} 筆")
        except ValueError:
            print("⚠ 無效的 limit 參數，將讀取所有資料")
            limit = None
    else:
        limit = None
        print("✓ 一般模式: 處理所有資料")
    
    try:
        # 初始化並執行處理器
        processor = DiffKeywordProcessor()
        if processor.is_ready():
            processor.run(limit)
        
    except EnvironmentError as e:
        print(f"✗ 環境錯誤：{e}")
        print("請檢查您的 .env 設定檔。")
        sys.exit(1)
    except Exception as e:
        print(f"✗ 發生未預期的錯誤：{e}")
        sys.exit(1)
        
    print("\n" + "=" * 80)
    print("系統執行完畢。")
    print("=" * 80)


if __name__ == "__main__":
    main()
