import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import './../css/UnifiedNewsCard.css';
import UnifiedNewsCard from './UnifiedNewsCard';
import { useSupabase } from './supabase';
import { imageCache } from './utils/cache';

function CategorySection({ category }) {
  const { t } = useTranslation();

  // 基礎分類配置 (語言無關)
  const categoryConfigs = useMemo(() => ({
    'politics': { id: 'Politics', color: '#ef4444' },
    'taiwan': { id: 'Taiwan News', color: '#10b981' },
    'scienceAndTech': { id: 'Science & Technology', color: '#8b5cf6' },
    'international': { id: 'International News', color: '#f59e0b' },
    'life': { id: 'Lifestyle & Consumer', color: '#06b6d4' },
    'sports': { id: 'Sports', color: '#059669' },
    'entertainment': { id: 'Entertainment', color: '#ec4899' },
    'finance': { id: 'Business & Finance', color: '#10b981' },
    'health': { id: 'Health & Wellness', color: '#ef4444' }
  }), []);

  // 智能分類匹配 - 根據輸入找到對應的 key
  const findCategoryKey = useCallback((inputCategory) => {
    console.log('Finding category key for input:', inputCategory);
    
    // 建立所有可能的翻譯對照表（包含中文和英文）
    const allTranslations = {};
    for (const [key] of Object.entries(categoryConfigs)) {
      // 取得中文翻譯（假設 zh-TW 中的翻譯）
      const zhTranslations = {
        'politics': '政治',
        'taiwan': '台灣',
        'scienceAndTech': '科學與科技', 
        'international': '國際',
        'life': '生活',
        'sports': '體育',
        'entertainment': '娛樂',
        'finance': '商業財經',
        'health': '健康'
      };
      
      // 當前語言的翻譯
      const currentTranslation = t(`categorySection.categories.${key}`);
      const zhTranslation = zhTranslations[key];
      
      allTranslations[key] = {
        current: currentTranslation,
        zh: zhTranslation,
        dbId: categoryConfigs[key].id
      };
      
      console.log(`Key: ${key}, Current: ${currentTranslation}, ZH: ${zhTranslation}, DB: ${categoryConfigs[key].id}`);
    }
    
    // 嘗試匹配：當前語言翻譯、中文翻譯、或數據庫 ID
    for (const [key, translations] of Object.entries(allTranslations)) {
      if (translations.current === inputCategory || 
          translations.zh === inputCategory || 
          translations.dbId === inputCategory) {
        console.log(`✓ Found match: ${key} (matched: ${inputCategory})`);
        return key;
      }
    }
    
    console.log('❌ No match found for:', inputCategory);
    return null; // 找不到匹配
  }, [categoryConfigs, t]);

  const categoryKey = useMemo(() => findCategoryKey(category), [category, findCategoryKey]);
  
  const currentCategory = useMemo(() => {
    return categoryKey ? {
      ...categoryConfigs[categoryKey],
      key: categoryKey,
      translatedName: t(`categorySection.categories.${categoryKey}`)
    } : null;
  }, [categoryKey, categoryConfigs, t]);
  const [newsData, setNewsData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const supabaseClient = useSupabase();
  const ITEMS_PER_PAGE = 18;

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
    if (!currentCategory || !supabaseClient) return;

    try {
      setLoading(true);
      setError(null);

      console.log('Loading initial news for category:', currentCategory.id);

      // 查詢第一頁新聞
      const { data: newsData, error: newsError } = await supabaseClient
        .from('single_news')
        .select('story_id, news_title, ultra_short, generated_date, category')
        .eq('category', currentCategory.id)
        .order('generated_date', { ascending: false })
        .limit(ITEMS_PER_PAGE);

      if (newsError) {
        console.error('Error fetching news:', newsError);
        setError(t('categorySection.error.loadFailed'));
        return;
      }

      if (!newsData || newsData.length === 0) {
        console.log('No news found for category:', currentCategory.id);
        setNewsData([]);
        return;
      }

      // 載入這一頁的圖片
      const enhancedData = await loadImagesForNews(newsData);
      
      setNewsData(enhancedData);
      
    } catch (err) {
      console.error('Error in loadInitialNews:', err);
      setError(t('categorySection.error.loadError'));
    } finally {
      setLoading(false);
    }
  }, [currentCategory, supabaseClient, loadImagesForNews, t]);



  // 初始載入效果
  useEffect(() => {
    loadInitialNews();
  }, [loadInitialNews]);

  if (!currentCategory) {
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
          <h2 className="catSec__title">
            {currentCategory 
              ? t('categorySection.newsTitle', { category: currentCategory.translatedName })
              : t('categorySection.newsTitle', { category })
            }
          </h2>
        </div>
        <div className="catSec__loading">{t('categorySection.loading')}</div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="catSec">
        <div className="catSec__header">
          <h2 className="catSec__title">
            {currentCategory 
              ? t('categorySection.newsTitle', { category: currentCategory.translatedName })
              : t('categorySection.newsTitle', { category })
            }
          </h2>
        </div>
        <div className="catSec__error">{error}</div>
      </section>
    );
  }

  // 資料已經在 fetchCategoryNews 中處理完成，包含圖片
  console.log('Final news data for UnifiedNewsCard:', newsData);

  return (
    <section className="catSec">
      <div className="catSec__header">
        <h2 className="catSec__title">
          {currentCategory 
            ? t('categorySection.newsTitle', { category: currentCategory.translatedName })
            : t('categorySection.newsTitle', { category })
          }
        </h2>
      </div>

      {newsData.length === 0 ? (
        <div className="catSec__empty">
          {currentCategory 
            ? t('categorySection.empty.noNews', { category: currentCategory.translatedName })
            : t('categorySection.empty.noNews', { category })
          }
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