import React, { useState, useRef, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import TopicChatRoom from './TopicChatRoom';
import './../css/SpecialReportDetail.css';

// 模擬專題報導詳細資料
const specialReportData = {
  1: {
    id: 1,
    title: "2025罷免案",
    summary: "國民黨與民眾黨2024年起聯手以人數優勢陸續通過國會職權等修法引發不滿，民團2025年起陸續鎖定國民黨立委發動罷免連署。24位藍委及新竹市長高虹安罷免案7月26日投開票，25案全數遭到否決。第二波共7案罷免投票將在8月23日登場，包括國民黨立委馬文君、游顥、羅明才、江啟臣、楊瓊瓔、顏寬恒、林思銘。",
    icon: "🗳️",
    events: [
      "即時開票",
    ],
    articles: 15,
    views: "25.3k",
    lastUpdate: "2025/7/30 18:10",
    eventDetails: {
      "即時開票": {
        title: "即時開票結果",
        summary: "最新罷免投票開票結果，包含各選區投票率、同意票與不同意票統計。",
        articles: [
          { 
            id: 101, 
            title: "大罷免投票率平均破5成5 傅崐萁案破6成創紀錄", 
            views: "12.5k", 
            date: "2025/7/26 22:55", 
            author: "中央社",
            category: "專題報導",
            sourceCount: 3,
            shortSummary: "2025年7月26日舉行的罷免投票中，整體投票率平均突破55%，其中傅崐萁案的投票率更突破60%，創下歷史新高。各選區的投票情況顯示民眾對罷免案的高度關注。",
            relatedNews: [
              { id: 1011, title: "傅崐萁罷免案詳細分析" },
              { id: 1012, title: "各選區投票率統計" },
              { id: 1013, title: "罷免案投票結果影響" }
            ],
            keywords: ["投票", "罷免", "統計"]
          },
          { 
            id: 102, 
            title: "2025立委罷免案開票結果一覽 7月26日24案全數不通過", 
            views: "8.9k", 
            date: "2025/7/26 16:00", 
            author: "中央社",
            category: "專題報導",
            sourceCount: 4,
            shortSummary: "7月26日舉行的24個立委罷免案全部未通過門檻，顯示選民對罷免制度的態度趨於保守。各案投票結果分析顯示，反對罷免的票數明顯高於支持罷免。",
            relatedNews: [
              { id: 1021, title: "罷免制度檢討聲浪" },
              { id: 1022, title: "選民態度分析報告" },
              { id: 1023, title: "政治影響評估" }
            ],
            keywords: ["罷免", "制度", "分析"]
          },
          { 
            id: 103, 
            title: "高虹安鄭正鈐罷免案即時開票 中央社圖表掌握實況", 
            views: "15.2k", 
            date: "2025/7/26 15:00", 
            author: "中央社",
            category: "專題報導",
            sourceCount: 2,
            shortSummary: "新竹市長高虹安與立委鄭正鈐的罷免案開票過程透過中央社即時圖表呈現，讓民眾能夠第一時間掌握投票進度與結果。",
            relatedNews: [
              { id: 1031, title: "高虹安罷免案背景" },
              { id: 1032, title: "鄭正鈐政治立場" },
              { id: 1033, title: "新竹市政治情勢" }
            ],
            keywords: ["高虹安", "鄭正鈐", "新竹"]
          }
        ]
      },
    }
  }
};

function SpecialReportDetail() {
  const { id } = useParams();
  const [activeEvent, setActiveEvent] = useState(null);
  const [expandedCards, setExpandedCards] = useState({});
  const [isChatOpen, setIsChatOpen] = useState(false);
  const sectionRefs = useRef({});

  const report = specialReportData[id];

  if (!report) {
    return (
      <div className="srdPage">
        <div className="srdMain">
          <div style={{ textAlign: 'center', padding: '3rem' }}>
            <h2>專題報導不存在</h2>
            <p>請返回專題報導列表</p>
            <Link to="/special-reports" style={{ color: '#667eea' }}>
              返回專題報導
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const handleNavClick = (event) => {
    setActiveEvent(event);
    const targetRef = sectionRefs.current[event];
    if (targetRef) {
      targetRef.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const toggleExpanded = (cardId) => {
    setExpandedCards((prev) => ({ ...prev, [cardId]: !prev[cardId] }));
  };

  

  return (
    <div className="srdPage">
      {/* 聊天室圖標按鈕 */}
      <button 
        className={`chat-toggle-btn ${isChatOpen ? 'hidden' : ''}`}
        onClick={() => setIsChatOpen(!isChatOpen)}
        title={isChatOpen ? '關閉聊天室' : '開啟聊天室'}
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path 
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" 
            stroke="currentColor" 
            strokeWidth="2" 
            strokeLinecap="round" 
            strokeLinejoin="round"
          />
        </svg>
      </button>

      <div className={`srdMain ${isChatOpen ? 'chat-open' : ''}`}>
        {/* Header */}
        <div className="srdHeader">
          <div className="srdHeader__content">
            <h1 className="srdHeader__title">{report.title}</h1>
            <p className="srdHeader__summary">{report.summary}</p>
            <div className="srdHeader__meta">
              <div className="srdHeader__metaItem">
                <span>📅</span>
                <span>{report.lastUpdate}</span>
              </div>
              <div className="srdHeader__metaItem">
                <span>📄</span>
                <span>{report.articles} 篇文章</span>
              </div>
              <div className="srdHeader__metaItem">
                <span>👁️</span>
                <span>{report.views}</span>
              </div>
            </div>
          </div>
          <div className="srdHeader__image" />
        </div>

        {/* Layout */}
        <div className="srdLayout">
          <div className="srdMainCol">
            {report.events.map((event) => {
              const eventDetail = report.eventDetails[event];
              return (
                <section
                  key={event}
                  className="srdSection"
                  ref={(el) => {
                    sectionRefs.current[event] = el;
                  }}
                >
                  <h2 className="srdSection__title">{event}</h2>
                  <p className="srdSection__summary">{eventDetail?.summary}</p>

                  <div className="srdGrid">
                    {eventDetail?.articles.map((news) => {
                      const isExpanded = !!expandedCards[news.id];
                      return (
                        <article key={news.id} className="srdCard">
                          <div className="srdCard__header">
                            <Link to={`/news/${news.id}`} className="srdCard__title">
                              {news.title}
                            </Link>
                          </div>

                          <div className="srdCard__info">
                            <span className="srdDateText">{news.date}</span>
                            <span className="srdAuthorText">記者 {news.author}</span>
                          </div>

                          <div className="srdCard__meta">
                            <span className="srdCategoryTag">{news.category}</span>
                            <span className="srdSourceCount">{news.sourceCount} 個來源</span>
                            {news.keywords?.map((kw) => (
                              <span key={kw} className="srdKeywordChip">{kw}</span>
                            ))}
                          </div>

                          <div className="srdCard__content">
                            <p className={`srdCard__summary ${isExpanded ? 'is-expanded' : ''}`}>
                              {isExpanded ? news.shortSummary : news.shortSummary.substring(0, 150)}
                            </p>

                            {isExpanded && (
                              <div className="srdExpanded">
                                <div className="srdRelatedNews">
                                  <h4 className="srdRelatedNews__title">相關報導</h4>
                                  <ul className="srdRelatedNews__list">
                                    {news.relatedNews.map((rn) => (
                                      <li key={rn.id} className="srdRelatedNews__item">
                                        <Link to={`/news/${rn.id}`} className="srdRelatedNews__link">
                                          {rn.title}
                                        </Link>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              </div>
                            )}
                          </div>

                          <div className="srdCard__actions">
                            <div className="srdActionButtons">
                              <button
                                type="button"
                                className="srdActionButton"
                                onClick={() => toggleExpanded(news.id)}
                              >
                                {isExpanded ? '收起' : '展開'}
                              </button>
                            </div>
                            <div className="srdStats">
                              <span className="srdStatItem">👁️ {news.views}</span>
                            </div>
                          </div>
                        </article>
                      );
                    })}
                  </div>
                </section>
              );
            })}
          </div>

          {/* Sidebar */}
          <aside className="srdSidebar">
            <div className="srdSidebarCard">
              <h3 className="srdSidebarTitle">專題導覽</h3>
              <nav className="srdNav">
                {report.events.map((event) => (
                  <button
                    key={event}
                    className={`srdNavItem ${activeEvent === event ? 'is-active' : ''}`}
                    onClick={() => handleNavClick(event)}
                    type="button"
                  >
                    {event}
                  </button>
                ))}
              </nav>
            </div>
          </aside>
        </div>
      </div>

      {/* 側邊聊天室 */}
      <div className={`chat-sidebar ${isChatOpen ? 'open' : ''}`}>
        <div className="chat-sidebar-header">
          <h3>專題討論</h3>
          <button 
            className="chat-close-btn"
            onClick={() => setIsChatOpen(false)}
          >
            ✕
          </button>
        </div>
        <div className="chat-sidebar-content">
          <TopicChatRoom />
        </div>
      </div>
    </div>
  );
}

export default SpecialReportDetail;