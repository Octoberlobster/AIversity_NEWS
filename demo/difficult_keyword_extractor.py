"""
困難關鍵字提取器 - 仿照 keyword_processor 架構
從 Supabase single_news 表讀取資料，提取困難關鍵字並生成解釋

用法:
  python difficult_keyword_extractor.py [limit]

請在 word_analysis_system/.env 設定 GEMINI_API_KEY、SUPABASE_URL 與 SUPABASE_KEY
"""

import os
import json
import time
import sys
from typing import List, Dict, Any, Set, Optional
from dotenv import load_dotenv
from tqdm import tqdm
import google.generativeai as genai


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
        'term_map_fields': ['story_id', 'term'],
        'term_table': 'term',
        'term_fields': ['term', 'definition', 'example'],
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
        self.model = None
        self.supabase_client = None
        self.api_config = DiffKeywordConfig.API_CONFIG
        self.proc_config = DiffKeywordConfig.PROCESSING_CONFIG
        self.db_config = DiffKeywordConfig.DB_CONFIG
        self._setup_model()
        self._setup_supabase()

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
            print(f"✓ Supabase 連線 ({supabase_url}) 初始化成功")
        except Exception as e:
            print(f"✗ 初始化 Supabase 時發生錯誤: {e}")
            print("請確認已安裝 supabase-py：pip install supabase-py postgrest-py")
            raise

    def is_ready(self) -> bool:
        """檢查模型和資料庫連線是否已成功初始化"""
        return self.model is not None and self.supabase_client is not None

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

    def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        """呼叫 Gemini API 並處理回覆"""
        for attempt in range(self.api_config['max_retries']):
            try:
                response = self.model.generate_content(prompt)
                # 使用修正後的清理函式
                cleaned_text = self._clean_response_text(response.text)
                return json.loads(cleaned_text)
            except json.JSONDecodeError as e:
                print(f"✗ JSON 解析錯誤 (嘗試 {attempt + 1}/{self.api_config['max_retries']}): {e}")
                if attempt == self.api_config['max_retries'] - 1:
                    print(f"原始回覆: {response.text}")
                    return {}
            except Exception as e:
                print(f"✗ API 呼叫時發生錯誤 (嘗試 {attempt + 1}/{self.api_config['max_retries']}): {e}")
                if attempt == self.api_config['max_retries'] - 1:
                    return {}
                time.sleep(2)  # 重試前等待
        return {}

    def fetch_single_news(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """從 Supabase single_news 表讀取資料"""
        print("讀取 single_news 資料...")
        
        try:
            table_name = self.db_config['table_name']
            fields = ','.join(self.db_config['select_fields'])
            
            query = self.supabase_client.table(table_name).select(fields)
            
            if limit:
                query = query.limit(limit)
                print(f"限制讀取前 {limit} 筆")
            else:
                print("讀取所有資料")
            
            resp = query.execute()
            
            if getattr(resp, 'error', None):
                print(f"讀取 {table_name} 失敗: {resp.error}")
                return []
            
            rows = resp.data or []
            print(f"成功讀取 {len(rows)} 筆資料")
            return rows
            
        except Exception as e:
            print(f"讀取資料時發生錯誤: {e}")
            return []

    def fetch_term_map(self) -> Dict[str, List[str]]:
        """從 Supabase term_map 表讀取資料，並組織成 story_id -> terms 的字典"""
        print("讀取 term_map 資料...")
        
        try:
            table_name = self.db_config['term_map_table']
            fields = ','.join(self.db_config['term_map_fields'])
            
            query = self.supabase_client.table(table_name).select(fields)
            resp = query.execute()
            
            if getattr(resp, 'error', None):
                print(f"讀取 {table_name} 失敗: {resp.error}")
                return {}
            
            rows = resp.data or []
            print(f"成功讀取 {len(rows)} 筆 term_map 資料")
            
            # 組織成 story_id -> terms 的字典
            term_map = {}
            for row in rows:
                story_id = row.get('story_id')
                term = row.get('term')
                
                if story_id and term:
                    if story_id not in term_map:
                        term_map[story_id] = []
                    term_map[story_id].append(term)
            
            print(f"組織 term_map: {len(term_map)} 個不同的 story_id")
            return term_map
            
        except Exception as e:
            print(f"讀取 term_map 資料時發生錯誤: {e}")
            return {}

    def fetch_combined_data(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """讀取並合併 single_news 和 term_map 資料"""
        print("\n=== 讀取合併資料 ===")
        
        # 讀取 single_news 資料
        news_data = self.fetch_single_news(limit)
        if not news_data:
            return []
        
        # 讀取 term_map 資料
        term_map = self.fetch_term_map()
        
        # 合併資料
        combined_data = []
        for news in news_data:
            story_id = news.get('story_id')
            existing_terms = term_map.get(story_id, [])
            
            # 將 existing_terms 添加到新聞資料中
            news_with_terms = news.copy()
            news_with_terms['existing_terms'] = existing_terms
            combined_data.append(news_with_terms)
        
        print(f"合併完成: {len(combined_data)} 筆新聞資料，其中 {len([n for n in combined_data if n['existing_terms']])} 筆有現有關鍵字")
        return combined_data

    def extract_keywords_from_text(self, text: str, title: str) -> List[str]:
        """從單篇文本中提取困難關鍵字"""
        prompt = f"""
        你是一位專業的知識編輯，擅長為大眾讀者解釋複雜概念。
        請從以下新聞內容中，**嚴格篩選**出對一般大眾而言，最具專業性、技術性或較為艱深難懂的關鍵字。
        
        **嚴格標準：只提取真正困難的詞彙**
        必須符合以下至少一個嚴格條件：
        - 高度專業術語（需要專業背景才能理解，如醫學、法律、工程、金融專業術語）
        - 外來語或縮寫（一般人不熟悉的英文縮寫、組織名稱）
        - 特定領域概念（需要特殊知識背景才能理解的概念）
        - 新興技術術語（如人工智慧、區塊鏈等新科技名詞）
        
        **不要提取的詞彙：**
        - 常見的地名、人名、公司名（除非非常專業或罕見）
        - 一般性形容詞、動詞、副詞
        - 日常生活常見詞彙
        - 簡單的數字、時間、比例
        - 政治人物姓名（除非是專門術語）
        
        **提取原則：寧缺勿濫，只選擇真正需要解釋的困難詞彙**

        標題：{title}
        內容：{text}

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

    def print_progress_summary(self, story_keywords: Dict, all_keywords: Set[str]):
        """印出進度摘要"""
        width = DiffKeywordConfig.OUTPUT_CONFIG['terminal_width']
        print("\n" + "=" * width)
        print("  困難關鍵字提取進度摘要")
        print("=" * width)
        print(f"處理新聞數量: {len(story_keywords)}")
        print(f"不重複關鍵字總數: {len(all_keywords)}")
        print(f"平均每篇關鍵字數: {sum(len(data['keywords']) for data in story_keywords.values()) / len(story_keywords):.1f}")
        print("=" * width)

    def check_existing_term_combinations(self, story_keywords: Dict) -> List[Dict[str, str]]:
        """檢查並準備需要插入到 term_map 的新組合"""
        print("\n=== 檢查 term_map 重複性 ===")
        
        # 先取得現有的所有 term_map 組合
        try:
            table_name = self.db_config['term_map_table']
            query = self.supabase_client.table(table_name).select('story_id,term')
            resp = query.execute()
            
            if getattr(resp, 'error', None):
                print(f"讀取 {table_name} 失敗: {resp.error}")
                return []
            
            existing_combinations = set()
            for row in resp.data or []:
                story_id = row.get('story_id')
                term = row.get('term')
                if story_id and term:
                    existing_combinations.add((story_id, term))
            
            print(f"現有 term_map 組合數量: {len(existing_combinations)}")
            
        except Exception as e:
            print(f"讀取現有 term_map 資料時發生錯誤: {e}")
            return []
        
        # 檢查哪些組合是新的
        new_combinations = []
        total_new_keywords = 0
        
        for story_id, story_data in story_keywords.items():
            new_keywords = story_data.get("new_keywords", [])
            
            for keyword in new_keywords:
                combination = (story_id, keyword)
                if combination not in existing_combinations:
                    new_combinations.append({
                        'story_id': story_id,
                        'term': keyword
                    })
                    total_new_keywords += 1
        
        print(f"準備插入的新組合數量: {len(new_combinations)}")
        return new_combinations

    def check_existing_terms(self, word_explanations: Dict) -> List[Dict[str, str]]:
        """檢查並準備需要插入到 term 表的新關鍵字定義"""
        print("\n=== 檢查 term 表重複性 ===")
        
        # 先取得現有的所有 term
        try:
            table_name = self.db_config['term_table']
            query = self.supabase_client.table(table_name).select('term')
            resp = query.execute()
            
            if getattr(resp, 'error', None):
                print(f"讀取 {table_name} 失敗: {resp.error}")
                return []
            
            existing_terms = set()
            for row in resp.data or []:
                term = row.get('term')
                if term:
                    existing_terms.add(term)
            
            print(f"現有 term 表中的關鍵字數量: {len(existing_terms)}")
            
        except Exception as e:
            print(f"讀取現有 term 資料時發生錯誤: {e}")
            return []
        
        # 檢查哪些關鍵字是新的
        new_terms = []
        
        for word, explanation in word_explanations.items():
            if word not in existing_terms:
                # 從解釋中提取定義和應用
                definition = explanation.get('definition', '')
                examples = explanation.get('examples', [])
                example_text = examples[0].get('text', '') if examples else ''
                
                new_terms.append({
                    'term': word,
                    'definition': definition,
                    'example': example_text
                })
        
        print(f"準備插入的新關鍵字數量: {len(new_terms)}")
        return new_terms

    def display_term_insertion_preview(self, new_terms: List[Dict[str, str]]):
        """顯示準備插入 term 表的資料預覽"""
        width = DiffKeywordConfig.OUTPUT_CONFIG['terminal_width']
        
        print("\n" + "=" * width)
        print("  準備插入 term 表的資料預覽 (資料庫格式)")
        print("=" * width)
        
        if not new_terms:
            print("沒有新的關鍵字需要插入到 term 表")
            return
        
        print(f"總計準備插入: {len(new_terms)} 筆關鍵字定義")
        print(f"目標資料表: {self.db_config['term_table']}")
        
        print("\n資料庫插入格式預覽 (前5筆):")
        print("-" * 80)
        print("INSERT INTO term (term, definition, example) VALUES")
        
        # 顯示前5筆的完整SQL格式
        display_limit = min(5, len(new_terms))
        for i, term_data in enumerate(new_terms[:display_limit]):
            term = term_data['term']
            definition = term_data['definition']
            example = term_data['example']
            
            # 處理可能的單引號轉義
            escaped_term = term.replace("'", "''")
            escaped_definition = definition.replace("'", "''")
            escaped_example = example.replace("'", "''")
            
            if i == len(new_terms) - 1 or i == display_limit - 1:
                print(f"  ('{escaped_term}', '{escaped_definition}', '{escaped_example}');")
            else:
                print(f"  ('{escaped_term}', '{escaped_definition}', '{escaped_example}'),")
        
        if len(new_terms) > display_limit:
            print(f"  ... (還有 {len(new_terms) - display_limit} 筆資料)")
        
        print("-" * 80)
        
        print("\nJSON 格式預覽 (前3筆):")
        print("-" * 80)
        for i, term_data in enumerate(new_terms[:3]):
            print(f"第 {i+1} 筆:")
            print("  {")
            print(f"    \"term\": \"{term_data['term']}\",")
            print(f"    \"definition\": \"{term_data['definition']}\",")
            print(f"    \"example\": \"{term_data['example']}\"")
            print("  }")
            if i < 2 and i < len(new_terms) - 1:
                print("  ,")
        
        if len(new_terms) > 3:
            print(f"  ... (還有 {len(new_terms) - 3} 筆)")
        
        print("-" * 80)
        
        print("\n詳細內容預覽 (前3筆):")
        print("-" * 80)
        for i, term_data in enumerate(new_terms[:3]):
            print(f"\n【關鍵字 {i+1}】: {term_data['term']}")
            print(f"定義: {term_data['definition']}")
            print(f"應用: {term_data['example']}")
            print("-" * 40)
        
        if len(new_terms) > 3:
            print(f"... 還有 {len(new_terms) - 3} 個關鍵字")
        
        print("\n統計摘要:")
        print("-" * 40)
        print(f"總計新關鍵字: {len(new_terms)} 個")
        
        # 統計定義和應用的長度
        avg_def_length = sum(len(t['definition']) for t in new_terms) / len(new_terms) if new_terms else 0
        avg_example_length = sum(len(t['example']) for t in new_terms) / len(new_terms) if new_terms else 0
        
        print(f"平均定義長度: {avg_def_length:.1f} 字")
        print(f"平均應用長度: {avg_example_length:.1f} 字")
        
        # 檢查空白內容
        empty_definitions = sum(1 for t in new_terms if not t['definition'].strip())
        empty_examples = sum(1 for t in new_terms if not t['example'].strip())
        
        if empty_definitions > 0:
            print(f"⚠️  空白定義: {empty_definitions} 個")
        if empty_examples > 0:
            print(f"⚠️  空白應用: {empty_examples} 個")
        
        print("-" * 40)
        
        print("\n" + "=" * width)
        print("⚠️  注意: 以上資料尚未插入資料庫，僅供預覽確認")
        print("=" * width)

    def display_insertion_preview(self, new_combinations: List[Dict[str, str]]):
        """顯示準備插入 term_map 的資料預覽"""
        width = DiffKeywordConfig.OUTPUT_CONFIG['terminal_width']
        
        print("\n" + "=" * width)
        print("  準備插入 term_map 的資料預覽 (資料庫格式)")
        print("=" * width)
        
        if not new_combinations:
            print("沒有新的組合需要插入到 term_map")
            return
        
        print(f"總計準備插入: {len(new_combinations)} 筆資料")
        print(f"目標資料表: {self.db_config['term_map_table']}")
        
        print("\n資料庫插入格式預覽:")
        print("-" * 80)
        print("INSERT INTO term_map (story_id, term) VALUES")
        
        # 顯示前10筆的完整SQL格式
        display_limit = min(10, len(new_combinations))
        for i, combo in enumerate(new_combinations[:display_limit]):
            story_id = combo['story_id']
            term = combo['term']
            
            # 處理可能的單引號轉義
            escaped_term = term.replace("'", "''")
            
            if i == len(new_combinations) - 1 or i == display_limit - 1:
                print(f"  ('{story_id}', '{escaped_term}');")
            else:
                print(f"  ('{story_id}', '{escaped_term}'),")
        
        if len(new_combinations) > display_limit:
            print(f"  ... (還有 {len(new_combinations) - display_limit} 筆資料)")
        
        print("-" * 80)
        
        print("\nJSON 格式預覽 (前5筆):")
        print("-" * 50)
        for i, combo in enumerate(new_combinations[:5]):
            print(f"第 {i+1} 筆:")
            print("  {")
            print(f"    \"story_id\": \"{combo['story_id']}\",")
            print(f"    \"term\": \"{combo['term']}\"")
            print("  }")
            if i < 4 and i < len(new_combinations) - 1:
                print("  ,")
        
        if len(new_combinations) > 5:
            print(f"  ... (還有 {len(new_combinations) - 5} 筆)")
        
        print("-" * 50)
        
        # 統計每個 story_id 的新關鍵字數量
        grouped_by_story = {}
        for combo in new_combinations:
            story_id = combo['story_id']
            if story_id not in grouped_by_story:
                grouped_by_story[story_id] = []
            grouped_by_story[story_id].append(combo['term'])
        
        print("\n按 story_id 統計:")
        print("-" * 40)
        for story_id, terms in grouped_by_story.items():
            print(f"Story ID {story_id}: {len(terms)} 個新關鍵字")
            # 顯示前3個關鍵字作為示例
            sample_terms = terms[:3]
            print(f"  示例: {', '.join(sample_terms)}")
            if len(terms) > 3:
                print(f"  ... 還有 {len(terms) - 3} 個")
            print()
        
        print("-" * 40)
        print(f"總計不同 story_id: {len(grouped_by_story)} 個")
        print(f"總計新 term 組合: {len(new_combinations)} 筆")
        
        print("\n" + "=" * width)
        print("⚠️  注意: 以上資料尚未插入資料庫，僅供預覽確認")
        print("=" * width)

    def print_final_results(self, final_results: Dict):
        """將最終結果印出到終端機"""
        width = DiffKeywordConfig.OUTPUT_CONFIG['terminal_width']
        
        print("\n" + "=" * width)
        print("  困難關鍵字提取結果")
        print("=" * width)
        
        # 印出統計摘要
        summary = final_results['summary']
        print(f"處理時間: {summary['processing_date']}")
        print(f"處理新聞數量: {summary['total_news']}")
        print(f"不重複關鍵字總數: {summary['total_unique_keywords']}")
        print(f"成功解釋詞彙數: {summary['successfully_explained_keywords']}")
        
        print("\n" + "-" * width)
        print("  各新聞困難關鍵字詳細結果")
        print("-" * width)
        
        # 印出每篇新聞的結果
        for story_id, story_data in final_results['stories'].items():
            print(f"\n📰 Story ID: {story_id}")
            print(f"標題: {story_data['title']}")
            print(f"總關鍵字數量: {story_data['keyword_count']}")
            
            # 顯示新提取和現有關鍵字的分類
            if 'new_keyword_count' in story_data and 'existing_term_count' in story_data:
                print(f"  - 新提取關鍵字: {story_data['new_keyword_count']} 個")
                print(f"  - 現有 term_map: {story_data['existing_term_count']} 個")
            
            if story_data['keywords']:
                print("困難關鍵字與解釋:")
                for idx, keyword_data in enumerate(story_data['keywords'], 1):
                    term = keyword_data.get('term', 'N/A')
                    definition = keyword_data.get('definition', '無解釋')
                    examples = keyword_data.get('examples', [])
                    source = keyword_data.get('source', '未知')  # 標記來源
                    
                    source_icon = "🆕" if source == "new" else "📋" if source == "existing" else "❓"
                    print(f"  {idx}. {source_icon} 【{term}】")
                    print(f"     定義: {definition}")
                    
                    if examples:
                        example_text = examples[0].get('text', '無範例') if examples else '無範例'
                        print(f"     應用: {example_text}")
                    print()
            else:
                print("  (無提取到困難關鍵字)")
            
            print("-" * 40)
        
        print("\n" + "=" * width)
        print("結果輸出完畢")
        print("=" * width)
        """將最終結果印出到終端機"""
        width = DiffKeywordConfig.OUTPUT_CONFIG['terminal_width']
        
        print("\n" + "=" * width)
        print("  困難關鍵字提取結果")
        print("=" * width)
        
        # 印出統計摘要
        summary = final_results['summary']
        print(f"處理時間: {summary['processing_date']}")
        print(f"處理新聞數量: {summary['total_news']}")
        print(f"不重複關鍵字總數: {summary['total_unique_keywords']}")
        print(f"成功解釋詞彙數: {summary['successfully_explained_keywords']}")
        
        print("\n" + "-" * width)
        print("  各新聞困難關鍵字詳細結果")
        print("-" * width)
        
        # 印出每篇新聞的結果
        for story_id, story_data in final_results['stories'].items():
            print(f"\n📰 Story ID: {story_id}")
            print(f"標題: {story_data['title']}")
            print(f"總關鍵字數量: {story_data['keyword_count']}")
            
            # 顯示新提取和現有關鍵字的分類
            if 'new_keyword_count' in story_data and 'existing_term_count' in story_data:
                print(f"  - 新提取關鍵字: {story_data['new_keyword_count']} 個")
                print(f"  - 現有 term_map: {story_data['existing_term_count']} 個")
            
            if story_data['keywords']:
                print("困難關鍵字與解釋:")
                for idx, keyword_data in enumerate(story_data['keywords'], 1):
                    term = keyword_data.get('term', 'N/A')
                    definition = keyword_data.get('definition', '無解釋')
                    examples = keyword_data.get('examples', [])
                    source = keyword_data.get('source', '未知')  # 標記來源
                    
                    source_icon = "🆕" if source == "new" else "📋" if source == "existing" else "❓"
                    print(f"  {idx}. {source_icon} 【{term}】")
                    print(f"     定義: {definition}")
                    
                    if examples:
                        example_text = examples[0].get('text', '無範例') if examples else '無範例'
                        print(f"     應用: {example_text}")
                    print()
            else:
                print("  (無提取到困難關鍵字)")
            
            print("-" * 40)
        
        print("\n" + "=" * width)
        print("結果輸出完畢")
        print("=" * width)

    def run(self, limit: Optional[int] = None):
        """執行完整的困難關鍵字提取流程"""
        if not self.is_ready():
            print("✗ 系統未就緒，無法執行")
            return

        print("\n" + "=" * 80)
        print("  困難關鍵字提取系統")
        print("=" * 80)

        # 1. 讀取並合併 Supabase single_news 和 term_map 資料
        news_data = self.fetch_combined_data(limit)
        if not news_data:
            print("未取得任何資料")
            return

        # 2. 提取所有關鍵字，並根據 story_id 組織
        print("\n=== 階段一：從新聞中提取困難關鍵字 ===")
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
        print(f"✓ 階段一完成：共提取 {len(unique_keywords)} 個不重複關鍵字。")
        
        # 印出進度摘要
        self.print_progress_summary(story_keywords, all_keywords)

        # 3. 為關鍵字生成解釋
        print("\n=== 階段二：為關鍵字生成解釋與範例 ===")
        word_explanations = {}
        for word in tqdm(unique_keywords, desc="生成詞彙解釋"):
            explanation = self.get_word_explanation(word)
            if explanation and "term" in explanation:
                word_explanations[word] = explanation
            else:
                print(f"⚠ 未能成功解釋詞彙：'{word}'")
        
        print(f"✓ 階段二完成：共成功解釋 {len(word_explanations)} 個詞彙。")

        # 4. 整理並儲存最終結果
        print("\n=== 階段三：整理最終結果 ===")
        final_results = {
            "summary": {
                "total_news": len(story_keywords),
                "total_unique_keywords": len(unique_keywords),
                "successfully_explained_keywords": len(word_explanations),
                "processing_date": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "stories": {},
            "word_explanations": word_explanations
        }
        
        # 將解釋加入到每個 story 的關鍵字中
        for story_id, story_data in story_keywords.items():
            keywords_with_explanations = []
            new_keywords = story_data.get("new_keywords", [])
            existing_terms = story_data.get("existing_terms", [])
            
            # 處理新提取的關鍵字
            for word in new_keywords:
                if word in word_explanations:
                    explanation = word_explanations[word].copy()
                    explanation['source'] = 'new'
                    keywords_with_explanations.append(explanation)
            
            # 處理現有的 terms
            for word in existing_terms:
                if word in word_explanations:
                    explanation = word_explanations[word].copy()
                    explanation['source'] = 'existing'
                    keywords_with_explanations.append(explanation)
            
            final_results["stories"][story_id] = {
                "title": story_data["title"],
                "keywords": keywords_with_explanations,
                "keyword_count": len(keywords_with_explanations),
                "new_keyword_count": len([k for k in keywords_with_explanations if k.get('source') == 'new']),
                "existing_term_count": len([k for k in keywords_with_explanations if k.get('source') == 'existing'])
            }

        # 5. 檢查並預覽準備插入 term_map 的資料
        new_combinations = self.check_existing_term_combinations(story_keywords)
        self.display_insertion_preview(new_combinations)

        # 6. 檢查並預覽準備插入 term 表的資料
        new_terms = self.check_existing_terms(word_explanations)
        self.display_term_insertion_preview(new_terms)

        # 7. 印出結果到終端機
        self.print_final_results(final_results)

        print("\n✓ 處理完成！")
        print(f"- 處理新聞數量: {final_results['summary']['total_news']}")
        print(f"- 不重複關鍵字: {final_results['summary']['total_unique_keywords']}")
        print(f"- 成功解釋詞彙: {final_results['summary']['successfully_explained_keywords']}")
        
        if new_combinations:
            print(f"- 準備插入 term_map: {len(new_combinations)} 筆新組合")
        if new_terms:
            print(f"- 準備插入 term: {len(new_terms)} 個新關鍵字")


def main():
    """主程式入口"""
    print("=" * 80)
    print("  困難關鍵字提取系統 - 基於 Supabase single_news")
    print("=" * 80)
    
    # 解析指令列參數
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"✓ 設定讀取限制: {limit} 筆")
        except ValueError:
            print("⚠ 無效的 limit 參數，將讀取所有資料")
            limit = None
    
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


# 在 DiffKeywordProcessor 類中添加插入方法（需要手動移動到類內）
def insert_term_map_data(self, new_combinations: List[Dict[str, str]]) -> bool:
    """將新的 term_map 組合插入資料庫"""
    if not new_combinations:
        print("沒有 term_map 資料需要插入")
        return True
    
    print(f"\n=== 開始插入 term_map 資料 ===")
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
    
    print(f"\nterm_map 插入結果:")
    print(f"  成功: {success_count} 筆")
    print(f"  失敗: {error_count} 筆")
    
    return error_count == 0

def insert_term_data(self, new_terms: List[Dict[str, str]]) -> bool:
    """將新的關鍵字定義插入 term 表"""
    if not new_terms:
        print("沒有 term 資料需要插入")
        return True
    
    print(f"\n=== 開始插入 term 資料 ===")
    print(f"準備插入 {len(new_terms)} 筆資料到 {self.db_config['term_table']} 表")
    
    success_count = 0
    error_count = 0
    
    try:
        table_name = self.db_config['term_table']
        
        # 批次插入
        batch_size = 50  # term 表資料較大，每批插入50筆
        for i in range(0, len(new_terms), batch_size):
            batch = new_terms[i:i + batch_size]
            
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
        print(f"✗ 插入 term 時發生錯誤: {e}")
        return False
    
    print(f"\nterm 插入結果:")
    print(f"  成功: {success_count} 筆")
    print(f"  失敗: {error_count} 筆")
    
    return error_count == 0


if __name__ == "__main__":
    main()
