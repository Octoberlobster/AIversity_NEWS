import React, { useMemo, useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useCountry } from './CountryContext';
// import { useNewsImages, useRelatedSources } from '../hooks/useYesterdayNews';
import { useQueries } from '@tanstack/react-query';
import { useSupabase } from './supabase';
import '../css/YesterdayFocus.css';

function YesterdayFocus() {
  const { t } = useTranslation();
  const { selectedCountry } = useCountry();
  const location = useLocation();
  const supabase = useSupabase();

  // 獲取當前語言
  const currentLang = location.pathname.split('/')[1] || 'zh-TW';

  // 計算最新日期(昨天)作為預設值 - 使用台灣時區
  const getLatestDate = () => {
    // 使用台灣時區 (UTC+8)
    const today = new Date();
    const taiwanTime = new Date(today.toLocaleString('en-US', { timeZone: 'Asia/Taipei' }));
    const yesterday = new Date(taiwanTime);
    yesterday.setDate(yesterday.getDate() - 1);
    
    const year = yesterday.getFullYear();
    const month = String(yesterday.getMonth() + 1).padStart(2, '0');
    const day = String(yesterday.getDate()).padStart(2, '0');
    
    return `${year}-${month}-${day}`;
  };

  // 計算今天日期 - 使用台灣時區（作為日期選擇器的最大值）
  const getTodayDate = () => {
    const today = new Date();
    const taiwanTime = new Date(today.toLocaleString('en-US', { timeZone: 'Asia/Taipei' }));
    
    const year = taiwanTime.getFullYear();
    const month = String(taiwanTime.getMonth() + 1).padStart(2, '0');
    const day = String(taiwanTime.getDate()).padStart(2, '0');
    
    return `${year}-${month}-${day}`;
  };

  // 日期狀態 (預設為今天)
  const [selectedDate, setSelectedDate] = useState(getTodayDate());
  
  // 追蹤要載入的日期列表 (用於累積載入)
  const [datesToLoad, setDatesToLoad] = useState([getTodayDate()]);

  // 國家 ID 對應到翻譯 key
  const countryTranslationMap = {
    'taiwan': 'header.countries.taiwan',
    'usa': 'header.countries.usa',
    'japan': 'header.countries.japan',
    'indonesia': 'header.countries.indonesia'
  };

  const countryTranslationKey = countryTranslationMap[selectedCountry] || 'header.countries.taiwan';
  const currentCountryLabel = t(countryTranslationKey);

  // 國家 ID 對應到資料庫的 country 值
  const countryDbMap = {
    'taiwan': 'Taiwan',
    'usa': 'United States of America',
    'japan': 'Japan',
    'indonesia': 'Indonesia'
  };

  const currentCountryDbName = countryDbMap[selectedCountry] || 'Taiwan';

  // 語言欄位後綴映射
  const LANGUAGE_SUFFIX_MAP = {
    'zh-TW': '',
    'en': '_en_lang',
    'jp': '_jp_lang',
    'id': '_id_lang'
  };
  const suffix = LANGUAGE_SUFFIX_MAP[currentLang] || '';

  // 🎯 使用 useQueries 批次載入多個日期的新聞 (React Query 會自動處理快取)
  const newsQueries = useQueries({
    queries: datesToLoad.map(date => ({
      queryKey: ['yesterday-news', currentCountryDbName, date, currentLang],
      queryFn: async () => {
        console.log('[YesterdayFocus] 載入日期:', date);
        
        // 1. 拉取 top_ten_news
        const { data: topTenData, error: topTenError } = await supabase
          .from('top_ten_news')
          .select('*')
          .eq('country', currentCountryDbName)
          .eq('date', date);

        if (topTenError) throw topTenError;
        if (!topTenData || topTenData.length === 0) return [];

        // 2. 解析 story_ids
        const allStoryIds = [];
        topTenData.forEach(item => {
          const parsedJson = typeof item.top_ten_news_id === 'string' 
            ? JSON.parse(item.top_ten_news_id) 
            : item.top_ten_news_id;
          allStoryIds.push(...parsedJson.top_ten_story_ids);
        });

        // 3. 批量拉取新聞基本資料
        const titleField = suffix ? `news_title, news_title${suffix}` : 'news_title';
        const summaryField = suffix ? `ultra_short, ultra_short${suffix}` : 'ultra_short';
        
        const { data: newsData, error: newsError } = await supabase
          .from('single_news')
          .select(`story_id, ${titleField}, ${summaryField}, generated_date`)
          .in('story_id', allStoryIds)
          .order('generated_date', { ascending: false });

        if (newsError) throw newsError;

        return newsData.map(news => ({
          id: news.story_id,
          title: suffix ? (news[`news_title${suffix}`] || news.news_title) : news.news_title,
          summary: suffix ? (news[`ultra_short${suffix}`] || news.ultra_short) : news.ultra_short,
          date: news.generated_date,
          loadDate: date,
        }));
      },
      staleTime: 10 * 60 * 1000,
      cacheTime: 60 * 60 * 1000,
      enabled: !!currentCountryDbName && !!date,
    }))
  });

  // 合併所有日期的新聞資料
  const basicNewsData = useMemo(() => {
    const allNews = [];
    newsQueries.forEach(query => {
      if (query.data) {
        allNews.push(...query.data);
      }
    });
    return allNews;
  }, [newsQueries]);

  // 檢查是否有任何查詢正在載入且沒有快取資料
  const isLoadingBasic = newsQueries.some(query => query.isLoading && !query.data);
  
  // 檢查是否正在載入更多(有資料但還在載入新的)
  const isLoadingMore = newsQueries.some(query => query.isLoading) && basicNewsData.length > 0;
  
  // 檢查是否有任何查詢錯誤
  const basicError = newsQueries.find(query => query.error)?.error;

  // 提取所有 story_ids 用於載入圖片和來源
  // const storyIds = useMemo(() => {
  //   return basicNewsData.map(news => news.id);
  // }, [basicNewsData]);

  // 🎯 第二階段: 背景載入圖片 (延遲執行) - 改為分批載入
  // const { data: imagesData = {} } = useNewsImages(storyIds);
  const imageQueries = useQueries({
    queries: newsQueries.map(newsQuery => {
      const newsList = newsQuery.data || [];
      const ids = newsList.map(n => n.id);
      return {
        queryKey: ['news-images-batch', ...ids],
        queryFn: async () => {
          if (!ids || ids.length === 0) return {};
          console.log('[YesterdayFocus] 載入圖片批次:', ids.length);
          
          const { data, error } = await supabase
            .from('generated_image')
            .select('story_id, image')
            .in('story_id', ids);

          if (error) throw error;

          const map = {};
          data.forEach(item => {
            if (item.image) {
              try {
                const cleanBase64 = item.image.replace(/\s/g, '');
                map[item.story_id] = `data:image/png;base64,${cleanBase64}`;
              } catch (e) {
                map[item.story_id] = 'https://placehold.co/300x200/e5e7eb/9ca3af?text=…';
              }
            }
          });
          return map;
        },
        enabled: ids.length > 0,
        staleTime: 30 * 60 * 1000,
        cacheTime: 2 * 60 * 60 * 1000,
      };
    })
  });

  // 合併所有圖片資料
  const imagesData = useMemo(() => {
    const allImages = {};
    imageQueries.forEach(query => {
      if (query.data) {
        Object.assign(allImages, query.data);
      }
    });
    return allImages;
  }, [imageQueries]);

  // 🎯 第三階段: 背景載入相關來源 (延遲執行) - 改為分批載入
  // const { data: sourcesData = {} } = useRelatedSources(storyIds);
  const sourceQueries = useQueries({
    queries: newsQueries.map(newsQuery => {
      const newsList = newsQuery.data || [];
      const ids = newsList.map(n => n.id);
      return {
        queryKey: ['related-sources-batch', ...ids],
        queryFn: async () => {
          if (!ids || ids.length === 0) return {};
          console.log('[YesterdayFocus] 載入來源批次:', ids.length);

          const { data, error } = await supabase
            .from('cleaned_news')
            .select('story_id, article_title, article_url, media')
            .in('story_id', ids);

          if (error) throw error;

          const map = {};
          data.forEach(item => {
            if (!map[item.story_id]) map[item.story_id] = [];
            map[item.story_id].push({
              id: map[item.story_id].length + 1,
              media: item.media || new URL(item.article_url).hostname.replace('www.', ''),
              name: item.article_title,
              url: item.article_url,
            });
          });
          return map;
        },
        enabled: ids.length > 0,
        staleTime: 10 * 60 * 1000,
        cacheTime: 60 * 60 * 1000,
      };
    })
  });

  // 合併所有來源資料
  const sourcesData = useMemo(() => {
    const allSources = {};
    sourceQueries.forEach(query => {
      if (query.data) {
        Object.assign(allSources, query.data);
      }
    });
    return allSources;
  }, [sourceQueries]);

  // 合併所有資料
  const newsData = useMemo(() => {
    return basicNewsData.map(news => ({
      ...news,
      image: imagesData[news.id] || 'https://placehold.co/300x200/e5e7eb/9ca3af?text=…',
      relatedSources: sourcesData[news.id] || [],
    }));
  }, [basicNewsData, imagesData, sourcesData]);

  // Debug logging
  useEffect(() => {
    console.log('[YesterdayFocus] 狀態更新:', {
      選擇日期: selectedDate,
      要載入的日期: datesToLoad,
      選擇國家: selectedCountry,
      基本資料數量: basicNewsData.length,
      已載入圖片數量: Object.keys(imagesData).length,
      已載入來源數量: Object.keys(sourcesData).length,
    });
  }, [selectedDate, datesToLoad, selectedCountry, basicNewsData.length, imagesData, sourcesData]);

  // 日期選擇處理函數
  const handleDateChange = (e) => {
    const newDate = e.target.value;
    setSelectedDate(newDate);
    setDatesToLoad([newDate]);
  };

  // 快速日期選擇函數 - 重置載入列表
  const selectLatestDate = () => {
    // 使用台灣時區計算今天日期
    const now = new Date();
    const taiwanTime = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Taipei' }));
    
    const year = taiwanTime.getFullYear();
    const month = String(taiwanTime.getMonth() + 1).padStart(2, '0');
    const day = String(taiwanTime.getDate()).padStart(2, '0');
    const currentDate = `${year}-${month}-${day}`;
    
    console.log('[YesterdayFocus] 最新按鈕:', {
      台灣時間: taiwanTime.toLocaleString('zh-TW', { timeZone: 'Asia/Taipei' }),
      選擇日期: currentDate
    });
    
    setSelectedDate(currentDate);
    setDatesToLoad([currentDate]);
  };

  const selectDateOffset = (days) => {
    // 使用台灣時區計算日期
    const today = new Date();
    const taiwanTime = new Date(today.toLocaleString('en-US', { timeZone: 'Asia/Taipei' }));
    const targetDate = new Date(taiwanTime);
    targetDate.setDate(targetDate.getDate() + days);
    
    const year = targetDate.getFullYear();
    const month = String(targetDate.getMonth() + 1).padStart(2, '0');
    const day = String(targetDate.getDate()).padStart(2, '0');
    const newDate = `${year}-${month}-${day}`;
    
    setSelectedDate(newDate);
    setDatesToLoad([newDate]);
  };
  
  // 載入更多新聞 (前一天)
  const loadMoreNews = () => {
    // 計算最後一個已載入日期的前一天
    const lastDate = datesToLoad[datesToLoad.length - 1];
    const dateObj = new Date(lastDate);
    dateObj.setDate(dateObj.getDate() - 1);
    
    const year = dateObj.getFullYear();
    const month = String(dateObj.getMonth() + 1).padStart(2, '0');
    const day = String(dateObj.getDate()).padStart(2, '0');
    const previousDate = `${year}-${month}-${day}`;
    
    console.log('[YesterdayFocus] 載入更多:', {
      當前日期列表: datesToLoad,
      新增日期: previousDate
    });
    
    // 加入新日期到列表 (React Query 會自動處理快取)
    setDatesToLoad(prev => [...prev, previousDate]);
  };
  
  // 當選擇的國家改變時,重置日期列表
  useEffect(() => {
    setDatesToLoad([selectedDate]);
  }, [selectedCountry, selectedDate]);

  // 載入狀態 - 只有在完全沒有資料且正在載入時才顯示
  if (isLoadingBasic && basicNewsData.length === 0) {
    return (
      <div className="yesterday-focus-container">
        <div className="focus-wrapper">
          <div className="focus-header">
            <h1 className="yesterday-title">{t('yesterdayFocus.title', { country: currentCountryLabel })}</h1>
          <div className="date-selector">
            <div className="date-controls">
              <button onClick={() => selectDateOffset(-1)} className="date-btn">{t('yesterdayFocus.dateButtons.yesterday')}</button>
              <input 
                type="date" 
                value={selectedDate}
                onChange={handleDateChange}
                className="date-input"
                max={getTodayDate()}
              />
              <button onClick={selectLatestDate} className="date-btn date-btn-primary">{t('yesterdayFocus.dateButtons.latest')}</button>
              </div>
            </div>
          </div>
          <div className="loading-container">{t('common.loading')}</div>
        </div>
      </div>
    );
  }

  // 錯誤狀態
  if (basicError) {
    return (
      <div className="yesterday-focus-container">
        <div className="focus-wrapper">
          <div className="focus-header">
            <h1 className="yesterday-title">{t('yesterdayFocus.title', { country: currentCountryLabel })}</h1>
            <div className="date-selector">
              <div className="date-controls">
                <button onClick={() => selectDateOffset(-1)} className="date-btn">{t('yesterdayFocus.dateButtons.yesterday')}</button>
                <input 
                  type="date" 
                  value={selectedDate}
                  onChange={handleDateChange}
                  className="date-input"
                  max={getTodayDate()}
                />
                <button onClick={selectLatestDate} className="date-btn date-btn-primary">{t('yesterdayFocus.dateButtons.latest')}</button>
              </div>
            </div>
          </div>
          <div className="no-content">{t('yesterdayFocus.loadFailed')}</div>
        </div>
      </div>
    );
  }

  // 無資料狀態
  if (newsData.length === 0) {
    return (
      <div className="yesterday-focus-container">
        <div className="focus-wrapper">
          <div className="focus-header">
            <h1 className="yesterday-title">{t('yesterdayFocus.title', { country: currentCountryLabel })}</h1>
            <div className="date-selector">
              <div className="date-controls">
                <button onClick={() => selectDateOffset(-1)} className="date-btn">{t('yesterdayFocus.dateButtons.yesterday')}</button>
                <input 
                  type="date" 
                  value={selectedDate}
                  onChange={handleDateChange}
                  className="date-input"
                  max={getTodayDate()}
                />
                <button onClick={selectLatestDate} className="date-btn date-btn-primary">{t('yesterdayFocus.dateButtons.latest')}</button>
              </div>
            </div>
          </div>
          <div className="no-content">{t('yesterdayFocus.noContent')}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="yesterday-focus-container">
      <div className="focus-wrapper">
        <div className="focus-header">
          <h1 className="yesterday-title">
            {t('yesterdayFocus.title', { country: currentCountryLabel })}
          </h1>
          <div className="date-selector">
            <div className="date-controls">
              <button 
                onClick={() => selectDateOffset(-1)}
                className="date-btn"
                title={t('yesterdayFocus.dateButtonTitles.yesterday')}
              >
                {t('yesterdayFocus.dateButtons.yesterday')}
              </button>
              <input 
                type="date" 
                value={selectedDate}
                onChange={handleDateChange}
                className="date-input"
                max={getTodayDate()}
              />
              <button 
                onClick={selectLatestDate}
                className="date-btn date-btn-primary"
                title={t('yesterdayFocus.dateButtonTitles.latest')}
              >
                {t('yesterdayFocus.dateButtons.latest')}
              </button>
            </div>
          </div>
        </div>

        <div className="news-cards-list">
          {newsData.map(news => (
            <div key={news.id} className="news-card-container">
              {/* 左側:新聞內容 */}
              <div className="card-main">
                <a 
                  href={`/${currentLang}/news/${news.id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="card-title-link"
                >
                  <h3 className="card-title">
                    {news.title}
                  </h3>
                </a>
                <div className="card-date">
                  {news.date}
                </div>
                <a 
                  href={`/${currentLang}/news/${news.id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="card-image-link"
                >
                  <div className="card-image">
                    <img 
                      src={news.image} 
                      alt={news.title}
                      onError={(e) => {
                        e.target.src = 'https://placehold.co/400x250/e5e7eb/9ca3af?text=…';
                      }}
                    />
                  </div>
                </a>
                <div className="card-content">
                  <p className="card-summary">{news.summary}</p>
                </div>
              </div>

              {/* 右側:相關來源側邊欄 */}
              <div className="card-sidebar">
                <h4 className="sidebar-title">{t('yesterdayFocus.relatedSources')}</h4>
                <div className="sources-list">
                  {news.relatedSources && news.relatedSources.length > 0 ? (
                    <>
                      {news.relatedSources.slice(0, 3).map(source => (
                        <a 
                          key={`${news.id}-${source.id}`} 
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="source-item"
                        >
                          <span className="source-media">{source.media}</span>
                          <span className="source-name">{source.name}</span>
                        </a>
                      ))}
                      {news.relatedSources.length > 3 && (
                        <div className="source-more">
                          <span>...</span>
                        </div>
                      )}
                    </>
                  ) : (
                    <div style={{ padding: '0.5rem', color: 'rgba(255,255,255,0.7)', fontSize: '0.85rem' }}>
                      {t('common.loading')}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* 閱讀更多按鈕 - 載入前一天新聞 */}
        <div className="load-more-section">
          {isLoadingMore && (
            <div className="loading-container" style={{ margin: '2rem 0' }}>
              {t('common.loading') || '載入中...'}
            </div>
          )}
          <button 
            onClick={loadMoreNews}
            className="load-more-btn"
            disabled={isLoadingMore}
          >
            <span>{t('yesterdayFocus.loadMore') || '查看前一天的焦點'}</span>
          </button>
        </div>

        {/* 回到最上面按鈕 */}
        <button 
          className="back-to-top-btn"
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          title={t('common.backToTop')}
        >
          ↑
        </button>
      </div>
    </div>
  );
}

export default YesterdayFocus;