import React, { useState } from 'react';
import NewsTopics from './NewsTopics';
import TimelineSources from './TimelineSources';
import './css/TimelineAnalysis.css';

const TimelineItem = ({ item, index, mediaColors, isPrediction }) => {
  const [expanded, setExpanded] = useState(false);

  // 預測項目的特殊樣式
  const predictionClass = isPrediction ? 'timeline-prediction' : '';
  const nodeClass = isPrediction 
    ? 'node-prediction' 
    : `${index % 3 === 0 ? 'node-blue' : index % 3 === 1 ? 'node-green' : 'node-red'}`;

  return (
    <div className={`timeline-item ${expanded ? 'expanded' : ''} ${predictionClass}`}>
      <div className="timeline-date-box">
        <div className="timeline-date">{item.date_range}</div>
      </div>
      
      <div 
        className={`timeline-node ${nodeClass}`}
        onClick={() => setExpanded(!expanded)}
      ></div>
      
      <div className="timeline-content">
        <h3 className="timeline-title">{item.summary}</h3>
        
        {expanded && (
          <div className="timeline-details">
            {/* 預測內容 */}
            {isPrediction ? (
              <div className="prediction-content">
                <p>{item.content}</p>
              </div>
            ) : (
              <>
                {/* 常規媒體焦點和來源組件 */}
                <NewsTopics 
                  timelineItemId={item.timeline_items_id} 
                  mediaColors={mediaColors}
                />
                <TimelineSources 
                  timelineItemId={item.timeline_items_id} 
                  mediaColors={mediaColors}
                />
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};


export default TimelineItem;
