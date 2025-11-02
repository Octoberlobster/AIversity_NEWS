import React, { useMemo, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import "./../css/UnifiedNewsCard.css";
import { useHomeNews } from '../hooks/useHomeNews';
import { useBatchNewsImages } from '../hooks/useCategoryNews';
import { useLanguageFields } from '../utils/useLanguageFields';

function UnifiedNewsCard({ limit, keyword, customData, onNewsCountUpdate, country = 'Taiwan' }) {
  const { getCurrentLanguage } = useLanguageFields();
  const { t } = useTranslation();
  const ITEMS_PER_PAGE = 18;

  const getLanguageRoute = (path) => {
    return `/${getCurrentLanguage()}${path}`;
  };

  // 🎯 如果有 customData,直接使用 (來自 CategorySection)
  const useCustomData = !!customData;

  // 🎯 第一階段: 載入基本新聞資料 (只在沒有 customData 時)
  const {
    data: homeNewsData,
    isLoading,
    hasNextPage,
    fetchNextPage,
    isFetchingNextPage,
  } = useHomeNews(country, ITEMS_PER_PAGE, !useCustomData); // 加入 enabled 參數

  // 合併所有頁面的新聞
  const basicNewsData = useMemo(() => {
    if (useCustomData) return customData;
    if (!homeNewsData) return [];
    return homeNewsData.pages.flatMap(page => page.news);
  }, [homeNewsData, customData, useCustomData]);

  // 提取所有 story_ids
  const storyIds = useMemo(() => {
    return basicNewsData.map(news => news.story_id);
  }, [basicNewsData]);

  // 🎯 第二階段: 背景載入圖片 (customData 可能已經有 imageUrl)
  const shouldLoadImages = useMemo(() => {
    // 如果是 customData 且已經有 imageUrl,就不需要載入
    if (useCustomData && customData.length > 0 && customData[0].imageUrl) {
      return false;
    }
    return storyIds.length > 0;
  }, [useCustomData, customData, storyIds]);

  const { data: imagesData = {} } = useBatchNewsImages(shouldLoadImages ? storyIds : []);

  // 合併資料
  const newsData = useMemo(() => {
    return basicNewsData.map(news => ({
      ...news,
      imageUrl: news.imageUrl || imagesData[news.story_id] || "https://placehold.co/300x200/e5e7eb/9ca3af?text=載入中...",
      isImageLoading: !news.imageUrl && !imagesData[news.story_id],
    }));
  }, [basicNewsData, imagesData]);

  // 通知父元件新聞數量
  useEffect(() => {
    if (onNewsCountUpdate) {
      onNewsCountUpdate(newsData.length);
    }
  }, [newsData.length, onNewsCountUpdate]);

  // 過濾關鍵字
  let filteredNews = newsData;
  if (keyword) {
    filteredNews = filteredNews.filter((news) =>
      (news.title && news.title.includes(keyword)) ||
      (news.shortSummary && news.shortSummary.includes(keyword))
    );
  }

  // 限制顯示數量
  const displayNews = limit ? filteredNews.slice(0, limit) : filteredNews;

  // 載入更多
  const handleLoadMore = () => {
    if (!useCustomData && hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  };

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
          {t('common.loading')}
        </div>
      )}
      
      <div className="newsGrid">
        {displayNews.map((news) => (
          <div className="card" key={news.story_id}>
            <div className="card__image">
              <Link to={getLanguageRoute(`/news/${news.story_id}`)}>
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
                    e.target.src = "https://placehold.co/300x200/e5e7eb/9ca3af?text=圖片載入失敗";
                  }}
                />
              </Link>
            </div>

            <div className="card__header">
              <Link className="card__title" to={getLanguageRoute(`/news/${news.story_id}`)}>
                {news.title}
              </Link>
            </div>
            
            <div className="card__info">
              <span className="dateText">{news.date}</span>
              <span className="authorText">{t('common.reporter')} gemini</span>
            </div>

            <div className="card__content">
              <p className="summaryText">
                {news.shortSummary}
              </p>
            </div>
          </div>
        ))}
      </div>
      
      {/* 閱讀更多新聞按鈕 - 只在非 customData 模式顯示 */}
      {!useCustomData && hasNextPage && newsData.length > 0 && (
        <div className="moreButtonWrap">
          <button 
            className="moreButton" 
            onClick={handleLoadMore}
            disabled={isFetchingNextPage}
            style={{
              opacity: isFetchingNextPage ? 0.6 : 1,
              cursor: isFetchingNextPage ? 'not-allowed' : 'pointer'
            }}
          >
            {isFetchingNextPage ? t('common.loading') : t('common.readMore')}
          </button>
        </div>
      )}
    </div>
  );
}

export default UnifiedNewsCard;
