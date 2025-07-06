import React, { useState, useEffect } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { useSupabase } from './supabase';
import { Link } from 'react-router-dom';
import './css/EventList.css';
import Header from './Header';

function NewsCategory() {
  const { type } = useParams(); // 從路由參數取得類別
  const location = useLocation();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [language, setLanguage] = useState('zh');
  const supabase = useSupabase();

  // 從 URL 查詢參數中獲取日期範圍
  const searchParams = new URLSearchParams(location.search);
  const startDate = searchParams.get('startDate');
  const endDate = searchParams.get('endDate');
  
  // 檢查日期設定是否有效
  const isDateRangeValid = () => {
    if (!startDate || !endDate) return true; // 如果只有一個日期或都沒有，視為有效
    return new Date(endDate) >= new Date(startDate);
  };

  const categoryNames = {
    'Politics': '政治新聞',
    'Social News': '社會新聞',
    'Science': '科學新聞',
    'Technology': '科技新聞',
    'International News': '國際新聞',
    'Lifestyle & Consumer News': '生活新聞',
    'Sports': '運動新聞',
    'Entertainment': '娛樂新聞',
    'Business & Finance': '財經新聞',
    'Health & Wellness': '醫療保健'
  };

  // 生成顯示標題，包含日期篩選資訊
  const generateDisplayTitle = () => {
    let title = type ? `${categoryNames[type] || type}` : '所有新聞專題';
    
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

  useEffect(() => {
    async function fetchEventsByCategory() {
      setLoading(true);
      try {
        // 先取得該類別的 event_id 清單
        const { data: mapData, error: mapError } = await supabase
          .from('event_category_map')
          .select('event_id')
          .eq('category', type);

        if (mapError) throw mapError;

        const eventIds = mapData.map(item => item.event_id);

        if (eventIds.length === 0) {
          setEvents([]);
          setLoading(false);
          return;
        }

        // 如果有日期篩選條件，需要通過 generated_news 表來進行日期篩選
        let finalEventIds = eventIds;
        
        if (startDate || endDate) {
          // 從 generated_news 表中根據日期篩選獲取 event_id
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

          // 獲取符合日期條件的 event_id（去重）
          finalEventIds = [...new Set(newsData.map(item => item.event_id))];
        }

        // 再依 event_id 查詢事件資料
        const { data: eventsData, error: eventError } = await supabase
          .from('event')
          .select('event_id, event_title')
          .in('event_id', eventIds)
          .order('event_id', { ascending: false });

        if (eventError) throw eventError;

        setEvents(eventsData);
      } catch (error) {
        console.error('抓取新聞專題時發生錯誤:', error);
      } finally {
        setLoading(false);
      }
    }

    if (type) {
      fetchEventsByCategory();
    } else {
      // 若沒有類別參數，可改成載入全部事件或其他邏輯
      setEvents([]);
      setLoading(false);
    }
  }, [supabase, type, startDate, endDate]);
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

export default NewsCategory;
