import React, { useState, useEffect } from 'react';
import './css/GeneratedNews.css';
import { useSupabase } from './supabase';

function GeneratedNews({eventId}) {
  const [eventData, setEventData] = useState(null);
  const [loading, setLoading] = useState(true);
  const supabaseClient = useSupabase();
  
  useEffect(() => {
    const fetchEventData = async () => {
      try {
        setLoading(true);
        const { data, error } = await supabaseClient
          .from('generated_news')
          .select('*')
          .eq('event_id', eventId)
          .order('date', { ascending: false })
          .limit(1); // 只獲取最新的一筆記錄
          
        if (error) throw error;
        
        if (data && data.length > 0) {
          setEventData(data[0]); // 保存第一條記錄
          console.log("資料庫抓到資料了 data:", data[0]);
        } else {
          console.log("找不到相關事件的新聞數據");
        }
      } catch (error) {
        console.error('Error fetching event details:', error);
      } finally {
        setLoading(false);
      }
    };
    
    if (eventId) {
      fetchEventData();
    }
  }, [eventId, supabaseClient]);

  // 加載中或無數據時顯示
  if (loading) return <div className="loading">載入中...</div>;
  if (!eventData) return <div className="error">未找到新聞數據</div>;

  // 數據加載完成後才渲染內容
  return (
    <div className="left-panel">
      <h2 className="panel-title">{eventData.title}</h2>
      <p className="panel-date">發布日期：{eventData.date}</p>
      <div className="panel-content">
        {eventData.content.split('\n\n').map((paragraph, index) => (
          <p key={index}>{paragraph}</p>
        ))}
      </div>
    </div>
  );
}

export default GeneratedNews;
