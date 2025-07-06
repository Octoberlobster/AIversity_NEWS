import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useSupabase } from './supabase';
import { Link } from 'react-router-dom';
import './css/EventList.css';
import Header from './Header';

function SearchResults() {
  const { query } = useParams();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [language, setLanguage] = useState('zh');
  const supabase = useSupabase();

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
        const { data: eventData, error: eventError } = await supabase
          .from('event')
          .select('event_id, event_title')
          .in('event_id', eventIds)
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
  }, [query, supabase]);

  const displayTitle = query ? `「${decodeURIComponent(query)}」的搜尋結果` : '搜尋結果';

  if (loading) {
    return <div>讀取中...</div>;
  }

  return (
    <>
      <Header language={language} setLanguage={setLanguage} />
      <div className="event-list-container">
        <h1 className="event-list-title">{displayTitle}</h1>
        {events.length === 0 ? (
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
