"""
新聞處理模組 - 用於處理 cleaned_final_news.json 中的 stories
功能：迭代每個 story，對其中的 articles 進行摘要和關鍵詞萃取
"""

import json
import google.generativeai as genai
import time
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging
from core.config import NewsProcessorConfig

# 設置日誌
try:
    os.makedirs(NewsProcessorConfig.LOG_DIR, exist_ok=True)
except Exception:
    pass
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(NewsProcessorConfig.LOG_DIR, 'news_processing.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NewsProcessor:
    """新聞處理器 - 負責處理新聞數據的摘要和關鍵詞萃取"""
    
    def __init__(self, api_key: str, model_name: Optional[str] = None):
        """
        初始化新聞處理器
        
        Args:
            api_key: Gemini API 金鑰
            model_name: 使用的 Gemini 模型名稱
        """
        # 配置 Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name or NewsProcessorConfig.GEMINI_MODEL)
        # 參數來源於 Config
        self.generation_configs = NewsProcessorConfig.GENERATION_CONFIGS
        self.safety_settings = NewsProcessorConfig.SAFETY_SETTINGS
    
    def create_article_summary_prompt(self, article: Dict, summary_type: str = "analysis") -> str:
        """
        創建單篇文章摘要的 prompt
        
        Args:
            article: 文章數據
            summary_type: 摘要類型 ("short", "medium", "long", "analysis")
        
        Returns:
            格式化的 prompt 字串
        """
        
        max_chars = NewsProcessorConfig.MAX_CONTENT_LENGTH
        base_prompt = f"""
            你是專業的新聞編輯，請分析以下新聞文章並提取關鍵資訊。

            【新聞資料】
            標題：{article.get('article_title', '無標題')}
            發布時間：{article.get('publish_date') or article.get('crawl_date', '未知時間')}
            內容：{article.get('content', '無內容')[:max_chars]}  # 限制長度避免超過 token 限制

            【任務要求】
            請提取以下資訊並以 JSON 格式輸出：

            1. 核心摘要（2-3句話概括主要事件）
            2. 關鍵詞列表（5-8個最重要的關鍵詞）
            3. 重要人物（提及的重要人物姓名）
            4. 重要機構組織（提及的公司、政府部門、學術機構等）
            5. 地點資訊（涉及的地理位置）
            6. 時間線（重要的時間點）
            7. 事件分類（政治、經濟、科技、社會等）

            【輸出格式】
            請嚴格按照以下 JSON 格式輸出，不要包含其他文字：

            {{
                "core_summary": "核心摘要內容",
                "keywords": ["關鍵詞1", "關鍵詞2", "關鍵詞3"],
                "key_persons": ["人物1", "人物2"],
                "key_organizations": ["組織1", "組織2"],
                "locations": ["地點1", "地點2"],
                "timeline": ["時間點1", "時間點2"],
                "category": "事件分類",
                "confidence_score": 0.95
            }}
            """
        return base_prompt
    
    def process_single_article(self, article: Dict) -> Optional[Dict]:
        """
        處理單篇文章
        
        Args:
            article: 文章數據字典
            
        Returns:
            處理結果字典，包含摘要和關鍵資訊
        """
        try:
            # 檢查文章內容
            if not article.get('content') or len(article['content'].strip()) < 50:
                logger.warning(f"文章 {article.get('id', 'unknown')} 內容太短或為空")
                return None
            
            # 創建 prompt
            prompt = self.create_article_summary_prompt(article)
            
            # 調用 Gemini API
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(**self.generation_configs["analysis"]),
                safety_settings=self.safety_settings
            )
            
            # 解析回應
            if response.text:
                try:
                    # 清理回應文字，移除可能的 markdown 格式
                    clean_text = response.text.strip()
                    
                    # 如果被 ```json 包圍，則提取內容
                    if clean_text.startswith('```json'):
                        # 找到第一個 { 和最後一個 }
                        start_idx = clean_text.find('{')
                        end_idx = clean_text.rfind('}') + 1
                        if start_idx != -1 and end_idx != 0:
                            clean_text = clean_text[start_idx:end_idx]
                    elif clean_text.startswith('```'):
                        # 處理一般的 ``` 包圍
                        lines = clean_text.split('\n')
                        # 移除第一行的 ``` 和最後一行的 ```
                        if len(lines) > 2:
                            clean_text = '\n'.join(lines[1:-1])
                    
                    # 嘗試解析 JSON
                    result = json.loads(clean_text)
                    
                    # 添加原始文章資訊
                    result.update({
                        "original_article_id": article.get('id'),
                        "original_title": article.get('article_title'),
                        "publish_date": article.get('publish_date') or article.get('crawl_date'),
                        "source_url": article.get('final_url'),
                        "processed_at": datetime.now().isoformat()
                    })
                    
                    logger.info(f"成功處理文章: {article.get('article_title', '')[:50]}...")
                    return result
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON 解析失敗: {e}")
                    logger.error(f"清理後的文字: {clean_text[:200]}...")
                    logger.error(f"原始回應: {response.text[:200]}...")
                    return None
            else:
                logger.error("Gemini API 回應為空")
                return None
                
        except Exception as e:
            logger.error(f"處理文章時發生錯誤: {e}")
            return None
    
    def process_story_articles(self, story: Dict) -> Dict:
        """
        處理單個 story 中的所有 articles
        
        Args:
            story: story 數據字典
            
        Returns:
            處理結果字典
        """
        story_id = story.get('story_index', 'unknown')
        logger.info(f"開始處理 Story {story_id}: {story.get('story_title', '')}")
        
        articles = story.get('articles', [])
        processed_articles = []
        failed_articles = []
        
        for i, article in enumerate(articles):
            logger.info(f"處理 Story {story_id} 的第 {i+1}/{len(articles)} 篇文章...")
            
            # 處理單篇文章
            result = self.process_single_article(article)
            
            if result:
                processed_articles.append(result)
            else:
                failed_articles.append({
                    "article_id": article.get('id'),
                    "article_title": article.get('article_title'),
                    "reason": "處理失敗"
                })
            
            # 添加延遲避免 API 速率限制
            time.sleep(NewsProcessorConfig.API_DELAY)
        
        # 組織結果
        story_result = {
            "story_index": story_id,
            "story_title": story.get('story_title'),
            "category": story.get('category'),
            "total_articles": len(articles),
            "processed_articles": len(processed_articles),
            "failed_articles": len(failed_articles),
            "articles_analysis": processed_articles,
            "failed_list": failed_articles,
            "processed_at": datetime.now().isoformat()
        }
        
        logger.info(f"Story {story_id} 處理完成: 成功 {len(processed_articles)}/{len(articles)} 篇")
        
        return story_result
    
    def load_news_data(self, file_path: str) -> List[Dict]:
        """
        載入新聞數據檔案
        
        Args:
            file_path: JSON 檔案路徑
            
        Returns:
            stories 列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"成功載入 {len(data)} 個 stories")
            return data
            
        except Exception as e:
            logger.error(f"載入檔案失敗: {e}")
            return []
    
    def save_processed_data(self, data: List[Dict], output_path: str):
        """
        保存處理結果
        
        Args:
            data: 處理結果列表
            output_path: 輸出檔案路徑
        """
        try:
            # 確保輸出目錄存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"處理結果已保存至: {output_path}")
            
        except Exception as e:
            logger.error(f"保存檔案失敗: {e}")
    
    def process_all_stories(self, input_file: str, output_file: str, start_index: int = 0, max_stories: Optional[int] = None):
        """
        處理所有 stories
        
        Args:
            input_file: 輸入檔案路徑
            output_file: 輸出檔案路徑  
            start_index: 開始處理的 story 索引
            max_stories: 最大處理數量（用於測試）
        """
        logger.info("=== 開始新聞處理流程 ===")
        
        # 載入數據
        # 若未指定，使用 config 預設路徑
        input_file = input_file or NewsProcessorConfig.INPUT_FILE
        stories = self.load_news_data(input_file)
        if not stories:
            logger.error("無法載入新聞數據")
            return
        
        # 確定處理範圍
        end_index = len(stories)
        if max_stories:
            end_index = min(start_index + max_stories, len(stories))
        
        logger.info(f"將處理 stories {start_index} 到 {end_index-1} (共 {end_index-start_index} 個)")
        
        # 處理每個 story
        processed_stories = []
        
        for i in range(start_index, end_index):
            story = stories[i]
            
            try:
                logger.info(f"\n=== 處理進度: {i+1-start_index}/{end_index-start_index} ===")
                result = self.process_story_articles(story)
                processed_stories.append(result)
                
                # 定期保存進度
                if (i - start_index + 1) % 5 == 0:
                    temp_output = output_file.replace('.json', f'_progress_{i+1}.json')
                    self.save_processed_data(processed_stories, temp_output)
                    logger.info(f"進度已保存: {temp_output}")
                
            except Exception as e:
                logger.error(f"處理 Story {i} 時發生嚴重錯誤: {e}")
                continue
        
        # 保存最終結果
        # 若未指定，使用 config 預設輸出檔名
        output_file = output_file or NewsProcessorConfig.get_output_filename(prefix="processed_articles")
        self.save_processed_data(processed_stories, output_file)
        
        # 生成處理報告
        self.generate_processing_report(processed_stories, output_file.replace('.json', '_report.txt'))
        
        logger.info("=== 新聞處理流程完成 ===")
    
    def generate_processing_report(self, processed_data: List[Dict], report_path: str):
        """
        生成處理報告
        
        Args:
            processed_data: 處理結果數據
            report_path: 報告檔案路徑
        """
        total_stories = len(processed_data)
        total_articles = sum(story.get('total_articles', 0) for story in processed_data)
        successful_articles = sum(story.get('processed_articles', 0) for story in processed_data)
        
        report = f"""
新聞處理報告
====================
處理時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

統計資訊:
- 處理 Stories 總數: {total_stories}
- 文章總數: {total_articles}
- 成功處理文章數: {successful_articles}
- 成功率: {successful_articles/total_articles*100:.1f}%

各 Story 處理詳情:
"""
        
        for story in processed_data:
            report += f"\nStory {story.get('story_index')}: {story.get('story_title')}"
            report += f"\n  - 文章數: {story.get('total_articles')}"
            report += f"\n  - 成功: {story.get('processed_articles')}"
            report += f"\n  - 失敗: {story.get('failed_articles')}"
        
        try:
            # 確保報告目錄存在
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"處理報告已生成: {report_path}")
        except Exception as e:
            logger.error(f"生成報告失敗: {e}")


def main():
    """主函數 - 簡易測試，讀取 Config"""
    api_key = NewsProcessorConfig.get_gemini_api_key()
    processor = NewsProcessor(api_key=api_key, model_name=NewsProcessorConfig.GEMINI_MODEL)
    processor.process_all_stories(
        input_file=NewsProcessorConfig.INPUT_FILE,
        output_file=NewsProcessorConfig.get_output_filename(prefix="processed_articles"),
        start_index=0,
        max_stories=2
    )


if __name__ == "__main__":
    main()
