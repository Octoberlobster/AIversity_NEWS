import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import UnifiedNewsCard from './UnifiedNewsCard';
import FloatingChat from './FloatingChat';
import { searchNews, fetchNewsDataFromSupabase } from './api';
import { useSupabase } from './supabase';
import './../css/SearchResultsPage.css';

const hotKeywords = [
  'AI', '房價', '疫苗', '選舉', '颱風', '股市', '升息', '地震', '烏俄', '通膨',
  '台積電', '碳中和', '缺水', '罷工', 'ChatGPT', '元宇宙', '女足', '大罷免',
  '能源', 'AI醫療', '5G', '電動車', '半導體', '新冠', '核電', '綠能'
];

function SearchResultsPage() {
  const { query } = useParams();
  const navigate = useNavigate();
  const supabaseClient = useSupabase();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [searchInfo, setSearchInfo] = useState(null);
  const [showAllNews, setShowAllNews] = useState(false);

  useEffect(() => {
    const performSearch = async () => {
      if (!query || query.trim() === '') {
        setError('請輸入搜尋關鍵字');
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
          throw new Error('搜尋 API 沒有返回有效回應');
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
          setSearchResults(newsData);
        } else {
          console.log('沒有找到 story_ids 或為空陣列');
          setSearchResults([]);
        }

      } catch (err) {
        console.error('搜尋錯誤:', err);
        setError(err.message || '搜尋時發生錯誤');
      } finally {
        setLoading(false);
      }
    };

    performSearch();
  }, [query, supabaseClient]);

  if (loading) {
    return (
      <div className="searchPage">
        <main className="searchPage__main">
          <div className="searchPage__loading">
            <div className="loadingSpinner"></div>
            <p>搜尋中...</p>
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
            <h2>⚠️ 搜尋出現問題</h2>
            <p>{error}</p>
            <button 
              className="searchPage__backBtn"
              onClick={() => navigate('/')}
            >
              返回首頁
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
                搜尋結果：「{query}」
              </h2>
              {searchInfo && (
                <div className="searchPage__info">
                  <p className="searchPage__resultCount">
                    找到 {searchInfo.count || searchResults.length} 篇相關新聞
                  </p>
                  {searchInfo.keywords && searchInfo.keywords.length > 0 && (
                    <div className="searchPage__keywords">
                      <span>搜尋關鍵字: </span>
                      {searchInfo.keywords.map((keyword, index) => (
                        <span key={index} className="searchPage__keyword">
                          {keyword}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {searchResults.length === 0 ? (
              <div className="searchPage__noResults">
                <h3>😔 找不到相關新聞</h3>
                <p>嘗試使用不同的關鍵字，或瀏覽以下熱門主題：</p>
                <div className="searchPage__suggestedKeywords">
                  {hotKeywords.slice(0, 8).map((kw) => (
                    <span
                      key={kw}
                      className="searchPage__suggestedKw"
                      onClick={() => navigate(`/search/${encodeURIComponent(kw)}`)}
                    >
                      {kw}
                    </span>
                  ))}
                </div>
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
                      顯示更多搜尋結果 ({searchResults.length - 12} 篇)
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
