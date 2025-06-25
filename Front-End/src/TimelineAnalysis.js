import React, { useState, useEffect } from 'react';
import { useSupabase } from './supabase';
import TimelineItem from './TimelineItem';
import './css/TimelineAnalysis.css';

const TimelineAnalysis = ({ eventId }) => {
  const [timelineItems, setTimelineItems] = useState([]);
  const [predictionItem, setPredictionItem] = useState(null);
  const [loading, setLoading] = useState(true);
  const supabaseClient = useSupabase();
  
  // 定義顏色設置...
  const mediaColors = { /* 您的媒體顏色映射 */ };

  // 獲取時間軸項目和預測數據
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // 獲取時間軸歷史數據
        const { data: timelineData, error: timelineError } = await supabaseClient
          .from('timeline_items')
          .select('*')
          .eq('event_id', eventId)
          .order('start_date', { ascending: true });
          
        if (timelineError) throw timelineError;
        
        // 獲取相同事件的預測數據
        const { data: predictionData, error: predictionError } = await supabaseClient
          .from('generated_news')
          .select('generated_id, predict_title, predict_content, date')
          .eq('event_id', eventId)
          .order('date', { ascending: false })
          .limit(1); // 獲取最新的預測
          
        if (predictionError) throw predictionError;
        
        setTimelineItems(timelineData || []);
        
        // 如果有預測數據，轉換為時間軸項目格式
        if (predictionData && predictionData.length > 0) {
          const prediction = predictionData[0];
          // 創建一個與時間軸項目格式相符的預測項目
          setPredictionItem({
            timeline_items_id: `prediction-${prediction.generated_id}`,
            date_range: '趨勢分析',
            summary: prediction.predict_title,
            content: prediction.predict_content,
            is_prediction: true // 標記為預測項目
          });
        }
      } catch (error) {
        console.error('Error fetching timeline data:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [eventId, supabaseClient]);

  // 渲染部分...
  // 在這裡集成預測項目到時間軸中
  return (
    <div className="timeline-container">
      <h2 className="timeline-main-title">新聞時序 & 趨勢分析</h2>
      
      <div className="timeline">
        <div className="timeline-line"></div>
        
        {/* 呈現所有的歷史時間軸項目 */}
        {timelineItems.map((item, index) => (
          <TimelineItem 
            key={item.timeline_items_id}
            item={item}
            index={index}
            mediaColors={mediaColors}
            isPrediction={false}
          />
        ))}
        
        {/* 如果有預測數據，在時間軸最後呈現預測項目 */}
        {predictionItem && (
          <TimelineItem 
            key={predictionItem.timeline_items_id}
            item={predictionItem}
            index={timelineItems.length}
            mediaColors={mediaColors}
            isPrediction={true}
          />
        )}
      </div>
    </div>
  );
};


export default TimelineAnalysis;
