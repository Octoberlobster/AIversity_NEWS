import React, { useState } from 'react';
import './TimelineAnalysis.css';

const TimelineAnalysis = () => {
  const [expandedItems, setExpandedItems] = useState({});

  const toggleItem = (id) => {
    setExpandedItems(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const timelineEvents = [
    {
      id: 1,
      date: "2022年2月24日",
      title: "俄羅斯全面入侵烏克蘭",
      type: "event", // 綠色節點
      details: {
        western: "俄羅斯無端侵略,烏克蘭奮起抵抗",
        russian: "特別軍事行動,解放頓巴斯地區",
        neutral: "衝突升級,局勢緊張"
      }
    },
    {
      id: 2,
      date: "2022年2月25日",
      title: "AI預測: 基輔可能陷落,西方將加強制裁",
      type: "prediction", // 紅色節點
      predictions: [
        "俄軍可能在72小時內攻佔基輔",
        "美國和歐盟將實施更嚴厲的經濟制裁",
        "烏克蘭軍民抵抗將持續"
      ]
    },
    {
      id: 3,
      date: "2022年3月16日",
      title: "馬里烏波爾劇院被轟炸",
      type: "event",
      details: {
        western: "俄軍蓄意攻擊平民避難所",
        russian: "亞速營將平民作為人盾",
        neutral: "平民傷亡嚴重,需要人道主義援助"
      }
    },
    {
      id: 4,
      date: "2022年3月17日",
      title: "AI預測: 談判可能取得進展,但戰事仍將持續",
      type: "prediction",
      predictions: [
        "雙方可能就中立地位達成初步共識",
        "頓巴斯地區問題仍是主要障礙",
        "戰事可能轉向消耗戰"
      ]
    },
    {
      id: 5,
      date: "2023年6月6日",
      title: "卡霍夫卡大壩被炸",
      type: "event",
      details: {
        western: "俄軍破壞關鍵基礎設施",
        russian: "烏軍蓄意破壞,轉移反攻失利注意力",
        neutral: "環境災難,需要緊急人道主義援助"
      }
    },
    {
      id: 6,
      date: "2023年6月7日",
      title: "AI預測: 烏克蘭反攻可能加速,國際援助將增加",
      type: "prediction",
      predictions: [
        "烏軍可能利用混亂局面加速南部反攻",
        "西方國家將提供更多軍事和人道主義援助",
        "俄軍可能加強對烏克蘭基礎設施的打擊"
      ]
    }
  ];

  const renderTimelineItem = (item) => {
    return (
      <div className="timeline-item" key={item.id}>
        <div className={`timeline-node ${item.type === 'event' ? 'event-node' : 'prediction-node'}`} 
             onClick={() => toggleItem(item.id)}>
        </div>
        <div className="timeline-date">{item.date}</div>
        <div className="timeline-title">{item.title}</div>
        
        {expandedItems[item.id] && (
          <div className="timeline-details">
            {item.type === 'event' ? (
              <div className="media-comparison">
                <div className="media-source">
                  <h4>西方媒體報導</h4>
                  <p>{item.details.western}</p>
                </div>
                <div className="media-source">
                  <h4>俄羅斯媒體報導</h4>
                  <p>{item.details.russian}</p>
                </div>
                <div className="media-source">
                  <h4>中立媒體報導</h4>
                  <p>{item.details.neutral}</p>
                </div>
              </div>
            ) : (
              <div className="ai-predictions">
                <h4>AI預測分析</h4>
                <ul>
                  {item.predictions.map((prediction, idx) => (
                    <li key={idx}>{prediction}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
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
