import React, { useState, useEffect } from 'react';
import { useSupabase } from './supabase';
import { Link } from 'react-router-dom';
import './css/EventList.css'; 

// 將組件名稱從 NewsFeature 更新為 NewsProject
function NewsProject() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const supabase = useSupabase();

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const { data, error } = await supabase
          .from('event')
          .select('event_id, event_title')
          .order('event_id', { ascending: false });

        if (error) throw error;

        setEvents(data.map(event => ({ id: event.event_id, title: event.event_title })) || []);
        console.log("新聞專題資料已載入");
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
      
      {/* 條件渲染：加載中顯示加載指示器，否則顯示事件網格 */}
      {loading ? (
        <div className="loading-indicator">載入中...</div>
      ) : (
        <div className="event-grid">
          {/* 遍歷渲染事件卡片 */}
          {events.map(event => (
            <Link key={event.id} // React列表元素的唯一標識 
              to={`/event/${event.id}`} // 導航到事件詳情頁的路由
              className="event-card"
            >
              <h2 className="event-title">{event.title}</h2>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

// 更新導出的組件名稱
export default NewsProject;
