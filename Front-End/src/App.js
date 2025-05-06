import React, { useState, useEffect } from 'react'; // 引入React核心庫和必要的Hook函數
import { Routes, Route, Link, useNavigate } from 'react-router-dom';  // 引入React Router相關組件，用於路由導航和頁面切換
import { supabase, SupabaseProvider, useSupabase } from './supabase';
import './css/EventList.css';// 引入事件列表頁面的樣式表
import Header from './Header'; // 引入頁面頭部組件

/**
 * App組件 - 應用程序的主要入口點
 * 負責管理全局狀態和路由
 */
function App() {
  // 定義狀態變量
  const [events, setEvents] = useState([]); // 存儲從資料庫獲取的事件列表
  const [loading, setLoading] = useState(true); // 控制加載狀態
  
  // 初始化 Supabase 客戶端，用於與後端資料庫通信
  const supabaseClient = useSupabase();
  
  /**
   * 使用useEffect hook在組件掛載時獲取事件列表
   * 從Supabase資料庫獲取數據並更新狀態
   */
  useEffect(() => {
    const fetchEvents = async () => {
      try {
        // 從資料庫的event表中獲取事件列表
        const { data, error } = await supabase
          .from('event')
          .select('event_id, event_title') // 只選擇需要的字段
          .order('event_id', { ascending: false }); // 按ID降序排列，最新事件排在前面
          
        if (error) throw error; // 如果有錯誤則拋出
        // 格式化數據並更新狀態
        setEvents(data.map(event => ({ id: event.event_id, title: event.event_title })) || []);
        console.log("資料庫抓到資料了");
      } catch (error) {
        // 記錄錯誤但不中斷應用程序
        console.error('Error fetching events:', error);
      } finally {
        // 無論成功或失敗，都將加載狀態設為false
        setLoading(false);
      }
    };
    
    // 調用函數獲取事件
    fetchEvents();
  }, [supabaseClient]); // 空依賴數組表示此effect只在組件首次渲染時執行


  return (
    <SupabaseProvider>
      <div className="container">
        <Header />
        {/* 主內容區域 */}
        <div className="content">
          <EventListPage events={events} loading={loading} />
        </div>
      </div>
    </SupabaseProvider>
  );
}

/**
 * 事件列表頁面組件
 * 負責顯示所有可用的新聞事件專題
 * 
 * @param {Array} events - 事件數據陣列
 * @param {boolean} loading - 加載狀態
 */
function EventListPage({ events, loading }) {
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
            <Link 
              key={event.id} // React列表元素的唯一標識
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

// 導出App組件作為默認導出
export default App;
