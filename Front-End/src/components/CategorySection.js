import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';
import './../css/UnifiedNewsCard.css';
import UnifiedNewsCard from './UnifiedNewsCard';
import { useSupabase } from './supabase';
import { imageCache } from './utils/cache';

function CategorySection({ country }) {
  const { t } = useTranslation();
  const { categoryName } = useParams(); // 從路由參數獲取類別名稱
  const [newsData, setNewsData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const supabaseClient = useSupabase();
  const ITEMS_PER_PAGE = 18;

  // 載入新聞 - 根據國家和類別篩選
  const loadInitialNews = useCallback(async () => {
    if (!supabaseClient || !country) return;

    // 對應資料庫的正確國家名稱
    const countryMap = {
      'Taiwan': 'Taiwan',
      'Japan': 'Japan',
      'Indonesia': 'Indonesia',
      'USA': 'United States of America',
      'United States of America': 'United States of America',
    };
    // 支援路由參數為 USA 但查詢時為 United States of America
    const dbCountry = countryMap[country] || country;

    console.log('開始載入新聞，國家:', dbCountry, '類別:', categoryName || '全部');

    try {
      setLoading(true);
      setError(null);

      // 構建 stories 表的查詢
      let storiesQuery = supabaseClient
        .from('stories')
        .select('story_id')
        .eq('country', dbCountry)
        .limit(5000);

      // 如果有指定類別，則加上類別篩選
      if (categoryName) {
        storiesQuery = storiesQuery.eq('category', categoryName);
      }

      const { data: storiesData, error: storiesError } = await storiesQuery;

      if (storiesError) {
        console.error('Error fetching stories:', storiesError);
        setError(t('categorySection.error.loadFailed'));
        return;
      }

      if (!storiesData || storiesData.length === 0) {
        console.log('No stories found for country:', dbCountry, 'category:', categoryName);
        setNewsData([]);
        return;
      }

      // 取得所有 story_id
      const storyIds = storiesData.map(story => story.story_id);
      console.log(`Found ${storyIds.length} stories for ${dbCountry}${categoryName ? '/' + categoryName : ''}`);

      // 分批查詢 single_news，避免 in 查詢超過 URL 長度限制
      const BATCH_SIZE = 200;
      let allNews = [];
      for (let i = 0; i < storyIds.length && allNews.length < ITEMS_PER_PAGE; i += BATCH_SIZE) {
        const batchIds = storyIds.slice(i, i + BATCH_SIZE);
        const { data: newsData, error: newsError } = await supabaseClient
          .from('single_news')
          .select('story_id, news_title, ultra_short, generated_date, category')
          .in('story_id', batchIds)
          .order('generated_date', { ascending: false });
        if (newsError) {
          console.error('Error fetching news:', newsError);
          setError(t('categorySection.error.loadFailed'));
          return;
        }
        if (newsData && newsData.length > 0) {
          allNews = allNews.concat(newsData);
        }
        if (allNews.length >= ITEMS_PER_PAGE) break;
      }
      // 只取前 ITEMS_PER_PAGE 筆
      allNews = allNews
        .sort((a, b) => new Date(b.generated_date) - new Date(a.generated_date))
        .slice(0, ITEMS_PER_PAGE);

      // 先建立初始資料（文字 + placeholder），快速顯示
      const cachedImages = {};
      const uncachedStoryIds = [];
      allNews.forEach(item => {
        const cached = imageCache.get(`image_${item.story_id}`);
        if (cached) cachedImages[item.story_id] = cached;
        else uncachedStoryIds.push(item.story_id);
      });

      const initialData = allNews.map(news => ({
        ...news,
        title: news.news_title,
        shortSummary: news.ultra_short,
        date: new Date(news.generated_date).toLocaleDateString('zh-TW'),
        imageUrl: cachedImages[news.story_id] || '/api/placeholder/300/200',
        isImageLoading: !cachedImages[news.story_id]
      }));

      // 立即顯示文字與 placeholder
      setNewsData(initialData);

      // 背景分批載入未快取的圖片（並行小批次），載入後逐筆更新 state
      if (uncachedStoryIds.length > 0) {
        const CONCURRENT_LIMIT = 3; // 每次並行請求數
        const DELAY_BETWEEN_BATCHES = 0;

        for (let i = 0; i < uncachedStoryIds.length; i += CONCURRENT_LIMIT) {
          const batch = uncachedStoryIds.slice(i, i + CONCURRENT_LIMIT);

          const promises = batch.map(storyId =>
            supabaseClient
              .from('generated_image')
              .select('story_id, image')
              .eq('story_id', storyId)
              .single()
              .then(result => ({ result }))
              .catch(error => ({ error, storyId }))
          );

          const results = await Promise.all(promises);

          results.forEach(r => {
            if (r.result && r.result.data && r.result.data.image) {
              const imageItem = r.result.data;
              try {
                const cleanBase64 = imageItem.image.replace(/\s/g, '');
                const imageUrl = `data:image/png;base64,${cleanBase64}`;
                imageCache.set(`image_${imageItem.story_id}`, imageUrl);

                // 逐筆更新新聞資料的圖片
                setNewsData(prev => prev.map(n => n.story_id === imageItem.story_id ? { ...n, imageUrl, isImageLoading: false } : n));
              } catch (e) {
                console.error('Invalid image data for story', imageItem.story_id, e);
              }
            } else {
              // error handling
              if (r.error) console.error('Error fetching image:', r.error, r.storyId);
            }
          });

          if (i + CONCURRENT_LIMIT < uncachedStoryIds.length) {
            await new Promise(resolve => setTimeout(resolve, DELAY_BETWEEN_BATCHES));
          }
        }
      }

    } catch (err) {
      console.error('Error in loadInitialNews:', err);
      setError(t('categorySection.error.loadError'));
    } finally {
      setLoading(false);
    }
  }, [country, categoryName, supabaseClient, t]);



  // 初始載入效果
  useEffect(() => {
    loadInitialNews();
  }, [loadInitialNews]);

  // 生成標題
  const getPageTitle = useCallback(() => {
    // 類別英文對應本地化 key
    const categoryNameMap = {
      'Politics': t('header.menu.politics'),
      'International News': t('header.menu.international'),
      'Science & Technology': t('header.menu.scienceAndTech'),
      'Lifestyle & Consumer': t('header.menu.life'),
      'Sports': t('header.menu.sports'),
      'Entertainment': t('header.menu.entertainment'),
      'Business & Finance': t('header.menu.finance'),
      'Health & Wellness': t('header.menu.health'),
    };
    const countryName = t(`header.countries.${country.toLowerCase()}`);
    const newsWord = t('categorySection.news'); // i18n: 新聞
    if (categoryName) {
      // 若有對應本地化，顯示本地化類別
      const localCategory = categoryNameMap[categoryName] || categoryName;
      return `${countryName} - ${localCategory} ${newsWord}`;
    }
    return `${countryName} ${newsWord}`;
  }, [country, categoryName, t]);

  if (!country) {
    return (
      <section className="catSec">
        <div className="catSec__header">
          <h2 className="catSec__title">{t('categorySection.title')}</h2>
        </div>
        <div className="catSec__empty">{t('categorySection.empty.categoryNotFound')}</div>
      </section>
    );
  }

  if (loading) {
    return (
      <section className="catSec">
        <div className="catSec__header">
          <h2 className="catSec__title">{getPageTitle()}</h2>
        </div>
        <div className="catSec__loading">{t('categorySection.loading')}</div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="catSec">
        <div className="catSec__header">
          <h2 className="catSec__title">{getPageTitle()}</h2>
        </div>
        <div className="catSec__error">{error}</div>
      </section>
    );
  }

  // 資料已經處理完成，包含圖片
  console.log('Final news data for UnifiedNewsCard:', newsData);

  return (
    <section className="catSec">
      <div className="catSec__header">
        <h2 className="catSec__title">{getPageTitle()}</h2>
      </div>

      {newsData.length === 0 ? (
        <div className="catSec__empty">
          {t('categorySection.empty.noNews', { category: getPageTitle() })}
        </div>
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