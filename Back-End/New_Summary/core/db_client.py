"""
Supabase 資料庫客戶端 - 用於從 stories 和 cleaned_news 表拉取並組合資料
"""

import os
import logging
from typing import Dict, List, Optional, Any
from supabase import create_client, Client
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('outputs/logs/db_client.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Supabase 資料庫客戶端"""
    
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """
        初始化 Supabase 客戶端
        
        Args:
            url: Supabase URL
            key: Supabase API Key
        """
        self.url = url or os.getenv('SUPABASE_URL')
        self.key = key or os.getenv('SUPABASE_KEY')
        
        if not self.url or not self.key:
            raise ValueError("請設定 SUPABASE_URL 和 SUPABASE_KEY 環境變數")
        
        self.client: Client = create_client(self.url, self.key)
    
    def get_stories_with_articles(self) -> List[Dict[str, Any]]:
        """
        從 Supabase 拉取 stories 和對應的 cleaned_news 資料，組合成類似原 JSON 格式
        
        Returns:
            組合後的資料列表，格式類似原 JSON
        """
        try:
            # 1. 拉取所有 stories
            stories_response = self.client.table('stories').select('*').execute()
            stories = stories_response.data
            
            logger.info(f"從 stories 表拉取到 {len(stories)} 筆資料")
            
            result = []
            
            for idx, story in enumerate(stories, 1):
                story_id = story.get('story_id')
                
                # 2. 根據 story_id 拉取對應的 cleaned_news
                articles_response = self.client.table('cleaned_news').select('*').eq('story_id', story_id).execute()
                articles = articles_response.data
                
                logger.info(f"Story {story_id} 對應到 {len(articles)} 篇文章")
                
                # 3. 組合成類似原 JSON 的格式
                story_data = {
                    "story_id": story_id,  # 新增，原 JSON 沒有但資料庫有
                    "story_url": story.get('story_url', ''),  # 新增，原 JSON 沒有但資料庫有
                    "category": story.get('category', ''),
                    "crawl_date": story.get('crawl_date', ''),  # 新增，原 JSON 沒有但資料庫有
                    "articles": []
                }
                
                # 4. 處理每篇文章
                for article_idx, article in enumerate(articles, 1):
                    article_data = {
                        "id": article.get('article_id'),
                        "article_title": article.get('article_title', ''),
                        "article_url": article.get('article_url', ''),  # 從 cleaned_news 來，原 JSON 是 google_news_url
                        "content": article.get('content', ''),
                        "media": article.get('media', ''),
                    }
                    
                    story_data["articles"].append(article_data)
                
                if story_data["articles"]:  # 只加入有文章的 story
                    result.append(story_data)
            
            logger.info(f"成功組合 {len(result)} 個 stories 資料")
            return result
            
        except Exception as e:
            logger.error(f"拉取資料時發生錯誤: {str(e)}")
            raise
    
    def save_to_single_news(self, story_id: str, processed_data: Dict[str, Any]) -> bool:
        """
        將處理後的摘要資料儲存到 single_news 表
        
        Args:
            story_id: Story ID
            processed_data: 處理後的資料
            
        Returns:
            是否成功儲存
        """
        try:
            # 準備要插入的資料
            insert_data = {
                'story_id': story_id,
                'category': processed_data.get('category', ''),
                'total_articles': processed_data.get('total_articles', 0),
                'news_title': processed_data.get('news_title', ''),
                'ultra_short': processed_data.get('ultra_short', ''),
                'short': processed_data.get('short', ''),
                'long': processed_data.get('long', ''),
                'generated_date': processed_data.get('processed_at', '') or str(datetime.now().isoformat(sep=' ', timespec='minutes'))
            }
            
            # 檢查是否已存在
            existing = self.client.table('single_news').select('story_id').eq('story_id', story_id).execute()
            
            if existing.data:
                # 更新現有記錄
                response = self.client.table('single_news').update(insert_data).eq('story_id', story_id).execute()
                logger.info(f"更新 single_news 記錄: {story_id}")
            else:
                # 插入新記錄
                response = self.client.table('single_news').insert(insert_data).execute()
                logger.info(f"插入新的 single_news 記錄: {story_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"儲存到 single_news 時發生錯誤: {str(e)}")
            return False
