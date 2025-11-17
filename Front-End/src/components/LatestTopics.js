import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useLanguageFields } from '../utils/useLanguageFields';
import { useLatestTopics } from '../hooks/useSpecialReports';
import { useCountry } from './CountryContext';
import '../css/LatestTopics.css';

function LatestTopics() {
  const [currentTopicIndex, setCurrentTopicIndex] = useState(0);
  const { t } = useTranslation();
  const { getCurrentLanguage } = useLanguageFields();
  const currentLanguage = getCurrentLanguage();
  const { selectedCountry } = useCountry();

  // 🚀 使用 React Query Hook 載入資料
  const { topics: rawTopics, newsMap, imageData, branches, isLoading, error } = useLatestTopics();

  // 🚀 組合最終資料 (使用 useMemo 優化)
  const topics = useMemo(() => {
    if (!rawTopics || rawTopics.length === 0) return [];

    const { imageMap, topicToStoryMap } = imageData;
    const topicsWithData = [];

    // 多語言欄位映射
    const languageFieldMap = {
      'zh-TW': { title: 'topic_title', short: 'topic_short' },
      'en': { title: 'topic_title_en_lang', short: 'topic_short_en_lang' },
      'jp': { title: 'topic_title_jp_lang', short: 'topic_short_jp_lang' },
      'id': { title: 'topic_title_id_lang', short: 'topic_short_id_lang' }
    };

    const fields = languageFieldMap[currentLanguage] || languageFieldMap['zh-TW'];

    for (const topic of rawTopics) {
      const storyIds = newsMap[topic.topic_id];
      
      // 跳過沒有新聞的專題
      if (!storyIds || storyIds.length === 0) {
        console.log(`專題 ${topic[fields.title] || topic.topic_title} 沒有相關新聞，跳過`);
        continue;
      }

      // 獲取代表性圖片
      const firstStoryId = topicToStoryMap[topic.topic_id];
      const representativeImage = firstStoryId ? imageMap[firstStoryId] : null;

      // 獲取分支 (最多 4 個)
      const topicBranches = (branches[topic.topic_id] || [])
        .filter(branch => branch.title && branch.title.trim() !== '')
        .slice(0, 4);

      topicsWithData.push({
        ...topic,
        topic_title: topic[fields.title] || topic.topic_title,
        topic_short: topic[fields.short] || topic.topic_short,
        newsCount: storyIds.length,
        branches: topicBranches,
        representativeImage: representativeImage
      });

      // 最多 5 個專題
      if (topicsWithData.length >= 5) break;
    }

    console.log('[LatestTopics] 最終資料:', topicsWithData.length, '個專題');
    return topicsWithData;
  }, [rawTopics, newsMap, imageData, branches, currentLanguage]);

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
    if (topics.length <= 1) return;

    const interval = setInterval(() => {
      setCurrentTopicIndex((prevIndex) => 
        (prevIndex + 1) % topics.length
      );
    }, 10000); // 每10秒切換一次

    return () => clearInterval(interval);
  }, [topics.length]);

  // 手動切換到下一個專題
  const nextTopic = () => {
    setCurrentTopicIndex((prevIndex) => 
      (prevIndex + 1) % topics.length
    );
  };

  // 手動切換到上一個專題
  const prevTopic = () => {
    setCurrentTopicIndex((prevIndex) => 
      prevIndex === 0 ? topics.length - 1 : prevIndex - 1
    );
  };

  // 手動切換到指定專題
  const goToTopic = (index) => {
    setCurrentTopicIndex(index);
  };

  if (isLoading) {
    return (
      <div className="latest-topics">
        <div className="latest-topics-loading">{t('common.loading')}</div>
      </div>
    );
  }

  // 如果不是選擇臺灣，就顯示沒有專題
  if (selectedCountry !== 'taiwan') {
    return (
      <div className="latest-topics">
        <div className="latest-topics-title-section">
          <div className="latest-topics-title-content">
            <span className="star-icon">⭐</span>
            {t('home.latestTopic')}
          </div>
        </div>
        <div className="latest-topics-main">
          <div className="no-topics-message">
            {t('home.noTopics')}
          </div>
        </div>
      </div>
    );
  }

  if (error || topics.length === 0) {
    return null; // 如果沒有數據就不顯示整個組件
  }

  const currentTopic = topics[currentTopicIndex];

  return (
    <div className="latest-topics">
      {/* 標題區域 - 仿照熱門新聞的樣式 */}
      <div className="latest-topics-title-section">
        <div className="latest-topics-title-content">
          <span className="star-icon">⭐</span>
          {t('home.latestTopic')}
        </div>
      </div>

      {/* 主要內容區域 */}
      <div className="latest-topics-main">
        {/* 左側：專題跑馬燈 - 仿照現有跑馬燈樣式 */}
        <div className="topic-carousel">
          <div className="carousel-container">
            <div className="carousel-main">
              <div className="carousel-wrapper">
                {topics.map((topic, index) => (
                  <div 
                    key={topic.topic_id}
                    className={`carousel-slide ${index === currentTopicIndex ? 'active' : ''}`}
                  >
                    {topic.representativeImage && (
                      <Link to={getLanguageRoute(`/special-report/${topic.topic_id}`)} className="slide-image-link">
                        <div className="slide-image">
                          <img 
                            src={topic.representativeImage.imageUrl || 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=1200&h=600&fit=crop'} 
                            alt={topic.representativeImage.description || topic.topic_title}
                            onError={(e) => {
                              e.target.src = 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=1200&h=600&fit=crop';
                            }}
                          />
                          <div className="slide-overlay"></div>
                        </div>
                      </Link>
                    )}
                    
                    <div className="slide-content">
                      <Link to={getLanguageRoute(`/special-report/${topic.topic_id}`)} className="slide-title-link">
                        <h2 className="slide-title">{topic.topic_title}</h2>
                      </Link>
                      <p className="slide-summary">
                        {topic.topic_short 
                          ? (topic.topic_short.length > 120 
                              ? topic.topic_short.substring(0, 120) + '...' 
                              : topic.topic_short)
                          : '探索這個重要專題的深度報導...'
                        }
                      </p>
                      <div className="slide-meta">
                        <span className="slide-date">
                          {topic.generated_date || ''}
                        </span>
                        <span className="slide-news-count">
                          {topic.newsCount} {t('home.articles')}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* 控制按鈕 */}
              {topics.length > 1 && (
                <>
                  <button className="carousel-btn carousel-btn-prev" onClick={prevTopic}>
                    ‹
                  </button>
                  <button className="carousel-btn carousel-btn-next" onClick={nextTopic}>
                    ›
                  </button>
                </>
              )}

              {/* 指示器 */}
              {topics.length > 1 && (
                <div className="carousel-indicators">
                  {topics.map((_, index) => (
                    <button
                      key={index}
                      className={`indicator ${index === currentTopicIndex ? 'active' : ''}`}
                      onClick={() => goToTopic(index)}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 右側：專題分支 - 仿照側欄卡片樣式 */}
        <div className="topic-sidebar">
          <div className="sidebar-card">
            <h3 className="sidebar-title">{t('home.topicNavigation')}</h3>
            <div className="branches-list">
              {currentTopic.branches.length > 0 ? (
                currentTopic.branches.map((branch, index) => (
                  <Link
                    key={branch.id}
                    to={getLanguageRoute(`/special-report/${currentTopic.topic_id}?branch=${encodeURIComponent(branch.id)}`)}
                    className="branch-item"
                  >
                    <span className="branch-icon">📰</span>
                    <span className="branch-name">{branch.title}</span>
                    <span className="branch-arrow">→</span>
                  </Link>
                ))
              ) : (
                <div className="no-branches">{t('home.nobranches')}</div> // 如果專題沒有分支，顯示提示
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LatestTopics;