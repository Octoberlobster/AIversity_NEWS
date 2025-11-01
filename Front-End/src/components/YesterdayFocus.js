import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useCountry } from './CountryContext';
import { useSupabase } from './supabase';
import '../css/YesterdayFocus.css';

function YesterdayFocus() {
  const { selectedCountry } = useCountry();
  const supabase = useSupabase();
  const navigate = useNavigate();
  const location = useLocation();
  const [newsData, setNewsData] = useState([]);

  // 獲取當前語言
  const currentLang = location.pathname.split('/')[1] || 'zh-TW';

  // 國家 ID 對應到顯示名稱
  const countryMap = {
    'taiwan': '臺灣',
    'usa': '美國',
    'japan': '日本',
    'indonesia': '印尼'
  };

  const currentCountryLabel = countryMap[selectedCountry] || '台灣';

  // 國家 ID 對應到資料庫的 country 值
  const countryDbMap = {
    'taiwan': 'Taiwan',
    'usa': 'United States of America',
    'japan': 'Japan',
    'indonesia': 'Indonesia'
  };

  const currentCountryDbName = countryDbMap[selectedCountry] || 'Taiwan';

  // 處理新聞點擊
  const handleNewsClick = (storyId) => {
    navigate(`/${currentLang}/news/${storyId}`);
  };

  // 計算昨天的日期（格式：YYYY-MM-DD）
  useEffect(() => {
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    // 格式化為 YYYY-MM-DD
    const year = yesterday.getFullYear();
    const month = String(yesterday.getMonth() + 1).padStart(2, '0');
    const day = String(yesterday.getDate()).padStart(2, '0');
    const yesterdayDate = `${year}-${month}-${day}`;

    console.log('昨天的日期:', yesterdayDate);
    console.log('當前選擇的國家:', selectedCountry);

    // 從 top_ten_news 表拉取資料
    const fetchYesterdayNews = async () => {
      try {
        const { data, error } = await supabase
          .from('top_ten_news')
          .select('*')
          .eq('country', currentCountryDbName)
          .eq('date', yesterdayDate);

        if (error) {
          console.error('拉取資料錯誤:', error);
        } else {
          console.log('拉取到的資料:', data);
          
          // 解析 top_ten_news_id JSON 格式並拉取相關新聞資料
          if (data && data.length > 0) {
            const newsPromises = data.map(async (item, index) => {
              try {
                // 解析 top_ten_news_id JSON
                const parsedJson = typeof item.top_ten_news_id === 'string' 
                  ? JSON.parse(item.top_ten_news_id) 
                  : item.top_ten_news_id;
                
                const storyIds = parsedJson.top_ten_story_ids;
                console.log(`資料 ${index + 1} 的 story_id 陣列:`, storyIds);

                // 為每個 story_id 拉取新聞資料
                const newsDetailsPromises = storyIds.map(async (storyId) => {
                  try {
                    // 並行拉取三個表的資料
                    const [singleNewsRes, imageRes, cleanedNewsRes] = await Promise.all([
                      // 從 single_news 拉 news_title 和 short
                      supabase
                        .from('single_news')
                        .select('story_id, news_title, short')
                        .eq('story_id', storyId),
                      
                      // 從 generated_image 拉 image
                      supabase
                        .from('generated_image')
                        .select('story_id, image, description')
                        .eq('story_id', storyId),
                      
                      // 從 cleaned_news 拉 article_title、article_url 和 media
                      supabase
                        .from('cleaned_news')
                        .select('story_id, article_title, article_url, media')
                        .eq('story_id', storyId)
                    ]);

                    if (singleNewsRes.data && singleNewsRes.data.length > 0) {
                      const newsItem = singleNewsRes.data[0];
                      const newsTitle = newsItem.news_title;
                      const summary = newsItem.short;
                      
                      // 處理圖片 - base64
                      let imageUrl = null;
                      if (imageRes.data && imageRes.data.length > 0 && imageRes.data[0].image) {
                        const cleanBase64 = imageRes.data[0].image.replace(/\s/g, '');
                        imageUrl = `data:image/png;base64,${cleanBase64}`;
                      }
                      
                      // 拉取相關來源 (cleaned_news)
                      const relatedSources = cleanedNewsRes.data && cleanedNewsRes.data.length > 0
                        ? cleanedNewsRes.data.map((news, idx) => ({
                            id: idx + 1,
                            media: news.media || new URL(news.article_url).hostname.replace('www.', ''),
                            name: news.article_title,
                            url: news.article_url
                          }))
                        : [];

                      return {
                        id: storyId,
                        title: newsTitle,
                        summary: summary,
                        image: imageUrl || 'https://placehold.co/400x250/e5e7eb/9ca3af?text=圖片載入失敗',
                        date: item.date,
                        relatedSources: relatedSources
                      };
                    }
                  } catch (err) {
                    console.error(`拉取 story_id ${storyId} 的資料失敗:`, err);
                    return null;
                  }
                });

                const newsDetails = (await Promise.all(newsDetailsPromises)).filter(Boolean);
                return newsDetails;
              } catch (parseErr) {
                console.error(`解析第 ${index + 1} 筆資料失敗:`, parseErr);
                return [];
              }
            });

            const allNews = (await Promise.all(newsPromises)).flat();
            console.log('最終拉取的新聞資料:', allNews);
            setNewsData(allNews);
          } else {
            setNewsData([]);
          }
        }
      } catch (err) {
        console.error('查詢失敗:', err);
      }
    };

    fetchYesterdayNews();
  }, [selectedCountry, currentCountryDbName, supabase]);

  return (
    <div className="yesterday-focus-container">
      <div className="focus-wrapper">
        <h1 className="yesterday-title">
          {currentCountryLabel}昨日焦點
        </h1>

        <div className="news-cards-list">
          {newsData.map(news => (
            <div key={news.id} className="news-card-container">
              {/* 左側：新聞內容 */}
              <div className="card-main">
                <h3 
                  className="card-title" 
                  onClick={() => handleNewsClick(news.id)}
                  style={{ cursor: 'pointer' }}
                >
                  {news.title}
                </h3>
                <div 
                  className="card-image"
                  onClick={() => handleNewsClick(news.id)}
                  style={{ cursor: 'pointer' }}
                >
                  <img 
                    src={news.image} 
                    alt={news.title}
                    onError={(e) => {
                      e.target.src = 'https://placehold.co/400x250/e5e7eb/9ca3af?text=圖片載入失敗';
                    }}
                  />
                </div>
                <div className="card-content">
                  <p className="card-summary">{news.summary}</p>
                </div>
              </div>

              {/* 右側：相關來源側邊欄 */}
              <div className="card-sidebar">
                <h4 className="sidebar-title">相關來源</h4>
                <div className="sources-list">
                  {news.relatedSources && news.relatedSources.slice(0, 6).map(source => (
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
                  {news.relatedSources && news.relatedSources.length > 6 && (
                    <div className="source-more">
                      <span>...</span>
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
