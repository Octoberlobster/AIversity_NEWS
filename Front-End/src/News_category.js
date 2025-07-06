import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useSupabase } from './supabase';
import { Link } from 'react-router-dom';
import './css/EventList.css';
import Header from './Header';

function NewsCategory() {
  const { type } = useParams(); // 從路由參數取得類別
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [language, setLanguage] = useState('zh');
  const supabase = useSupabase();
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
  }, [supabase, type]);

  if (loading) {
    return <div>讀取中...</div>;
  }

  return (
    <>
        <Header language={language} setLanguage={setLanguage} />
        <div className="event-list-container">
        <h1 className="event-list-title">{type ? `${categoryNames[type] || type}` : '所有新聞專題'}</h1>
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

export default NewsCategory;
