import React, { useMemo, useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useCountry } from './CountryContext';
import { useYesterdayNews, useNewsImages, useRelatedSources } from '../hooks/useYesterdayNews';
import '../css/YesterdayFocus.css';

function YesterdayFocus() {
  const { t } = useTranslation();
  const { selectedCountry } = useCountry();
  const location = useLocation();

  // 獲取當前語言
  const currentLang = location.pathname.split('/')[1] || 'zh-TW';

  // 計算最新日期(昨天)作為預設值
  const getLatestDate = () => {
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    const year = yesterday.getFullYear();
    const month = String(yesterday.getMonth() + 1).padStart(2, '0');
    const day = String(yesterday.getDate()).padStart(2, '0');
    
    return `${year}-${month}-${day}`;
  };

  // 日期狀態 (預設為最新/昨天)
  const [selectedDate, setSelectedDate] = useState(getLatestDate());
  
  // 時間狀態 (預設為 00:00)
  const [selectedTime, setSelectedTime] = useState('00:00');

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

  // 🎯 第一階段: 載入基本新聞資料 (文字內容)
  const { 
    data: basicNewsData = [], 
    isLoading: isLoadingBasic,
    error: basicError 
  } = useYesterdayNews(currentCountryDbName, selectedDate, currentLang);

  // 提取所有 story_ids 用於載入圖片和來源
  const storyIds = useMemo(() => {
    return basicNewsData.map(news => news.id);
  }, [basicNewsData]);

  // 🎯 第二階段: 背景載入圖片 (延遲執行)
  const { data: imagesData = {} } = useNewsImages(storyIds);

  // 🎯 第三階段: 背景載入相關來源 (延遲執行)
  const { data: sourcesData = {} } = useRelatedSources(storyIds);

  // 合併所有資料
  const newsData = useMemo(() => {
    return basicNewsData.map(news => ({
      ...news,
      image: imagesData[news.id] || 'https://placehold.co/400x250/e5e7eb/9ca3af?text=載入中...',
      relatedSources: sourcesData[news.id] || [],
    }));
  }, [basicNewsData, imagesData, sourcesData]);

  // Debug logging
  useEffect(() => {
    console.log('[YesterdayFocus] 狀態更新:', {
      選擇日期: selectedDate,
      選擇國家: selectedCountry,
      基本資料數量: basicNewsData.length,
      已載入圖片數量: Object.keys(imagesData).length,
      已載入來源數量: Object.keys(sourcesData).length,
    });
  }, [selectedDate, selectedCountry, basicNewsData.length, imagesData, sourcesData]);

  // 日期選擇處理函數
  const handleDateChange = (e) => {
    setSelectedDate(e.target.value);
  };

  // 時間選擇處理函數
  const handleTimeChange = (time) => {
    setSelectedTime(time);
  };

  // 快速日期選擇函數
  const selectLatestDate = () => {
    setSelectedDate(getLatestDate());
    setSelectedTime('00:00'); // 重置為預設時間
  };

  const selectDateOffset = (days) => {
    const today = new Date();
    const targetDate = new Date(today);
    targetDate.setDate(targetDate.getDate() + days);
    
    const year = targetDate.getFullYear();
    const month = String(targetDate.getMonth() + 1).padStart(2, '0');
    const day = String(targetDate.getDate()).padStart(2, '0');
    
    setSelectedDate(`${year}-${month}-${day}`);
  };

  // 載入狀態
  if (isLoadingBasic) {
    return (
      <div className="yesterday-focus-container">
        <div className="focus-wrapper">
          <div className="focus-header">
            <h1 className="yesterday-title">{t('yesterdayFocus.title', { country: currentCountryLabel })}</h1>
            <div className="date-selector">
              <div className="date-controls">
                <button onClick={() => selectDateOffset(-7)} className="date-btn">-7天</button>
                <button onClick={() => selectDateOffset(-3)} className="date-btn">-3天</button>
                <button onClick={() => selectDateOffset(-1)} className="date-btn">昨天</button>
                <input 
                  type="date" 
                  value={selectedDate}
                  onChange={handleDateChange}
                  className="date-input"
                  max={getLatestDate()}
                />
                <button onClick={selectLatestDate} className="date-btn date-btn-primary">最新</button>
              </div>
              <div className="time-controls">
                <span className="time-label">時間:</span>
                {['00:00', '06:00', '12:00', '18:00'].map(time => (
                  <button
                    key={time}
                    onClick={() => handleTimeChange(time)}
                    className={`time-btn ${selectedTime === time ? 'time-btn-active' : ''}`}
                  >
                    {time}
                  </button>
                ))}
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
                <button onClick={() => selectDateOffset(-7)} className="date-btn">-7天</button>
                <button onClick={() => selectDateOffset(-3)} className="date-btn">-3天</button>
                <button onClick={() => selectDateOffset(-1)} className="date-btn">昨天</button>
                <input 
                  type="date" 
                  value={selectedDate}
                  onChange={handleDateChange}
                  className="date-input"
                  max={getLatestDate()}
                />
                <button onClick={selectLatestDate} className="date-btn date-btn-primary">最新</button>
              </div>
              <div className="time-controls">
                <span className="time-label">時間:</span>
                {['00:00', '06:00', '12:00', '18:00'].map(time => (
                  <button
                    key={time}
                    onClick={() => handleTimeChange(time)}
                    className={`time-btn ${selectedTime === time ? 'time-btn-active' : ''}`}
                  >
                    {time}
                  </button>
                ))}
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
                <button onClick={() => selectDateOffset(-7)} className="date-btn">-7天</button>
                <button onClick={() => selectDateOffset(-3)} className="date-btn">-3天</button>
                <button onClick={() => selectDateOffset(-1)} className="date-btn">昨天</button>
                <input 
                  type="date" 
                  value={selectedDate}
                  onChange={handleDateChange}
                  className="date-input"
                  max={getLatestDate()}
                />
                <button onClick={selectLatestDate} className="date-btn date-btn-primary">最新</button>
              </div>
              <div className="time-controls">
                <span className="time-label">時間:</span>
                {['00:00', '06:00', '12:00', '18:00'].map(time => (
                  <button
                    key={time}
                    onClick={() => handleTimeChange(time)}
                    className={`time-btn ${selectedTime === time ? 'time-btn-active' : ''}`}
                  >
                    {time}
                  </button>
                ))}
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
                onClick={() => selectDateOffset(-7)}
                className="date-btn"
                title="7天前"
              >
                -7天
              </button>
              <button 
                onClick={() => selectDateOffset(-3)}
                className="date-btn"
                title="3天前"
              >
                -3天
              </button>
              <button 
                onClick={() => selectDateOffset(-1)}
                className="date-btn"
                title="昨天"
              >
                昨天
              </button>
              <input 
                type="date" 
                value={selectedDate}
                onChange={handleDateChange}
                className="date-input"
                max={getLatestDate()}
              />
              <button 
                onClick={selectLatestDate}
                className="date-btn date-btn-primary"
                title="最新"
              >
                最新
              </button>
            </div>
            <div className="time-controls">
              <span className="time-label">時間:</span>
              {['00:00', '06:00', '12:00', '18:00'].map(time => (
                <button
                  key={time}
                  onClick={() => handleTimeChange(time)}
                  className={`time-btn ${selectedTime === time ? 'time-btn-active' : ''}`}
                  title={time}
                >
                  {time}
                </button>
              ))}
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
                        e.target.src = 'https://placehold.co/400x250/e5e7eb/9ca3af?text=圖片載入失敗';
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
      </div>
    </div>
  );
}

export default YesterdayFocus;
