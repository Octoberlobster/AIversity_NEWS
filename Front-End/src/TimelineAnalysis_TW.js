import React, { useState, useEffect } from 'react';
import './TimelineAnalysis.css';

const TimelineAnalysis = () => {
  const [expandedItems, setExpandedItems] = useState({});
  const [timelineData, setTimelineData] = useState([]);
  const [newsTopics, setNewsTopics] = useState({});
  
  // 定義不同新聞台的顏色
  const mediaColors = {
    'cnn.com': '#CC0000',
    'foxnews.com': '#003366',
    'bbc.com': '#BB1919',
    'reuters.com': '#FF8000',
    'apnews.com': '#0078D4',
    'default': '#777777'
  };

  useEffect(() => {
    // 動態加載所有時間軸JSON檔案
    const context = require.context('./processed/progress_TW', false, /\.json$/);
    
    // 在 useEffect 中加載 progress 資料時進行轉換
    const loadedData = context.keys().map(key => {
      const item = context(key);
      // 轉換 URL 陣列為 Sources 陣列
      const sources = item.URL ? item.URL.map(url => ({
        Source: new URL(url).hostname.replace('www.', ''),
        URL: url
      })) : [];
      
      return {
        ...item,
        Sources: sources,
        id: key.replace(/^\.\/|\.json$/g, ''),
        startDate: new Date(item.DateRange.split(' ~ ')[0])
      };
    });
    
    // 按日期排序
    loadedData.sort((a, b) => a.startDate - b.startDate);
    setTimelineData(loadedData);
    
    // 加載媒體焦點數據
    try {
      const topicsContext = require.context('./processed/similarty_TW', false, /\.json$/);
      const topicsData = {};
      
      topicsContext.keys().forEach(key => {
        const data = topicsContext(key);
        // 將數據按日期範圍分組
        data.forEach(item => {
          if (!topicsData[item.DateRange]) {
            topicsData[item.DateRange] = [];
          }
          topicsData[item.DateRange].push(item);
        });
      });
      
      setNewsTopics(topicsData);
    } catch (error) {
      console.error("Error loading news topics:", error);
    }
  }, []);

  const toggleItem = (id) => {
    setExpandedItems(prev => ({ ...prev, [id]: !prev[id] }));
  };
  
  // 獲取新聞來源的顏色
  const getSourceColor = (source) => {
    return mediaColors[source] || mediaColors.default;
  };

  return (
    <div className="timeline-container">
      <h2 className="timeline-main-title">新聞時序 & 趨勢分析</h2>
      
      <div className="timeline">
        <div className="timeline-line"></div>
        
        {timelineData.map((item, index) => (
          <div className={`timeline-item ${expandedItems[item.id] ? 'expanded' : ''}`} key={item.id}>
            <div className="timeline-date-box">
              <div className="timeline-date">{item.DateRange}</div>
            </div>
            
            <div 
              className={`timeline-node ${index % 3 === 0 ? 'node-blue' : index % 3 === 1 ? 'node-green' : 'node-red'}`}
              onClick={() => toggleItem(item.id)}
            ></div>
            
            <div className="timeline-content">
              <h3 className="timeline-title">{item.Title}</h3>
              <p className="timeline-summary">{item.Summary}</p>
              
              {expandedItems[item.id] && (
                <div className="timeline-details">
                  {newsTopics[item.DateRange] && newsTopics[item.DateRange].length > 0 ? (
                    <div className="media-topics">
                      <h4 className="topics-title">媒體焦點分析</h4>
                      
                      {newsTopics[item.DateRange].map((topic, topicIndex) => (
                        <div className="topic-item" key={topicIndex}>
                          <div className="topic-content">{topic.Topic}</div>
                          
                          {topic.News_sources && topic.News_sources.length > 0 && (
                            <div className="topic-sources">
                              {topic.News_sources.map((source, sourceIndex) => (
                                <span 
                                  className="media-source-tag" 
                                  key={sourceIndex}
                                  style={{
                                    backgroundColor: `${getSourceColor(source)}20`,
                                    color: getSourceColor(source),
                                    borderLeft: `3px solid ${getSourceColor(source)}`
                                  }}
                                >
                                  {source}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="no-topics">此時間段無媒體焦點分析</div>
                  )}
                  
                  {item.Sources && item.Sources.length > 0 && (
                    <div className="original-sources">
                      <h4 className="sources-title">原始新聞來源</h4>
                      <div className="news-sources">
                        {item.Sources.map((source, sourceIndex) => (
                          <a 
                            href={source.URL} 
                            target="_blank" 
                            rel="noopener noreferrer" 
                            className="news-source-tag"
                            key={sourceIndex}
                            style={{
                              backgroundColor: `${getSourceColor(source.Source)}15`,
                              color: getSourceColor(source.Source),
                              borderLeft: `3px solid ${getSourceColor(source.Source)}`
                            }}
                          >
                            {source.Source}
                          </a>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TimelineAnalysis;
