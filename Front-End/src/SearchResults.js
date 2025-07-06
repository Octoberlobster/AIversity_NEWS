import React, { useState, useEffect } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { useSupabase } from './supabase';
import { Link } from 'react-router-dom';
import './css/EventList.css';
import Header from './Header';

function SearchResults() {
  const { query } = useParams();
  const location = useLocation();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [language, setLanguage] = useState('zh');
  const supabase = useSupabase();

  // 解碼 URL 中的查詢參數
  const searchParams = new URLSearchParams(location.search);
  const startDate = searchParams.get('startDate');
  const endDate = searchParams.get('endDate');

  // 檢查日期設定是否有效
  const isDateRangeValid = () => {
    if (!startDate || !endDate) return true; // 如果只有一個日期或都沒有，視為有效
    return new Date(endDate) >= new Date(startDate);
  };
  
  useEffect(() => {
    async function fetchSearchResults() {
      setLoading(true);
      try {
        // 1. 從 event_keyword_map 找出 keyword 包含 query 的 event_id
        const { data: keywordMapData, error: keywordMapError } = await supabase
          .from('event_keyword_map')
          .select('event_id')
          .ilike('keyword', `%${query}%`);

        if (keywordMapError) throw keywordMapError;

        if (!keywordMapData || keywordMapData.length === 0) {
          setEvents([]);
          setLoading(false);
          return;
        }

        const eventIds = keywordMapData.map(item => item.event_id);

        // 2. 用 event_id 查詢事件資料
        let eventQuery = supabase
          .from('event')
          .select('event_id, event_title')
          .in('event_id', eventIds);

        // 3. 如果有日期篩選條件，需要 join generated_news 表來進行日期篩選
        if (startDate || endDate) {
          // 先從 generated_news 表中根據日期篩選獲取 event_id
          let newsQuery = supabase
            .from('generated_news')
            .select('event_id')
            .in('event_id', eventIds);

          // 應用日期篩選
          if (startDate) {
            newsQuery = newsQuery.gte('date', startDate);
          }
          if (endDate) {
            newsQuery = newsQuery.lte('date', endDate);
          }

          const { data: newsData, error: newsError } = await newsQuery;

          if (newsError) throw newsError;

          if (!newsData || newsData.length === 0) {
            setEvents([]);
            setLoading(false);
            return;
          }

          // 獲取符合日期條件的 event_id
          const filteredEventIds = [...new Set(newsData.map(item => item.event_id))];

          // 更新事件查詢，只查詢符合日期條件的事件
          eventQuery = supabase
            .from('event')
            .select('event_id, event_title')
            .in('event_id', filteredEventIds);
        }

        const { data: eventData, error: eventError } = await eventQuery
          .order('event_id', { ascending: false });

        if (eventError) throw eventError;

        setEvents(eventData);
      } catch (error) {
        console.error('抓取搜尋結果時發生錯誤:', error);
        setEvents([]);
      } finally {
        setLoading(false);
      }
    }

    fetchSearchResults();
  }, [query, supabase, startDate, endDate]);

  // 生成顯示標題，包含日期篩選資訊
  const generateDisplayTitle = () => {
    let title = query ? `「${decodeURIComponent(query)}」的搜尋結果` : '搜尋結果';
    
    if (startDate || endDate) {
      title += ' (';
      if (startDate && endDate) {
        title += `${startDate} 至 ${endDate}`;
      } else if (startDate) {
        title += `${startDate} 起`;
      } else if (endDate) {
        title += `至 ${endDate}`;
      }
      title += ')';
    }
    
    return title;
  };

  const displayTitle = generateDisplayTitle();

  if (loading) {
    return (
      <>
        <Header language={language} setLanguage={setLanguage} />
        <div className="event-list-container">
          <div>讀取中...</div>
        </div>
      </>
    );
  }

  return (
    <>
      <Header language={language} setLanguage={setLanguage} />
      <div className="event-list-container">
        <h1 className="event-list-title">{displayTitle}</h1>
        {startDate && endDate && !isDateRangeValid() && (
          <p className="error-message">起始日期不能晚於結束日期。</p>
        )}
        {events.length === 0 && isDateRangeValid() ? (
          <p>目前沒有相關資料。</p>
        ) : (
          <div className="event-grid">
            {events.map(event => (
              <Link key={event.event_id} to={`/event/${event.event_id}`} className="event-card">
                <h2 className="event-title">{event.event_title}</h2>
              </Link>
            ))}
          </div>
        )}
      </div>
    </>
  );
}

export default SearchResults;
