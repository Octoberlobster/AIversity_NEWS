import React, { useState, useEffect, useCallback } from 'react';
import './../css/UnifiedNewsCard.css';
import UnifiedNewsCard from './UnifiedNewsCard';
import { useSupabase } from './supabase';
import { imageCache } from './utils/cache';

function AbroadNewsPage() {
  const [newsData, setNewsData] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCountry, setSelectedCountry] = useState('all');
  const [availableCountries, setAvailableCountries] = useState([]);
  const supabaseClient = useSupabase();
  
  const ITEMS_PER_PAGE = 18;

  // 獲取可用的國家列表 - 先從 stories 表獲取非 Taiwan 的資料
  const loadAvailableCountries = useCallback(async () => {
    if (!supabaseClient) return;

    try {
      console.log('第一步：從 stories 表獲取非 Taiwan 的國家...');
      
      // 從 stories 表獲取 country 不等於 Taiwan 的資料
      const { data: storiesData, error: storiesError } = await supabaseClient
        .from('stories')
        .select('country')
        .not('country', 'is', null)
        .neq('country', 'Taiwan')
        .neq('country', 'taiwan')
        .limit(10000);

      if (storiesError) {
        console.error('Error fetching countries from stories:', storiesError);
        return;
      }

      console.log(`從 stories 表獲取到 ${storiesData.length} 筆國家資料`);
      
      // 提取所有唯一的國家列表
      const allCountries = [...new Set(storiesData.map(item => item.country).filter(Boolean))];
      console.log('從 stories 表中提取的所有唯一國家:', allCountries);
      console.log(`共有 ${allCountries.length} 個不同的國家`);
      
      setAvailableCountries(allCountries.sort());
      
    } catch (err) {
      console.error('Error in loadAvailableCountries:', err);
    }
  }, [supabaseClient]);

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
    if (!supabaseClient) return;

    try {
      setLoading(true);
      setError(null);

      console.log('Loading initial news for country:', selectedCountry);

      // 第一步：從 stories 表獲取非 Taiwan 的 story_id
      console.log('第一步：從 stories 表獲取非 Taiwan 的 story_id...');
      
      let storiesQuery = supabaseClient
        .from('stories')
        .select('story_id, country')
        .not('country', 'is', null)
        .neq('country', 'Taiwan')
        .neq('country', 'taiwan')
        .order('crawl_date', { ascending: false })
        .limit(ITEMS_PER_PAGE * 3);

      // 如果選擇了特定國家，則過濾
      if (selectedCountry !== 'all') {
        storiesQuery = storiesQuery.eq('country', selectedCountry);
      }

      const { data: storiesData, error: storiesError } = await storiesQuery;

      if (storiesError) {
        console.error('Error fetching stories:', storiesError);
        setError('無法載入故事資料');
        return;
      }

      if (!storiesData || storiesData.length === 0) {
        console.log('No stories found for country:', selectedCountry);
        setNewsData([]);
        setHasMore(false);
        return;
      }

      console.log(`獲取到 ${storiesData.length} 個非 Taiwan 的 story_id`);
      console.log('stories 資料:', storiesData.slice(0, 3)); // 顯示前3個

      // 第二步：用這些 story_id 去查詢 single_news
      const storyIds = storiesData.map(story => story.story_id);
      console.log('第二步：用 story_id 查詢 single_news...');

      const { data: newsData, error: newsError } = await supabaseClient
        .from('single_news')
        .select(`
          story_id, 
          news_title, 
          ultra_short, 
          generated_date, 
          category
        `)
        .in('story_id', storyIds)
        .order('generated_date', { ascending: false })
        .limit(ITEMS_PER_PAGE);

      // 將國家資訊合併到新聞資料中
      const newsWithCountry = newsData?.map(news => {
        const story = storiesData.find(s => s.story_id === news.story_id);
        return {
          ...news,
          stories: { country: story?.country }
        };
      }) || [];

      console.log('查詢到的原始新聞資料:', newsData);
      console.log('合併後的新聞資料:', newsWithCountry);

      if (newsError) {
        console.error('Error fetching news:', newsError);
        setError('無法載入新聞資料');
        return;
      }

      if (!newsWithCountry || newsWithCountry.length === 0) {
        console.log('No news found for country:', selectedCountry);
        setNewsData([]);
        setHasMore(false);
        return;
      }

      // 檢查新聞資料結構
      if (newsWithCountry && newsWithCountry.length > 0) {
        console.log('第一筆新聞的結構:', newsWithCountry[0]);
        console.log('stories 欄位:', newsWithCountry[0].stories);
        
        // 檢查新聞資料中所有的國家
        const newsCountries = [...new Set(newsWithCountry.map(news => news.stories?.country).filter(Boolean))];
        console.log('新聞資料中的所有國家:', newsCountries);
        console.log('新聞資料中的國家數量:', newsCountries.length);
      }

      // 載入這一頁的圖片
      const enhancedData = await loadImagesForNews(newsWithCountry);
      
      setNewsData(enhancedData);
      setCurrentPage(1);
      setHasMore(storiesData.length > ITEMS_PER_PAGE);
      
    } catch (err) {
      console.error('Error in loadInitialNews:', err);
      setError('載入新聞時發生錯誤');
    } finally {
      setLoading(false);
    }
  }, [selectedCountry, supabaseClient, loadImagesForNews]);

  // 載入更多新聞
  const loadMoreNews = useCallback(async () => {
    if (!supabaseClient || isLoadingMore || !hasMore) return;

    try {
      setIsLoadingMore(true);
      
      const nextPage = currentPage + 1;
      const offset = (nextPage - 1) * ITEMS_PER_PAGE;

      console.log(`Loading page ${nextPage} for country:`, selectedCountry);

      // 建立查詢，排除 taiwan 新聞
      let query = supabaseClient
        .from('single_news')
        .select(`
          story_id, 
          news_title, 
          ultra_short, 
          generated_date, 
          category,
          stories!inner(country)
        `)
        .not('stories.country', 'ilike', '%taiwan%') // 排除所有包含 taiwan 的國家
        .order('generated_date', { ascending: false })
        .range(offset, offset + ITEMS_PER_PAGE - 1);

      // 如果選擇了特定國家，則過濾
      if (selectedCountry !== 'all') {
        query = query.eq('stories.country', selectedCountry);
      }

      const { data: newNewsData, error: newsError } = await query;

      if (newsError) {
        console.error('Error fetching more news:', newsError);
        return;
      }

      if (!newNewsData || newNewsData.length === 0) {
        setHasMore(false);
        return;
      }

      // 載入這一頁的圖片（taiwan 已在資料庫查詢中排除）
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
  }, [selectedCountry, supabaseClient, isLoadingMore, hasMore, currentPage, loadImagesForNews]);

  // 初始載入效果
  useEffect(() => {
    loadAvailableCountries();
  }, [loadAvailableCountries]);

  // 當選擇的國家改變時重新載入新聞
  useEffect(() => {
    if (availableCountries.length > 0) {
      loadInitialNews();
    }
  }, [selectedCountry, loadInitialNews, availableCountries.length]);

  if (loading) {
    return (
      <section className="catSec">
        <div className="catSec__header" style={{ marginBottom: '30px' }}>
          <h2 className="catSec__title">國外新聞</h2>
        </div>
        <div className="catSec__loading">載入中...</div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="catSec">
        <div className="catSec__header" style={{ marginBottom: '30px' }}>
          <h2 className="catSec__title">國外新聞</h2>
        </div>
        <div className="catSec__error">{error}</div>
      </section>
    );
  }

  // 國家選擇處理函數
  const handleCountryChange = (event) => {
    setSelectedCountry(event.target.value);
  };

  // 獲取國家的中文名稱
  const getCountryDisplayName = (country) => {
    const countryNames = {
      'United States of America': '美國',
      'Japan': '日本',
      'Korea': '韓國',
      'France': '法國',
      'Germany': '德國',
      'Vietnam': '越南',
      'Philippines': '菲律賓',
      'Indonesia': '印尼',
      'Spain': '西班牙',
    };
    return countryNames[country] || country;
  };

  return (
    <section className="catSec">
      <div className="catSec__header" style={{ marginBottom: '30px' }}>
        <h2 className="catSec__title" style={{ marginBottom: '25px' }}>國外新聞</h2>
        
        {/* 國家選擇器 */}
        <div className="country-selector" style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '15px',
          padding: '15px 20px',
          backgroundColor: '#f8f9fa',
          borderRadius: '10px',
          border: '1px solid #e9ecef'
        }}>
          <label htmlFor="country-select" style={{ 
            fontSize: '16px', 
            fontWeight: '600',
            color: '#495057',
            minWidth: '80px'
          }}>
            選擇國家：
          </label>
          <select 
            id="country-select"
            value={selectedCountry} 
            onChange={handleCountryChange}
            style={{
              padding: '10px 15px',
              fontSize: '16px',
              border: '2px solid #dee2e6',
              borderRadius: '8px',
              backgroundColor: 'white',
              cursor: 'pointer',
              minWidth: '150px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              transition: 'border-color 0.2s ease'
            }}
            onFocus={(e) => e.target.style.borderColor = '#007bff'}
            onBlur={(e) => e.target.style.borderColor = '#dee2e6'}
          >
            <option value="all">所有國家</option>
            {availableCountries.map(country => (
              <option key={country} value={country}>
                {getCountryDisplayName(country)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {newsData.length === 0 ? (
        <div className="catSec__empty">
          目前沒有{selectedCountry === 'all' ? '國外' : getCountryDisplayName(selectedCountry)}新聞
        </div>
      ) : (
        <div className="catSec__content">
          <UnifiedNewsCard 
            customData={newsData}
            limit={newsData.length} 
          />
          
          {/* 載入更多按鈕 */}
          {hasMore && (
            <div style={{ textAlign: 'center', marginTop: '30px' }}>
              <button
                onClick={loadMoreNews}
                disabled={isLoadingMore}
                style={{
                  padding: '12px 24px',
                  fontSize: '16px',
                  backgroundColor: '#007bff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: isLoadingMore ? 'not-allowed' : 'pointer',
                  opacity: isLoadingMore ? 0.6 : 1
                }}
              >
                {isLoadingMore ? '載入中...' : '載入更多'}
              </button>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

export default AbroadNewsPage;