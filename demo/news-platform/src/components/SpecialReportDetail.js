import React, { useState, useRef, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import './../css/SpecialReportDetail.css';

// 模擬專題報導詳細資料
const specialReportData = {
  1: {
    id: 1,
    title: "2025罷免案",
    summary: "國民黨與民眾黨2024年起聯手以人數優勢陸續通過國會職權等修法引發不滿，民團2025年起陸續鎖定國民黨立委發動罷免連署。24位藍委及新竹市長高虹安罷免案7月26日投開票，25案全數遭到否決。第二波共7案罷免投票將在8月23日登場，包括國民黨立委馬文君、游顥、羅明才、江啟臣、楊瓊瓔、顏寬恒、林思銘。",
    status: "進行中",
    icon: "🗳️",
    events: [
      "即時開票",
      "結果分析", 
      "投票日動態",
      "立委罷免案",
      "高虹安罷免案",
      "罷免案日程",
      "投票須知",
      "其他文章"
    ],
    connectionMap: "罷免案涉及國民黨24位立委及新竹市長高虹安，共25案。第一波投票於7月26日舉行，全數被否決。第二波7案將於8月23日舉行，主要針對特定立委的罷免投票。",
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
      "結果分析": {
        title: "投票結果深度分析",
        summary: "分析罷免投票結果的背後原因、政治影響及未來發展趨勢。",
        articles: [
          { 
            id: 201, 
            title: "美學者：大罷免未過不影響台美互動 須持續深化互信", 
            views: "9.7k", 
            date: "2025/7/29 10:45", 
            author: "中央社",
            category: "專題報導",
            sourceCount: 5,
            shortSummary: "美國學者分析指出，台灣的罷免案結果不會影響台美關係發展，但雙方需要持續深化互信關係，在國防、經濟等領域加強合作。",
            relatedNews: [
              { id: 2011, title: "台美關係發展趨勢" },
              { id: 2012, title: "國際學者觀點" },
              { id: 2013, title: "外交政策影響" }
            ],
            keywords: ["台美", "外交", "學者"]
          },
          { 
            id: 202, 
            title: "大罷免結果對台美影響 智庫學者：取決在野國防路線", 
            views: "7.3k", 
            date: "2025/7/29 07:14", 
            author: "中央社",
            category: "專題報導",
            sourceCount: 3,
            shortSummary: "智庫學者認為，罷免案結果對台美關係的影響主要取決於在野黨在國防政策上的立場，以及是否願意與美方保持良好溝通。",
            relatedNews: [
              { id: 2021, title: "國防政策分析" },
              { id: 2022, title: "智庫研究報告" },
              { id: 2023, title: "政策影響評估" }
            ],
            keywords: ["國防", "政策", "智庫"]
          }
        ]
      },
      "投票日動態": {
        title: "投票日現場直擊",
        summary: "投票日當天的現場情況、選民反應及重要事件。",
        articles: [
          { 
            id: 301, 
            title: "大罷免失敗 罷團開票晚會感傷提前結束", 
            views: "6.4k", 
            date: "2025/7/26 19:54", 
            author: "中央社",
            category: "專題報導",
            sourceCount: 2,
            shortSummary: "罷免團體在開票晚會上看到結果不如預期，現場氣氛感傷，活動提前結束。許多支持者表示失望但仍會繼續關注相關議題。",
            relatedNews: [
              { id: 3011, title: "罷免團體反應" },
              { id: 3012, title: "支持者心聲" },
              { id: 3013, title: "後續行動計劃" }
            ],
            keywords: ["罷免", "團體", "反應"]
          }
        ]
      },
      "立委罷免案": {
        title: "立委罷免案詳情",
        summary: "針對24位國民黨立委的罷免案詳細資訊及背景。",
        articles: [
          { 
            id: 401, 
            title: "24位國民黨立委罷免案完整名單", 
            views: "13.1k", 
            date: "2025/7/25", 
            author: "中央社",
            category: "專題報導",
            sourceCount: 6,
            shortSummary: "完整列出24位國民黨立委的罷免案詳細資訊，包括各立委的基本資料、罷免理由、連署人數等相關資訊。",
            relatedNews: [
              { id: 4011, title: "各立委背景資料" },
              { id: 4012, title: "罷免理由分析" },
              { id: 4013, title: "連署情況統計" }
            ],
            keywords: ["立委", "國民黨", "名單"]
          }
        ]
      },
      "高虹安罷免案": {
        title: "高虹安罷免案專題",
        summary: "新竹市長高虹安罷免案的詳細過程及結果。",
        articles: [
          { 
            id: 501, 
            title: "高虹安罷免案投票率創新高", 
            views: "16.3k", 
            date: "2025/7/26", 
            author: "中央社",
            category: "專題報導",
            sourceCount: 4,
            shortSummary: "新竹市長高虹安的罷免案投票率創下歷史新高，顯示新竹市民對此次罷免案的高度關注和參與。",
            relatedNews: [
              { id: 5011, title: "新竹市民反應" },
              { id: 5012, title: "高虹安回應" },
              { id: 5013, title: "政治影響分析" }
            ],
            keywords: ["高虹安", "新竹", "投票率"]
          }
        ]
      },
      "罷免案日程": {
        title: "罷免案重要時程",
        summary: "罷免案的重要時間節點及後續發展。",
        articles: [
          { 
            id: 601, 
            title: "第二波罷免案8月23日舉行", 
            views: "10.2k", 
            date: "2025/7/28", 
            author: "中央社",
            category: "專題報導",
            sourceCount: 3,
            shortSummary: "第二波共7個罷免案將於8月23日舉行投票，包括國民黨立委馬文君、游顥、羅明才、江啟臣、楊瓊瓔、顏寬恒、林思銘。",
            relatedNews: [
              { id: 6011, title: "第二波罷免名單" },
              { id: 6012, title: "投票準備工作" },
              { id: 6013, title: "時程安排" }
            ],
            keywords: ["第二波", "罷免", "時程"]
          }
        ]
      },
      "投票須知": {
        title: "投票相關資訊",
        summary: "罷免投票的相關規定、注意事項及投票指南。",
        articles: [
          { 
            id: 701, 
            title: "罷免投票資格及注意事項", 
            views: "12.7k", 
            date: "2025/7/24", 
            author: "中央社",
            category: "專題報導",
            sourceCount: 5,
            shortSummary: "詳細說明罷免投票的資格條件、投票程序、注意事項等相關規定，幫助選民了解如何正確參與投票。",
            relatedNews: [
              { id: 7011, title: "投票資格查詢" },
              { id: 7012, title: "投票程序說明" },
              { id: 7013, title: "注意事項提醒" }
            ],
            keywords: ["投票", "資格", "程序"]
          }
        ]
      },
      "其他文章": {
        title: "相關新聞報導",
        summary: "與罷免案相關的其他新聞及評論文章。",
        articles: [
          { 
            id: 801, 
            title: "學者分析：罷免案對台灣民主的影響", 
            views: "9.8k", 
            date: "2025/7/27", 
            author: "中央社",
            category: "專題報導",
            sourceCount: 4,
            shortSummary: "政治學者分析罷免案對台灣民主發展的影響，探討罷免制度在民主政治中的角色和意義。",
            relatedNews: [
              { id: 8011, title: "民主制度檢討" },
              { id: 8012, title: "學者觀點彙整" },
              { id: 8013, title: "制度影響評估" }
            ],
            keywords: ["學者", "民主", "制度"]
          }
        ]
      }
    }
  }
};

function SpecialReportDetail() {
  const { id } = useParams();
  const report = specialReportData[id];
  const [activeEvent, setActiveEvent] = useState(report?.events[0] || '');
  const [expandedCards, setExpandedCards] = useState({});
  const sectionRefs = useRef({});
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');

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

  const handleSendMessage = () => {
    if (!chatInput.trim()) return;
    const userMsg = {
      id: Date.now(),
      text: chatInput,
      isOwn: true,
      time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })
    };
    setChatMessages((prev) => [...prev, userMsg]);
    setChatInput('');

    setTimeout(() => {
      const reply = {
        id: Date.now() + 1,
        text: `關於「${report.title}」這個專題，我可以為您提供深入分析。您提到的內容與專題中的「${activeEvent}」部分相關。需要我為您詳細解釋某個特定觀點嗎？`,
        isOwn: false,
        time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })
      };
      setChatMessages((prev) => [...prev, reply]);
    }, 1000);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') handleSendMessage();
  };

  const quickPrompts = ["分析這個專題", "相關背景資訊", "專家觀點", "未來發展趨勢"];

  return (
    <div className="srdPage">
      <div className="srdMain">
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

            {/* 專題聊天室 */}
            <div className="srdTopicChat">
              <div className="srdChatHeader">
                <div className="srdChatIcon">💬</div>
                <div>
                  <h4 className="srdChatTitle">專題討論</h4>
                  <p className="srdChatDesc">與AI助手討論這個專題的相關議題</p>
                </div>
              </div>

              <div className="srdQuickPrompts">
                {quickPrompts.map((p) => (
                  <button
                    key={p}
                    className="srdPromptBtn"
                    type="button"
                    onClick={() => setChatInput(p)}
                  >
                    {p}
                  </button>
                ))}
              </div>

              <div className="srdChatMessages">
                {chatMessages.length === 0 && (
                  <div className="srdMsg">
                    歡迎討論「{report.title}」這個專題！您可以詢問任何相關問題。
                  </div>
                )}
                {chatMessages.map((m) => (
                  <div key={m.id} className={`srdMsg ${m.isOwn ? 'is-own' : ''}`}>
                    {m.text}
                  </div>
                ))}
              </div>

              <input
                type="text"
                className="srdChatInput"
                placeholder="輸入您的問題或觀點..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyPress={handleKeyPress}
              />
              <button
                className="srdSendBtn"
                type="button"
                onClick={handleSendMessage}
                disabled={!chatInput.trim()}
              >
                發送訊息
              </button>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}

export default SpecialReportDetail;