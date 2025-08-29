import React, { useState, useEffect } from 'react';
import './../css/UnifiedNewsCard.css';
import UnifiedNewsCard from './UnifiedNewsCard';
import { useSupabase } from './supabase';

// 分類配置
const categories = {
  '政治': { id: 'Politics', name: '政治', color: '#ef4444' },
  '台灣': { id: 'Taiwan News', name: '台灣', color: '#10b981' },
  '科學與科技': { id: 'Science & Technology', name: '科學與科技', color: '#8b5cf6' },
  '國際': { id: 'International News', name: '國際', color: '#f59e0b' },
  '生活': { id: 'Lifestyle & Consumer', name: '生活', color: '#06b6d4' },
  '體育': { id: 'Sports', name: '體育', color: '#059669' },
  '娛樂': { id: 'Entertainment', name: '娛樂', color: '#ec4899' },
  '商業財經': { id: 'Business & Finance', name: '商業財經', color: '#10b981' },
  '健康': { id: 'Health & Wellness', name: '健康', color: '#ef4444' }
};

function CategorySection({ category }) {
  const [showAllNews, setShowAllNews] = useState(false);
  const [newsData, setNewsData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const supabaseClient = useSupabase();
  
  const currentCategory = categories[category];

  // 從資料庫獲取該分類的新聞
  useEffect(() => {
    const fetchCategoryNews = async () => {
      if (!currentCategory || !supabaseClient) return;

      try {
        setLoading(true);
        setError(null);

        const { data, error } = await supabaseClient
          .from('single_news')
          .select('*')
          .eq('category', currentCategory.id)
          .order('generated_date', { ascending: false });

        if (error) {
          console.error('Error fetching category news:', error);
          setError('無法載入新聞資料');
          setNewsData([]);
        } else {
          setNewsData(data || []);
        }
      } catch (err) {
        console.error('Unexpected error:', err);
        setError('載入新聞時發生錯誤');
        setNewsData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchCategoryNews();
  }, [currentCategory, supabaseClient]);

  if (!currentCategory) {
    return (
      <section className="catSec">
        <div className="catSec__header">
          <h2 className="catSec__title">分類新聞</h2>
        </div>
        <div className="catSec__empty">找不到該分類的新聞</div>
      </section>
    );
  }

  if (loading) {
    return (
      <section className="catSec">
        <div className="catSec__header">
          <h2 className="catSec__title">{category}新聞</h2>
        </div>
        <div className="catSec__loading">載入中...</div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="catSec">
        <div className="catSec__header">
          <h2 className="catSec__title">{category}新聞</h2>
        </div>
        <div className="catSec__error">{error}</div>
      </section>
    );
  }

  // 轉成 UnifiedNewsCard 所需格式
  const convertedNewsData = newsData.map((news, index) => ({
    story_id: news.story_id,
    title: news.news_title,
    category: currentCategory.name,
    date: news.generated_date,
    author: 'Gemini',
    sourceCount: news.total_articles,
    shortSummary: news.ultra_short,
    relatedNews: [],
    views: 0,
    keywords: [],
    terms: [],
  }));

  const displayLimit = showAllNews ? undefined : 12;

  return (
    <section className="catSec">
      <div className="catSec__header">
        <h2 className="catSec__title">
          {category}新聞
        </h2>
      </div>

      {newsData.length === 0 ? (
        <div className="catSec__empty">目前沒有 {category} 相關的新聞</div>
      ) : (
        <>
          <UnifiedNewsCard 
            limit={displayLimit} 
            customData={convertedNewsData}
            instanceId={`category_${currentCategory?.id || 'unknown'}`}
          />

          {!showAllNews && newsData.length > 12 && (
            <div className="catSec__moreWrap">
              <button className="btnPrimary" onClick={() => setShowAllNews(true)}>
                閱讀更多新聞 ({newsData.length - 12} 篇)
              </button>
            </div>
          )}
        </>
      )}
    </section>
  );
}

export default CategorySection;