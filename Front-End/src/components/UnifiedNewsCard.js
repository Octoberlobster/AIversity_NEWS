import React, { useMemo, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import "./../css/UnifiedNewsCard.css";
import { useHomeNews } from '../hooks/useHomeNews';
import { useBatchNewsImages } from '../hooks/useCategoryNews';
import { useLanguageFields } from '../utils/useLanguageFields';

function UnifiedNewsCard({ limit, keyword, customData, onNewsCountUpdate, country = 'Taiwan', showLoadMore = false }) {
  const { getCurrentLanguage } = useLanguageFields();
  const { t } = useTranslation();
  const ITEMS_PER_PAGE = 18;

  // 國家名稱映射
  const getCountryInfo = (country) => {
    const countryMap = {
      'Taiwan': { key: 'header.countries.taiwan', className: 'country-taiwan' },
      'United States of America': { key: 'header.countries.usa', className: 'country-usa' },
      'Japan': { key: 'header.countries.japan', className: 'country-japan' },
      'Indonesia': { key: 'header.countries.indonesia', className: 'country-indonesia' }
    };
    return countryMap[country] || null;
  };

  const getLanguageRoute = (path) => {
    return `/${getCurrentLanguage()}${path}`;
  };

  // 🎯 如果有 customData,直接使用 (來自 CategorySection)
  const useCustomData = !!customData;

  // 🎯 第一階段: 載入基本新聞資料 (只在沒有 customData 時)
  const {
    data: homeNewsData,
    isLoading,
    fetchNextPage,
    hasNextPage,
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
      imageUrl: news.imageUrl || imagesData[news.story_id] || "https://placehold.co/300x200/e5e7eb/9ca3af?text=…",
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
                    e.target.src = "https://placehold.co/300x200/e5e7eb/9ca3af?text=…";
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
              <span className="authorText">{t('common.editor')} {t('common.editorName')}</span>
              {news.country && getCountryInfo(news.country) && (
                <span className={`countryText ${getCountryInfo(news.country).className}`}>
                  {t(getCountryInfo(news.country).key)}
                </span>
              )}
            </div>

            <div className="card__content">
              <p className="summaryText">
                {news.shortSummary}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* 載入更多按鈕 - 只在首頁且有下一頁時顯示 */}
      {showLoadMore && !useCustomData && hasNextPage && (
        <div style={{ textAlign: 'center', margin: '2rem 0' }}>
          <button
            onClick={() => fetchNextPage()}
            disabled={isFetchingNextPage}
            style={{
              padding: '0.75rem 2rem',
              fontSize: '1rem',
              fontWeight: '600',
              color: '#fff',
              background: isFetchingNextPage ? '#94a3b8' : '#3b82f6',
              border: 'none',
              borderRadius: '8px',
              cursor: isFetchingNextPage ? 'not-allowed' : 'pointer',
              transition: 'all 0.3s ease',
              boxShadow: '0 2px 8px rgba(59, 130, 246, 0.3)',
            }}
            onMouseEnter={(e) => {
              if (!isFetchingNextPage) {
                e.target.style.background = '#2563eb';
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.4)';
              }
            }}
            onMouseLeave={(e) => {
              if (!isFetchingNextPage) {
                e.target.style.background = '#3b82f6';
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 2px 8px rgba(59, 130, 246, 0.3)';
              }
            }}
          >
            {isFetchingNextPage ? t('common.loadingMore') : t('common.loadMore')}
          </button>
        </div>
      )}
    </div>
  );
}

export default UnifiedNewsCard;
