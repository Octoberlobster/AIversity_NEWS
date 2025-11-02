import React, { useMemo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';
import './../css/UnifiedNewsCard.css';
import UnifiedNewsCard from './UnifiedNewsCard';
import { useCategoryNews, useBatchNewsImages } from '../hooks/useCategoryNews';

function CategorySection({ country }) {
  const { t } = useTranslation();
  const { categoryName } = useParams();
  const ITEMS_PER_PAGE = 18;

  // 🎯 第一階段: 載入基本新聞資料 (文字內容)
  const { 
    data: basicNewsData = [], 
    isLoading,
    error 
  } = useCategoryNews(country, categoryName, ITEMS_PER_PAGE);

  // 提取所有 story_ids 用於載入圖片
  const storyIds = useMemo(() => {
    return basicNewsData.map(news => news.story_id);
  }, [basicNewsData]);

  // 🎯 第二階段: 背景載入圖片 (延遲執行)
  const { data: imagesData = {} } = useBatchNewsImages(storyIds);

  // 合併資料
  const newsData = useMemo(() => {
    return basicNewsData.map(news => ({
      ...news,
      imageUrl: imagesData[news.story_id] || '/api/placeholder/300/200',
      isImageLoading: !imagesData[news.story_id],
    }));
  }, [basicNewsData, imagesData]);

  // 生成標題
  const getPageTitle = useCallback(() => {
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
    const countryName = t(`header.countries.${country?.toLowerCase()}`);
    const newsWord = t('categorySection.news');
    
    if (categoryName) {
      const localCategory = categoryNameMap[categoryName] || categoryName;
      return `${countryName} - ${localCategory} ${newsWord}`;
    }
    return `${countryName} ${newsWord}`;
  }, [country, categoryName, t]);

  // 無國家
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

  // 載入中
  if (isLoading) {
    return (
      <section className="catSec">
        <div className="catSec__header">
          <h2 className="catSec__title">{getPageTitle()}</h2>
        </div>
        <div className="catSec__loading">{t('categorySection.loading')}</div>
      </section>
    );
  }

  // 錯誤
  if (error) {
    return (
      <section className="catSec">
        <div className="catSec__header">
          <h2 className="catSec__title">{getPageTitle()}</h2>
        </div>
        <div className="catSec__error">{t('categorySection.error.loadFailed')}</div>
      </section>
    );
  }

  // 無資料
  if (newsData.length === 0) {
    return (
      <section className="catSec">
        <div className="catSec__header">
          <h2 className="catSec__title">{getPageTitle()}</h2>
        </div>
        <div className="catSec__empty">
          {t('categorySection.empty.noNews', { category: getPageTitle() })}
        </div>
      </section>
    );
  }

  return (
    <section className="catSec">
      <div className="catSec__header">
        <h2 className="catSec__title">{getPageTitle()}</h2>
      </div>
      <div className="catSec__content">
        <UnifiedNewsCard 
          customData={newsData}
          limit={newsData.length} 
        />
      </div>
    </section>
  );
}

export default CategorySection;
