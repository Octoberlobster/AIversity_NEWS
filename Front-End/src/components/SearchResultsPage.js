import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import UnifiedNewsCard from './UnifiedNewsCard';
import FloatingChat from './FloatingChat';
import { searchNews, fetchNewsDataFromSupabase } from './api';
import { useSupabase } from './supabase';
import './../css/SearchResultsPage.css';

function SearchResultsPage() {
  const { query } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();
  const supabaseClient = useSupabase();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [rawNewsData, setRawNewsData] = useState([]); // 儲存原始資料(包含所有語言)
  const [searchInfo, setSearchInfo] = useState(null);
  const [showAllNews, setShowAllNews] = useState(false);
  
  // 追蹤上次搜尋的 query,避免重複搜尋
  const lastQueryRef = useRef(null);

  // 獲取當前語言
  const currentLang = location.pathname.split('/')[1] || 'zh-TW';

  // 只在 query 改變時調用 API
  useEffect(() => {
    const performSearch = async () => {
      if (!query || query.trim() === '') {
        setError(t('searchResult.error.emptyQuery'));
        setLoading(false);
        return;
      }

      // 如果是同一個 query,不重新搜尋
      if (lastQueryRef.current === query) {
        console.log('相同的搜尋關鍵字,跳過 API 調用');
        return;
      }

      console.log('新的搜尋關鍵字:', query, '(上次:', lastQueryRef.current, ')');
      lastQueryRef.current = query;

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
          throw new Error(t('searchResult.error.emptyQuery'));
        }
        
        // 設置搜尋資訊
        setSearchInfo({
          query: searchResponse.query || query,
          keywords: searchResponse.keywords || [],
          count: searchResponse.count || 0
        });

        if (searchResponse.story_ids && Array.isArray(searchResponse.story_ids) && searchResponse.story_ids.length > 0) {
          console.log('準備從 Supabase 獲取 story_ids:', searchResponse.story_ids);
          // 2. 根據 story_ids 從 Supabase 獲取完整新聞資料(包含所有語言欄位)
          const newsData = await fetchNewsDataFromSupabase(supabaseClient, searchResponse.story_ids);
          console.log('從 Supabase 獲取的新聞資料:', newsData);
          
          // 3. 按照時間排序 (最新的在前面)
          const sortedNews = newsData.sort((a, b) => {
            const dateA = new Date(a.date || a.generated_date);
            const dateB = new Date(b.date || b.generated_date);
            return dateB - dateA; // 降序排列 (最新的在前)
          });
          
          console.log('排序後的新聞:', sortedNews.slice(0, 3).map(n => ({ title: n.news_title, date: n.date })));
          setRawNewsData(sortedNews); // 儲存原始資料
        } else {
          console.log('沒有找到 story_ids 或為空陣列');
          setRawNewsData([]);
        }

      } catch (err) {
        console.error('搜尋錯誤:', err);
        setError(err.message || t('searchResult.error.general'));
      } finally {
        setLoading(false);
      }
    };

    performSearch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, supabaseClient]); // 只監聽 query 和 supabaseClient

  // 根據當前語言處理顯示資料
  const searchResults = useMemo(() => {
    console.log('useMemo 重新計算顯示資料,語言:', currentLang);
    
    const LANGUAGE_SUFFIX_MAP = {
      'zh-TW': '',
      'en': '_en_lang',
      'jp': '_jp_lang',
      'id': '_id_lang'
    };

    const suffix = LANGUAGE_SUFFIX_MAP[currentLang] || '';

    return rawNewsData.map(news => ({
      ...news,
      title: suffix ? (news[`news_title${suffix}`] || news.news_title) : news.news_title,
      shortSummary: suffix ? (news[`ultra_short${suffix}`] || news.ultra_short) : news.ultra_short
    }));
  }, [rawNewsData, currentLang]); // 當語言或原始資料改變時重新計算

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
