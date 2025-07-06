import React, { useState, useEffect } from 'react';
import { useSupabase } from './supabase';
import { Link } from 'react-router-dom';
import './css/EventList.css';

function NewsProject() {
  const [popularEvents, setPopularEvents] = useState([]);
  const [latestEvents, setLatestEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const supabase = useSupabase();

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        // Fetch popular events (sorted by view_count descending)
        const { data: popularData, error: popularError } = await supabase
          .from('event')
          .select('event_id, event_title, view_count')
          .order('view_count', { ascending: false })
          .limit(5);

        if (popularError) throw popularError;

        setPopularEvents(
          popularData.map(event => ({ id: event.event_id, title: event.event_title })) || []
        );

        const { data: latestData, error: latestError } = await supabase
          .from('generated_news')
          .select('event_id, date, event:event_id(event_title)')
          .order('date', { ascending: false })
          .limit(5);
        console.log(latestData);
        if (latestError) throw latestError;

        setLatestEvents(
          latestData.map(item => ({
            id: item.event_id,
            title: item.event?.event_title || '未知標題'
          })) || []
        );
        

        console.log("熱門專題和最新專題資料已載入");
      } catch (error) {
        console.error('抓取新聞專題時發生錯誤:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  }, [supabase]);

  if (loading) {
    return <div>讀取中...</div>;
  }

  return (
    <div className="event-list-container">
      {/* 頁面標題 */}
      <h1 className="event-list-title">新聞事件專題</h1>

      {/* 熱門專題 */}
      <h2 className="event-section-title">熱門專題</h2>
      <div className="event-grid">
        {popularEvents.map(event => (
          <Link
            key={event.id}
            to={`/event/${event.id}`}
            className="event-card"
          >
            <h2 className="event-title">{event.title}</h2>
          </Link>
        ))}
      </div>

      {/* 最新專題 */}
      <h2 className="event-section-title">最新專題</h2>
      <div className="event-grid">
        {latestEvents.map(event => (
          <Link
            key={event.id}
            to={`/event/${event.id}`}
            className="event-card"
          >
            <h2 className="event-title">{event.title}</h2>
          </Link>
        ))}
      </div>
    </div>
  );
}

export default NewsProject;