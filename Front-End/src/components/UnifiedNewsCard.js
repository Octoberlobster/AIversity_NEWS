import React, { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import "./../css/UnifiedNewsCard.css";
import { useSupabase } from "./supabase";
import { newsCache, imageCache } from "./utils/cache";

function UnifiedNewsCard({ limit, keyword, customData, onNewsCountUpdate }) {
  const [newsData, setNewsData] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const supabaseClient = useSupabase();
  
  const ITEMS_PER_PAGE = 18;

  const loadInitialData = useCallback(async () => {
    setIsLoading(true);
    try {
      let data;
      
      if (customData) {
        data = customData;
      } else {
        // 檢查快取
        const cacheKey = `news_initial_${ITEMS_PER_PAGE}`;
        const cachedData = newsCache.get(cacheKey);
        
        if (cachedData) {
          setNewsData(cachedData);
          setCurrentPage(1);
          setHasMore(cachedData.length === ITEMS_PER_PAGE);
          setIsLoading(false);
          return;
        }

        const { data: fetchedData, error } = await supabaseClient
          .from("single_news")
          .select("story_id, news_title, ultra_short, generated_date")
          .order("generated_date", { ascending: false })
          .limit(ITEMS_PER_PAGE);

        if (error) {
          console.error("Error fetching news:", error);
          setIsLoading(false);
          return;
        }
        data = fetchedData;
      }

      // 批量獲取所有新聞的圖片 - 優化性能
      const storyIds = data.map(news => news.story_id);
      
      // 檢查圖片快取
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

      // 只查詢未快取的圖片
      let imageMap = { ...cachedImages };
      if (uncachedStoryIds.length > 0) {
        const { data: imagesData, error: imagesError } = await supabaseClient
          .from('generated_image')
          .select('story_id, image')
          .in('story_id', uncachedStoryIds);

        if (!imagesError && imagesData) {
          imagesData.forEach(imageItem => {
            if (!imageMap[imageItem.story_id] && imageItem.image) {
              // 清理 base64 字串，移除可能的換行符和空白字符
              const cleanBase64 = imageItem.image.replace(/\s/g, '');
              // 將純 base64 字串轉換為完整的 data URL
              const imageUrl = `data:image/png;base64,${cleanBase64}`;
              
              imageMap[imageItem.story_id] = imageUrl;
              // 快取圖片
              imageCache.set(`image_${imageItem.story_id}`, imageUrl);
            }
          });
        }
      }

      // 組合新聞資料與圖片
      const enhancedData = data.map(news => ({
        ...news,
        title: news.news_title || news.title,
        shortSummary: news.ultra_short || news.shortSummary,
        date: news.date || new Date(news.generated_date).toLocaleDateString("zh-TW"),
        imageUrl: news.imageUrl || imageMap[news.story_id] || "/api/placeholder/300/200"
      }));

      // 快取結果
      if (!customData) {
        const cacheKey = `news_initial_${ITEMS_PER_PAGE}`;
        newsCache.set(cacheKey, enhancedData);
      }

      setNewsData(enhancedData);
      setCurrentPage(1);
      setHasMore(enhancedData.length === ITEMS_PER_PAGE);
      
      if (onNewsCountUpdate) {
        onNewsCountUpdate(enhancedData.length);
      }

    } catch (error) {
      console.error("Error in loadInitialData:", error);
    }
    setIsLoading(false);
  }, [supabaseClient, customData, onNewsCountUpdate, ITEMS_PER_PAGE]);

  useEffect(() => {
    // 初始載入第一頁數據
    loadInitialData();
  }, [loadInitialData, supabaseClient]);

  const loadMoreNews = async () => {
    if (isLoading || !hasMore) return;
    
    setIsLoading(true);
    try {
      const nextPage = currentPage + 1;
      const offset = currentPage * ITEMS_PER_PAGE;

      const { data: fetchedData, error } = await supabaseClient
        .from("single_news")
        .select("story_id, news_title, ultra_short, generated_date")
        .order("generated_date", { ascending: false })
        .range(offset, offset + ITEMS_PER_PAGE - 1);

      if (error) {
        console.error("Error fetching more news:", error);
        setIsLoading(false);
        return;
      }

      // 批量獲取新聞圖片
      const storyIds = fetchedData.map(news => news.story_id);
      const { data: imagesData, error: imagesError } = await supabaseClient
        .from('generated_image')
        .select('story_id, image')
        .in('story_id', storyIds);

      // 建立圖片映射表
      const imageMap = {};
      if (!imagesError && imagesData) {
        imagesData.forEach(imageItem => {
          if (!imageMap[imageItem.story_id] && imageItem.image) {
            // 清理 base64 字串，移除可能的換行符和空白字符
            const cleanBase64 = imageItem.image.replace(/\s/g, '');
            // 將純 base64 字串轉換為完整的 data URL
            imageMap[imageItem.story_id] = `data:image/png;base64,${cleanBase64}`;
          }
        });
      }

      // 組合新數據
      const newEnhancedData = fetchedData.map(news => ({
        ...news,
        title: news.news_title || news.title,
        shortSummary: news.ultra_short || news.shortSummary,
        date: news.date || new Date(news.generated_date).toLocaleDateString("zh-TW"),
        imageUrl: news.imageUrl || imageMap[news.story_id] || "/api/placeholder/300/200"
      }));

      // 合併新數據到現有數據
      setNewsData(prevData => [...prevData, ...newEnhancedData]);
      setCurrentPage(nextPage);
      setHasMore(newEnhancedData.length === ITEMS_PER_PAGE);

      if (onNewsCountUpdate) {
        onNewsCountUpdate(newsData.length + newEnhancedData.length);
      }

    } catch (error) {
      console.error("Error in loadMoreNews:", error);
    }
    setIsLoading(false);
  };

  let filteredNews = newsData;
  if (keyword) {
    filteredNews = filteredNews.filter((news) =>
      (news.title && news.title.includes(keyword)) ||
      (news.shortSummary && news.shortSummary.includes(keyword))
    );
  }
  const displayNews = limit ? filteredNews.slice(0, limit) : filteredNews;

  return (
    <div className="unifiedNewsCard">
      {isLoading && newsData.length === 0 && (
        <div className="loading-container" style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '200px',
          fontSize: '16px',
          color: '#666'
        }}>
          載入中...
        </div>
      )}
      
      <div className="newsGrid">
        {displayNews.map((news) => (
          <div className="card" key={news.story_id}>
            <div className="card__image">
              <Link to={`/news/${news.story_id}`}>
                <img
                  src={news.imageUrl}
                  alt={news.title}
                  className="newsImage"
                  style={{
                    width: '100%',
                    height: '200px',
                    objectFit: 'cover'
                  }}
                  onError={(e) => {
                    e.target.src = "/api/placeholder/300/200";
                  }}
                />
              </Link>
            </div>

            <div className="card__header">
              <Link className="card__title" to={`/news/${news.story_id}`}>
                {news.title}
              </Link>
            </div>
            
            <div className="card__info">
              <span className="dateText">{news.date}</span>
              <span className="authorText">記者 gemini</span>
            </div>

            <div className="card__content">
              <p className="summaryText">
                {news.shortSummary}
              </p>
            </div>

            
          </div>
        ))}
      </div>
      
      {/* 閱讀更多新聞按鈕 */}
      {hasMore && newsData.length > 0 && (
        <div className="moreButtonWrap">
          <button 
            className="moreButton" 
            onClick={loadMoreNews}
            disabled={isLoading}
            style={{
              opacity: isLoading ? 0.6 : 1,
              cursor: isLoading ? 'not-allowed' : 'pointer'
            }}
          >
            {isLoading ? '載入中...' : '閱讀更多新聞'}
          </button>
        </div>
      )}
    </div>
  );
}

export default UnifiedNewsCard;
