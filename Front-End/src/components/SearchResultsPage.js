import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import UnifiedNewsCard from './UnifiedNewsCard';
import FloatingChat from './FloatingChat';
import { searchNews, fetchNewsDataFromSupabase } from './api';
import { useSupabase } from './supabase';
import './../css/SearchResultsPage.css';

function SearchResultsPage() {
  const { query } = useParams();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const supabaseClient = useSupabase();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [searchInfo, setSearchInfo] = useState(null);
  const [showAllNews, setShowAllNews] = useState(false);

  useEffect(() => {
    const performSearch = async () => {
      if (!query || query.trim() === '') {
        setError(t('searchResult.error.emptyQuery'));
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        console.log('開始搜尋:', query);
        console.log('Supabase client 狀態:', !!supabaseClient);
        
        // 1. 調用 Advanced_Search_Service API
        const searchResponse = await searchNews(query);
        console.log('搜尋 API 回應:', searchResponse);
        
        // 檢查 API 回應是否有效
        if (!searchResponse) {
          throw new Error(t('searchResult.error.noResponse'));
        }
        
        // 設置搜尋資訊
        setSearchInfo({
          query: searchResponse.query || query,
          keywords: searchResponse.keywords || [],
          count: searchResponse.count || 0
        });

        if (searchResponse.story_ids && Array.isArray(searchResponse.story_ids) && searchResponse.story_ids.length > 0) {
          console.log('準備從 Supabase 獲取 story_ids:', searchResponse.story_ids);
          // 2. 根據 story_ids 從 Supabase 獲取完整新聞資料
          const newsData = await fetchNewsDataFromSupabase(supabaseClient, searchResponse.story_ids);
          console.log('從 Supabase 獲取的新聞資料:', newsData);
          console.log('第一筆新聞資料結構:', newsData[0]);
          
          // 3. 按照時間排序 (最新的在前面)
          const sortedNews = newsData.sort((a, b) => {
            const dateA = new Date(a.date || a.generated_date);
            const dateB = new Date(b.date || b.generated_date);
            return dateB - dateA; // 降序排列 (最新的在前)
          });
          
          console.log('排序後的新聞:', sortedNews.slice(0, 3).map(n => ({ title: n.title, date: n.date })));
          setSearchResults(sortedNews);
        } else {
          console.log('沒有找到 story_ids 或為空陣列');
          setSearchResults([]);
        }

      } catch (err) {
        console.error('搜尋錯誤:', err);
        setError(err.message || t('searchResult.error.general'));
      } finally {
        setLoading(false);
      }
    };

    performSearch();
  }, [query, supabaseClient, t]);

  if (loading) {
    return (
      <div className="searchPage">
        <main className="searchPage__main">
          <div className="searchPage__loading">
            <div className="loadingSpinner"></div>
            <p>{t('searchResult.loading.text')}</p>
          </div>
        </main>
        <FloatingChat />
      </div>
    );
  }

  if (error) {
    return (
      <div className="searchPage">
        <main className="searchPage__main">
          <div className="searchPage__error">
            <h2>{t('searchResult.error.title')}</h2>
            <p>{error}</p>
            <button 
              className="searchPage__backBtn"
              onClick={() => navigate('/')}
            >
              {t('searchResult.error.backToHome')}
            </button>
          </div>
        </main>
        <FloatingChat />
      </div>
    );
  }

  return (
    <div className="searchPage">
      <main className="searchPage__main">
        <div className="searchPage__grid">
          <div className="searchPage__mainCol">
            <div className="searchPage__header">
              <h2 className="searchPage__sectionTitle">
                {t('searchResult.header.title', { query })}
              </h2>
              {searchInfo && searchInfo.keywords && searchInfo.keywords.length > 0 && (
                <div className="searchPage__keywords">
                  <span>{t('searchResult.header.keywords')}</span>
                  {searchInfo.keywords.map((keyword, index) => (
                    <span key={index} className="searchPage__keyword">
                      {keyword}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {searchResults.length === 0 ? (
              <div className="searchPage__noResults">
                <h3>{t('searchResult.noResults.title')}</h3>
                <p>{t('searchResult.noResults.suggestion')}</p>
              </div>
            ) : (
              <>
                <UnifiedNewsCard 
                  customData={showAllNews ? searchResults : searchResults.slice(0, 12)}
                  instanceId={`search_${query}`}
                />

                {!showAllNews && searchResults.length > 12 && (
                  <div className="searchPage__moreWrap">
                    <button
                      className="searchPage__moreBtn"
                      onClick={() => setShowAllNews(true)}
                    >
                      {t('searchResult.moreButton.text', { count: searchResults.length - 12 })}
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </main>
      <FloatingChat />
    </div>
  );
}

export default SearchResultsPage;
