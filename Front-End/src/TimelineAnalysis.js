import React, { useState, useEffect } from 'react';
import './TimelineAnalysis.css';

const TimelineAnalysis = () => {
  const [expandedItems, setExpandedItems] = useState({});
  const [timelineEvents, setTimelineEvents] = useState([]);
  const [newsDetails, setNewsDetails] = useState({});

  useEffect(() => {
    // 使用webpack的require.context動態導入所有進度JSON檔案
    const progressContext = require.context('./processed/progress', false, /\.json$/);
    const events = progressContext.keys().map((key, index) => {
      const eventData = progressContext(key);
      
      // 預設為 event，如果檔案名稱包含 "predict" 則設成 predict
      const type = key.includes("predict") ? "predict" : "event";

      return {
        id: index + 1,
        date: eventData.Date,
        summary: eventData.Summary,
        type: type,
        urls: eventData.URL
      };
    });

    // 按日期排序事件
    events.sort((a, b) => new Date(a.date) - new Date(b.date));
    setTimelineEvents(events);

    // 導入新聞詳情JSON檔案
    try {
      const similarityContext = require.context('./processed/similarty', false, /\.json$/);
      const newsData = {};
      
      similarityContext.keys().forEach(key => {
        const data = similarityContext(key);
        data.forEach(item => {
          if (!newsData[item.Date]) {
            newsData[item.Date] = [];
          }
          newsData[item.Date].push(item);
        });
      });
      
      setNewsDetails(newsData);
    } catch (error) {
      console.error("Error loading news details:", error);
    }
  }, []);

  const toggleItem = (id) => {
    setExpandedItems(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const renderTimelineItem = (item) => {
    // 檢查是否有對應日期的新聞詳情
    const detail = newsDetails[item.date];

    return (
      <div className="timeline-item" key={item.id}>
        <div 
          className={`timeline-node ${item.type === 'event' ? 'event-node' : 'prediction-node'}`} 
          onClick={() => toggleItem(item.id)}
        ></div>
        <div className="timeline-content">
          <div className="timeline-date">{item.date}</div>
          <div className="timeline-title">{item.summary}</div>
          
          {expandedItems[item.id] && detail && (
            <div className="timeline-details">
              {detail.map((newsItem, index) => (
                <div key={index} className="news-detail-item">
                  <h4>{newsItem.Topic}</h4>
                  <div className="news-source-label">新聞來源：</div>
                  <div className="news-sources">
                    {newsItem.News_sources.map((source, idx) => (
                      <span key={idx} className="news-source-tag">{source}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="timeline-container">
      <h2>烏俄戰爭時序分析</h2>
      <div className="timeline-legend">
        <div className="legend-item">
          <div className="legend-node event-node"></div>
          <span>實際事件</span>
        </div>
        <div className="legend-item">
          <div className="legend-node prediction-node"></div>
          <span>AI預測</span>
        </div>
      </div>
      
      <div className="vertical-timeline">
        {timelineEvents.map(item => renderTimelineItem(item))}
      </div>
    </div>
  );
};

export default TimelineAnalysis;
