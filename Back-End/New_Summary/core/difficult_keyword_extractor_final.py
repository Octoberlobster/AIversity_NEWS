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
import logging
from typing import List, Dict, Any, Set, Optional
from dotenv import load_dotenv
from tqdm import tqdm
import google.generativeai as genai

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
            logger.info(f"✓ Gemini API ({self.api_config['model_name']}) 初始化成功")
        except Exception as e:
            logger.error(f"✗ 初始化 Gemini 時發生錯誤: {e}")
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
            logger.info(f"✓ Supabase 連線 ({supabase_url}) 初始化成功")
        except Exception as e:
            logger.error(f"✗ 初始化 Supabase 時發生錯誤: {e}")
            logger.error("請確認已安裝 supabase-py：pip install supabase-py postgrest-py")
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
                logger.warning(f"✗ JSON 解析錯誤 (嘗試 {attempt + 1}/{self.api_config['max_retries']}): {e}")
                if attempt == self.api_config['max_retries'] - 1:
                    logger.error(f"原始回覆: {response.text}")
                    return {}
            except Exception as e:
                logger.warning(f"✗ API 呼叫時發生錯誤 (嘗試 {attempt + 1}/{self.api_config['max_retries']}): {e}")
                if attempt == self.api_config['max_retries'] - 1:
                    return {}
                time.sleep(2)  # 重試前等待
        return {}

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
            table_name = self.db_config['term_map_table']
            fields = ','.join(self.db_config['term_map_fields'])
            
            query = self.supabase_client.table(table_name).select(fields)
            resp = query.execute()
            
            if getattr(resp, 'error', None):
                logger.error(f"讀取 {table_name} 失敗: {resp.error}")
                term_map = {}
            else:
                rows = resp.data or []
                logger.info(f"成功讀取 {len(rows)} 筆 term_map 資料")
                
                # 組織成 story_id -> terms 的字典
                term_map = {}
                for row in rows:
                    story_id = row.get('story_id')
                    term = row.get('term')
                    
                    if story_id and term:
                        if story_id not in term_map:
                            term_map[story_id] = []
                        term_map[story_id].append(term)
                
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

    def insert_term_map_data(self, new_combinations: List[Dict[str, str]]) -> bool:
        """將新的 term_map 組合插入資料庫"""
        if not new_combinations:
            logger.info("沒有 term_map 資料需要插入")
            return True
        
        logger.info("=== 開始插入 term_map 資料 ===")
        logger.info(f"準備插入 {len(new_combinations)} 筆資料到 {self.db_config['term_map_table']} 表")
        
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
                        logger.error(f"批次 {i//batch_size + 1} 插入失敗: {resp.error}")
                        error_count += len(batch)
                    else:
                        batch_success = len(batch)
                        success_count += batch_success
                        logger.info(f"✓ 批次 {i//batch_size + 1}: 成功插入 {batch_success} 筆")
                
                except Exception as e:
                    logger.error(f"✗ 批次 {i//batch_size + 1} 發生錯誤: {e}")
                    error_count += len(batch)
        
        except Exception as e:
            logger.error(f"✗ 插入 term_map 時發生錯誤: {e}")
            return False
        
        logger.info("term_map 插入結果:")
        logger.info(f"  成功: {success_count} 筆")
        logger.info(f"  失敗: {error_count} 筆")
        
        return error_count == 0

    def insert_term_data(self, new_terms: List[Dict[str, str]]) -> bool:
        """將新的關鍵字定義插入 term 表"""
        if not new_terms:
            logger.info("沒有 term 資料需要插入")
            return True
        
        logger.info("=== 開始插入 term 資料 ===")
        logger.info(f"準備插入 {len(new_terms)} 筆資料到 {self.db_config['term_table']} 表")
        
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
                        logger.error(f"批次 {i//batch_size + 1} 插入失敗: {resp.error}")
                        error_count += len(batch)
                    else:
                        batch_success = len(batch)
                        success_count += batch_success
                        logger.info(f"✓ 批次 {i//batch_size + 1}: 成功插入 {batch_success} 筆")
                
                except Exception as e:
                    logger.error(f"✗ 批次 {i//batch_size + 1} 發生錯誤: {e}")
                    error_count += len(batch)
        
        except Exception as e:
            logger.error(f"✗ 插入 term 時發生錯誤: {e}")
            return False
        
        logger.info("term 插入結果:")
        logger.info(f"  成功: {success_count} 筆")
        logger.info(f"  失敗: {error_count} 筆")
        
        return error_count == 0

    def check_existing_term_combinations(self, story_keywords: Dict) -> List[Dict[str, str]]:
        """檢查並準備需要插入到 term_map 的新組合"""
        logger.info("=== 檢查 term_map 重複性 ===")
        
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
        
        for story_id, story_data in story_keywords.items():
            new_keywords = story_data.get("new_keywords", [])
            
            for keyword in new_keywords:
                combination = (story_id, keyword)
                if combination not in existing_combinations:
                    new_combinations.append({
                        'story_id': story_id,
                        'term': keyword
                    })
        
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
        new_combinations = self.check_existing_term_combinations(story_keywords)
        new_terms = self.check_existing_terms(word_explanations)
        
        # 5. 執行資料庫插入
        logger.info("=== 階段四：執行資料庫插入 ===")
        
        # 先插入 term 表（關鍵字定義）
        term_success = self.insert_term_data(new_terms)
        
        # 再插入 term_map 表（story_id 和 term 的關聯）
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


if __name__ == "__main__":
    main()