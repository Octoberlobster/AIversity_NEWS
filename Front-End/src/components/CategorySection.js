import React, { useState, useEffect, useCallback } from 'react';
import './../css/UnifiedNewsCard.css';
import UnifiedNewsCard from './UnifiedNewsCard';
import { useSupabase } from './supabase';
import { imageCache } from './utils/cache';

// 分類配置
const categories = {
  '政治': { id: 'Politics', name: '政治', color: '#ef4444' },
  '台灣': { id: 'Taiwan News', name: '台灣', color: '#10b981' },
  '科學與科技': { id: 'Science & Technology', name: '科學與科技', color: '#8b5cf6' },
  '國際': { id: 'International News', name: '國際', color: '#f59e0b' },
  '生活': { id: 'Lifestyle & Consumer', name: '生活', color: '#06b6d4' },
  '體育': { id: 'Sports', name: '體育', color: '#059669' },
  '娛樂': { id: 'Entertainment', name: '娛樂', color: '#ec4899' },
  '商業財經': { id: 'Business & Finance', name: '商業財經', color: '#10b981' },
  '健康': { id: 'Health & Wellness', name: '健康', color: '#ef4444' }
};

function CategorySection({ category }) {
  const [newsData, setNewsData] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState(null);
  const supabaseClient = useSupabase();
  
  const currentCategory = categories[category];
  const ITEMS_PER_PAGE = 18;

  // 載入圖片的共用函數
  const loadImagesForNews = useCallback(async (newsArray) => {
    if (!newsArray || newsArray.length === 0) return [];

    const storyIds = newsArray.map(news => news.story_id);
    console.log(`Loading images for ${storyIds.length} stories`);
    
    // 檢查快取
    const uncachedStoryIds = [];
    const cachedImages = {};
    storyIds.forEach(storyId => {
      const cached = imageCache.get(`image_${storyId}`);
      if (cached) {
        cachedImages[storyId] = cached;
      } else {
        uncachedStoryIds.push(storyId);
      }
    });

    // 查詢未快取的圖片
    let imageMap = { ...cachedImages };
    if (uncachedStoryIds.length > 0) {
      try {
        const { data: imagesData, error: imagesError } = await supabaseClient
          .from('generated_image')
          .select('story_id, image')
          .in('story_id', uncachedStoryIds);

        if (!imagesError && imagesData) {
          imagesData.forEach(imageItem => {
            if (imageItem.image) {
              const cleanBase64 = imageItem.image.replace(/\s/g, '');
              const imageUrl = `data:image/png;base64,${cleanBase64}`;
              
              imageMap[imageItem.story_id] = imageUrl;
              imageCache.set(`image_${imageItem.story_id}`, imageUrl);
            }
          });
        }
      } catch (error) {
        console.error('Error loading images:', error);
      }
    }

    // 組合新聞資料與圖片
    return newsArray.map(news => ({
      ...news,
      title: news.news_title,
      shortSummary: news.ultra_short,
      date: new Date(news.generated_date).toLocaleDateString("zh-TW"),
      imageUrl: imageMap[news.story_id] || "/api/placeholder/300/200"
    }));
  }, [supabaseClient]);

  // 載入第一頁新聞
  const loadInitialNews = useCallback(async () => {
    if (!currentCategory || !supabaseClient) return;

    try {
      setLoading(true);
      setError(null);

      console.log('Loading initial news for category:', currentCategory.id);

      // 查詢第一頁新聞
      const { data: newsData, error: newsError } = await supabaseClient
        .from('single_news')
        .select('story_id, news_title, ultra_short, generated_date, category')
        .eq('category', currentCategory.id)
        .order('generated_date', { ascending: false })
        .limit(ITEMS_PER_PAGE);

      if (newsError) {
        console.error('Error fetching news:', newsError);
        setError('無法載入新聞資料');
        return;
      }

      if (!newsData || newsData.length === 0) {
        console.log('No news found for category:', currentCategory.id);
        setNewsData([]);
        setHasMore(false);
        return;
      }

      // 載入這一頁的圖片
      const enhancedData = await loadImagesForNews(newsData);
      
      setNewsData(enhancedData);
      setCurrentPage(1);
      setHasMore(newsData.length === ITEMS_PER_PAGE);
      
    } catch (err) {
      console.error('Error in loadInitialNews:', err);
      setError('載入新聞時發生錯誤');
    } finally {
      setLoading(false);
    }
  }, [currentCategory, supabaseClient, loadImagesForNews]);

  // 載入更多新聞
  const loadMoreNews = useCallback(async () => {
    if (!currentCategory || !supabaseClient || isLoadingMore || !hasMore) return;

    try {
      setIsLoadingMore(true);
      
      const nextPage = currentPage + 1;
      const offset = (nextPage - 1) * ITEMS_PER_PAGE;

      console.log(`Loading page ${nextPage} for category:`, currentCategory.id);

      // 查詢下一頁新聞
      const { data: newNewsData, error: newsError } = await supabaseClient
        .from('single_news')
        .select('story_id, news_title, ultra_short, generated_date, category')
        .eq('category', currentCategory.id)
        .order('generated_date', { ascending: false })
        .range(offset, offset + ITEMS_PER_PAGE - 1);

      if (newsError) {
        console.error('Error fetching more news:', newsError);
        return;
      }

      if (!newNewsData || newNewsData.length === 0) {
        setHasMore(false);
        return;
      }

      // 載入這一頁的圖片
      const enhancedNewData = await loadImagesForNews(newNewsData);
      
      // 合併到現有資料
      setNewsData(prevData => [...prevData, ...enhancedNewData]);
      setCurrentPage(nextPage);
      setHasMore(newNewsData.length === ITEMS_PER_PAGE);

    } catch (err) {
      console.error('Error in loadMoreNews:', err);
    } finally {
      setIsLoadingMore(false);
    }
  }, [currentCategory, supabaseClient, isLoadingMore, hasMore, currentPage, loadImagesForNews]);

  // 初始載入效果
  useEffect(() => {
    loadInitialNews();
  }, [loadInitialNews]);

  if (!currentCategory) {
    return (
      <section className="catSec">
        <div className="catSec__header">
          <h2 className="catSec__title">分類新聞</h2>
        </div>
        <div className="catSec__empty">找不到該分類的新聞</div>
      </section>
    );
  }

  if (loading) {
    return (
      <section className="catSec">
        <div className="catSec__header">
          <h2 className="catSec__title">{category}新聞</h2>
        </div>
        <div className="catSec__loading">載入中...</div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="catSec">
        <div className="catSec__header">
          <h2 className="catSec__title">{category}新聞</h2>
        </div>
        <div className="catSec__error">{error}</div>
      </section>
    );
  }

  // 資料已經在 fetchCategoryNews 中處理完成，包含圖片
  console.log('Final news data for UnifiedNewsCard:', newsData);

  return (
    <section className="catSec">
      <div className="catSec__header">
        <h2 className="catSec__title">
          {category}新聞
        </h2>
      </div>

      {newsData.length === 0 ? (
        <div className="catSec__empty">目前沒有 {category} 相關的新聞</div>
      ) : (
        <div className="catSec__content">
          <UnifiedNewsCard 
            customData={newsData}
            limit={newsData.length} 
          />
        </div>
      )}
    </section>
  );
}

export default CategorySection;