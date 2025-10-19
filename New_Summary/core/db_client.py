"""
Supabase 資料庫客戶端 - 用於從 stories 和 cleaned_news 表拉取並組合資料
"""

import os
import logging
from typing import Dict, List, Optional, Any, Set
from supabase import create_client, Client
from datetime import datetime

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
        
        # 用來追蹤本次執行中有摘要更新的 story_ids
        self.updated_story_ids: Set[str] = set()
    
    def get_stories_with_articles(self, filter_processed: bool = True) -> List[Dict[str, Any]]:
        """
        從 Supabase 拉取 stories 和對應的 cleaned_news 資料，組合成類似原 JSON 格式
        
        Args:
            filter_processed: 是否篩選掉已處理且無變化的資料
        
        Returns:
            組合後的資料列表，格式類似原 JSON
        """
        try:
            # 1. 拉取所有 stories
            stories_response = self.client.table('stories').select('*').range(0, 1000).execute()
            stories = stories_response.data
            
            logger.info(f"從 stories 表拉取到 {len(stories)} 筆資料")
            
            # 2. 如果需要篩選，先拉取現有的 single_news 記錄
            existing_single_news = {}
            if filter_processed:
                single_news_response = self.client.table('single_news').select('story_id, total_articles').execute()
                existing_single_news = {
                    item['story_id']: item['total_articles'] 
                    for item in single_news_response.data
                }
                logger.info(f"從 single_news 表拉取到 {len(existing_single_news)} 筆現有記錄")
            
            result = []
            
            for idx, story in enumerate(stories, 1):
                story_id = story.get('story_id')
                
                # 2. 根據 story_id 拉取對應的 cleaned_news
                articles_response = self.client.table('cleaned_news').select('*').eq('story_id', story_id).execute()
                articles = articles_response.data
                
                current_article_count = len(articles)
                logger.info(f"Story {story_id} 對應到 {current_article_count} 篇文章")
                
                # 3. 判斷是否需要處理此 story
                should_process = True
                if filter_processed:
                    if story_id in existing_single_news:
                        # 已存在記錄，檢查 total_articles 是否有變化
                        existing_count = existing_single_news[story_id]
                        if existing_count == current_article_count:
                            should_process = False
                            logger.info(f"跳過 Story {story_id} - 文章數無變化 ({existing_count})")
                        else:
                            logger.info(f"需要更新 Story {story_id} - 文章數變化 {existing_count} -> {current_article_count}")
                    else:
                        logger.info(f"新的 Story {story_id} - 需要生成摘要")
                
                if not should_process:
                    continue
                
                # 4. 組合成類似原 JSON 的格式
                story_data = {
                    "story_index": len(result) + 1,  # 使用實際要處理的順序
                    "story_id": story_id,
                    "story_title": story.get('story_title', ''),
                    "story_url": story.get('story_url', ''),
                    "category": story.get('category', ''),
                    "crawl_date": story.get('crawl_date', ''),
                    "articles": []
                }
                
                # 5. 處理每篇文章
                for article_idx, article in enumerate(articles, 1):
                    article_data = {
                        "id": article.get('article_id'),
                        "article_index": article_idx,
                        "article_title": article.get('article_title', ''),
                        "article_url": article.get('article_url', ''),
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
                # 記錄此 story_id 已更新，需要重新生成 terms
                self.updated_story_ids.add(story_id)
            else:
                # 插入新記錄
                response = self.client.table('single_news').insert(insert_data).execute()
                logger.info(f"插入新的 single_news 記錄: {story_id}")
                # 記錄此 story_id 為新的，需要生成 terms
                self.updated_story_ids.add(story_id)
            
            return True
            
        except Exception as e:
            logger.error(f"儲存到 single_news 時發生錯誤: {str(e)}")
            return False
    
    def get_updated_story_ids(self) -> Set[str]:
        """
        獲取本次執行中有摘要更新的 story_ids
        
        Returns:
            需要重新生成 terms 的 story_ids 集合
        """
        return self.updated_story_ids.copy()
    
    def clear_updated_story_ids(self):
        """清空已更新的 story_ids 記錄"""
        self.updated_story_ids.clear()
    
    def test_connection(self) -> bool:
        """測試資料庫連線"""
        try:
            # 簡單查詢測試連線
            response = self.client.table('stories').select('story_id').limit(1).execute()
            logger.info("Supabase 連線測試成功")
            return True
        except Exception as e:
            logger.error(f"Supabase 連線測試失敗: {str(e)}")
            return False
    
