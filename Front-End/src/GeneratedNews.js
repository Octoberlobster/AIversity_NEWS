import React, { useState, useEffect } from 'react';
import './css/GeneratedNews.css';
import { useSupabase } from './supabase';

function GeneratedNews({eventId}) {

  const [eventData, setEventData] = useState(null); // 儲存事件數據
  const supabaseClient = useSupabase(); // 初始化 Supabase 客戶端
      useEffect(() => {
        const fetchEventData = async () => {
          try {
            const { data, error } = await supabaseClient
              .from('generated_news')
              .select('*')
              .eq('event_id', eventId)
              .order('date', { ascending: false }) //選date最近的那一筆
              
            if (error) throw error;
            setEventData(data);
          } catch (error) {
            console.error('Error fetching event details:', error);
          } 
        };
        
        fetchEventData();
      }, [eventId, supabaseClient]);

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
