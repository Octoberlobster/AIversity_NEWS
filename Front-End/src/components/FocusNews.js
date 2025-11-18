import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useLanguageFields } from '../utils/useLanguageFields';
import { useFocusNews } from '../hooks/useFocusNews';
import { useCountry } from './CountryContext';
import '../css/LatestTopics.css';

function FocusNews() {
  const [currentNewsIndex, setCurrentNewsIndex] = useState(0);
  const { t } = useTranslation();
  const { getCurrentLanguage } = useLanguageFields();
  const currentLanguage = getCurrentLanguage();
  const { selectedCountry } = useCountry();

  // 🚀 使用 React Query Hook 載入焦點新聞資料
  const { data: newsList = [], isLoading, error } = useFocusNews(selectedCountry);

  // 生成帶語言前綴的路由
  const getLanguageRoute = (path) => {
    const langPrefix = currentLanguage === 'zh-TW' ? '/zh-TW' : 
                      currentLanguage === 'en' ? '/en' : 
                      currentLanguage === 'jp' ? '/jp' : 
                      currentLanguage === 'id' ? '/id' : '/zh-TW';
    return `${langPrefix}${path}`;
  };

  // 自動輪播
  useEffect(() => {
    if (newsList.length <= 1) return;

    const interval = setInterval(() => {
      setCurrentNewsIndex((prevIndex) => 
        (prevIndex + 1) % newsList.length
      );
    }, 10000); // 每10秒切換一次

    return () => clearInterval(interval);
  }, [newsList.length]);

  // 手動切換到下一則新聞
  const nextNews = () => {
    setCurrentNewsIndex((prevIndex) => 
      (prevIndex + 1) % newsList.length
    );
  };

  // 手動切換到上一則新聞
  const prevNews = () => {
    setCurrentNewsIndex((prevIndex) => 
      prevIndex === 0 ? newsList.length - 1 : prevIndex - 1
    );
  };

  // 手動切換到指定新聞
  const goToNews = (index) => {
    setCurrentNewsIndex(index);
  };

  if (isLoading) {
    return (
      <div className="latest-topics">
        <div className="latest-topics-loading">{t('common.loading')}</div>
      </div>
    );
  }

  if (error || newsList.length === 0) {
    return null; // 如果沒有數據就不顯示整個組件
  }

  const currentNews = newsList[currentNewsIndex];

  return (
    <div className="latest-topics">
      {/* 標題區域 */}
      <div className="latest-topics-title-section">
        <div className="latest-topics-title-content">
          <span className="star-icon">⭐</span>
          {t('home.focusNews')}
        </div>
      </div>

      {/* 主要內容區域 */}
      <div className="latest-topics-main">
        {/* 左側：新聞輪播 */}
        <div className="topic-carousel">
          <div className="carousel-container">
            <div className="carousel-main">
              <div className="carousel-wrapper">
                {newsList.map((news, index) => (
                  <div 
                    key={news.story_id}
                    className={`carousel-slide ${index === currentNewsIndex ? 'active' : ''}`}
                  >
                    {news.imageUrl && (
                      <Link to={getLanguageRoute(`/news/${news.story_id}`)} className="slide-image-link">
                        <div className="slide-image">
                          <img 
                            src={news.imageUrl} 
                            alt={news.title}
                            onError={(e) => {
                              e.target.src = 'https://placehold.co/1200x600/e5e7eb/9ca3af?text=News';
                            }}
                          />
                          <div className="slide-overlay"></div>
                        </div>
                      </Link>
                    )}
                    
                    <div className="slide-content">
                      <Link to={getLanguageRoute(`/news/${news.story_id}`)} className="slide-title-link">
                        <h2 className="slide-title">{news.title}</h2>
                      </Link>
                      <p className="slide-summary">
                        {news.summary 
                          ? (news.summary.length > 120 
                              ? news.summary.substring(0, 120) + '...' 
                              : news.summary)
                          : ''
                        }
                      </p>
                      <div className="slide-meta">
                        <span className="slide-date">
                          {news.date || ''}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* 控制按鈕 */}
              {newsList.length > 1 && (
                <>
                  <button className="carousel-btn carousel-btn-prev" onClick={prevNews}>
                    ‹
                  </button>
                  <button className="carousel-btn carousel-btn-next" onClick={nextNews}>
                    ›
                  </button>
                </>
              )}

              {/* 指示器 */}
              {newsList.length > 1 && (
                <div className="carousel-indicators">
                  {newsList.map((_, index) => (
                    <button
                      key={index}
                      className={`indicator ${index === currentNewsIndex ? 'active' : ''}`}
                      onClick={() => goToNews(index)}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 右側：新聞來源 */}
        <div className="topic-sidebar">
          <div className="sidebar-card">
            <h3 className="sidebar-title">{t('home.newsSources')}</h3>
            <div className="branches-list">
              {currentNews.sources && currentNews.sources.length > 0 ? (
                currentNews.sources.map((source, index) => (
                  <a
                    key={index}
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="branch-item"
                  >
                    <span className="branch-name">
                      {source.media + " : " + (source.title.length > 25 ? source.title.substring(0, 25) + '...' : source.title)}
                    </span>
                    <span className="branch-arrow">→</span>
                  </a>
                ))
              ) : (
                <div className="no-branches">{t('home.noSources')}</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default FocusNews;
