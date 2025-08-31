import React, { useState, useRef, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import TopicChatRoom from './TopicChatRoom';
import UnifiedNewsCard from './UnifiedNewsCard';
import { useSupabase } from './supabase';
import { createHeaderVisualization } from './FiveW1HVisualization';
import './../css/SpecialReportDetail.css';

function SpecialReportDetail() {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [branches, setBranches] = useState([]); // 專題分支列表
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeEvent, setActiveEvent] = useState(null); // 目前導覽中的分支 ID
  const [isChatOpen, setIsChatOpen] = useState(false);
  const sectionRefs = useRef({});
  const supabase = useSupabase();
  const headerImageRef = useRef(null);
  const vizInstanceRef = useRef(null);
  const [is5W1HExpanded, setIs5W1HExpanded] = useState(false);
  const expanded5W1HRef = useRef(null);
  const expandedVizInstanceRef = useRef(null);

  useEffect(() => {
    const initializeHeaderVisualization = () => {
      if (headerImageRef.current && !vizInstanceRef.current) {
        // 使用新的 createHeaderVisualization 函數
        vizInstanceRef.current = createHeaderVisualization(
          headerImageRef, 
          report?.topic_title || "專題分析",
          false, // isModal
          report?.topic_id || id // 傳遞 topic_id，如果沒有就用 URL 的 id
        );
      }
    };

    // 延遲初始化確保 DOM 就緒
    const timer = setTimeout(initializeHeaderVisualization, 100);
    
    return () => {
      clearTimeout(timer);
      // 清理實例
      if (vizInstanceRef.current) {
        vizInstanceRef.current = null;
      }
    };
  }, [report?.topic_title, report?.topic_id, id]);

  // 新增：處理5W1H關聯圖點擊放大
  useEffect(() => {
    if (is5W1HExpanded && expanded5W1HRef.current && !expandedVizInstanceRef.current) {
      // 延遲初始化確保模態框DOM就緒
      const timer = setTimeout(() => {
        if (expanded5W1HRef.current) {
          expandedVizInstanceRef.current = createHeaderVisualization(
            expanded5W1HRef, 
            report?.topic_title || "專題分析",
            true, // 標記為模態框模式
            report?.topic_id || id // 傳遞 topic_id
          );
        }
      }, 100);
      
      return () => clearTimeout(timer);
    }
  }, [is5W1HExpanded, report?.topic_title, report?.topic_id, id]);

  // 新增：關閉5W1H關聯圖放大視窗
  const close5W1HExpanded = () => {
    setIs5W1HExpanded(false);
    // 清理放大的視覺化實例
    if (expandedVizInstanceRef.current) {
      expandedVizInstanceRef.current = null;
    }
  };

  // 新增：點擊5W1H關聯圖放大
  const handle5W1HClick = () => {
    setIs5W1HExpanded(true);
  };
  // 獲取專題詳細資料
  const fetchSpecialReportDetail = async () => {
    try {
      setLoading(true);
      setError(null);

      // 專題基本資訊
      const { data: topicData, error: topicError } = await supabase
        .from('topic')
        .select('topic_id, topic_title, topic_short, topic_long, generated_date')
        .eq('topic_id', id)
        .single();
      if (topicError) throw new Error(`無法獲取專題資訊: ${topicError.message}`);
      if (!topicData) throw new Error('專題不存在');

      // 專題新聞數量
      const { data: newsCountData, error: countError } = await supabase
        .from('topic_news_map')
        .select('topic_id')
        .eq('topic_id', id);
      if (countError) console.warn('無法獲取新聞數量:', countError);

      // 專題分支列表（topic_branch）
      const { data: branchData, error: branchError } = await supabase
        .from('topic_branch')
        .select('topic_branch_id, topic_id, topic_branch_title, topic_branch_content')
        .eq('topic_id', id);
      if (branchError) console.warn('無法獲取分支列表:', branchError);

      const normalizedBranches = (branchData || []).map((b, idx) => ({
        id: b.topic_branch_id,
        name: b.topic_branch_title || `分支 ${idx + 1}`,
        summary: b.topic_branch_content || ''
      }));

      // 針對每個分支抓取對應新聞（topic_branch__map -> single_news），並轉為 UnifiedNewsCard 的 customData
      const branchesWithNews = await Promise.all(
        normalizedBranches.map(async (branch) => {
          try {
            const { data: mapRows, error: mapError } = await supabase
              .from('topic_branch_news_map')
              .select('story_id')
              .eq('topic_branch_id', branch.id);
            if (mapError) {
              console.warn(`無法獲取分支 ${branch.id} 的故事映射:`, mapError);
              return { ...branch, news: [] };
            }
            const storyIds = (mapRows || []).map(r => r.story_id).filter(Boolean);
            if (!storyIds || storyIds.length === 0) {
              return { ...branch, news: [] };
            }

            const { data: stories, error: storiesError } = await supabase
              .from('single_news')
              .select('story_id, news_title, category, generated_date, total_articles, ultra_short')
              .in('story_id', storyIds);
            if (storiesError) {
              console.warn(`無法獲取分支 ${branch.id} 的新聞內容:`, storiesError);
              return { ...branch, news: [] };
            }

            const customData = (stories || []).map(s => ({
              story_id: s.story_id,
              title: s.news_title,
              category: s.category, // 若需中文化，可在這裡自行映射
              date: s.generated_date,
              author: 'Gemini',
              sourceCount: s.total_articles,
              shortSummary: s.ultra_short,
              relatedNews: [],
              views: 0,
              keywords: [],
              terms: []
            }));

            return { ...branch, news: customData };
          } catch (e) {
            console.warn(`分支 ${branch.id} 抓取新聞時發生錯誤:`, e);
            return { ...branch, news: [] };
          }
        })
      );

      const reportData = {
        topic_id: topicData.topic_id,
        topic_title: topicData.topic_title,
        description: topicData.topic_long || topicData.topic_short || '',
        articles: newsCountData ? newsCountData.length : 0,
        views: `${(Math.floor(Math.random() * 20) + 1).toFixed(1)}k`,
        lastUpdate: topicData.generated_date ? new Date(topicData.generated_date).toLocaleDateString('zh-TW') : ''
      };

  setReport(reportData);
  setBranches(branchesWithNews);
  if (branchesWithNews.length > 0) setActiveEvent(branchesWithNews[0].id);
    } catch (err) {
      setError(err.message);
      console.error('獲取專題詳細資料失敗:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      fetchSpecialReportDetail();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, supabase]);

  if (loading) {
    return (
      <div className="srdPage">
        <div className="srdMain">
          <div style={{ textAlign: 'center', padding: '3rem' }}>
            <h2>載入中...</h2>
          </div>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="srdPage">
        <div className="srdMain">
          <div style={{ textAlign: 'center', padding: '3rem' }}>
            <h2>專題報導不存在</h2>
            <p>{error || '請返回專題報導列表'}</p>
            <Link to="/special-reports" style={{ color: '#667eea' }}>
              返回專題報導
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const handleNavClick = (branchId) => {
    setActiveEvent(branchId);
    const targetRef = sectionRefs.current[branchId];
    if (targetRef) {
      targetRef.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  // 無需本地卡片展開邏輯，UnifiedNewsCard 內建處理

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
            <h1 className="srdHeader__title">{report.topic_title}</h1>
            <p className="srdHeader__summary">{report.description}</p>
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
          <div className="srdHeader__image" ref={headerImageRef} onClick={handle5W1HClick} style={{ cursor: 'pointer' }}>
            <div id="header-mindmap" style={{ width: '100%', height: '100%' }}></div>
            <div className="srdHeader__imageOverlay">
              <span className="srdHeader__imageHint">點擊放大</span>
            </div>
          </div>
        </div>

        {/* Layout */}
        <div className="srdLayout">
          <div className="srdMainCol">
            {branches.map((branch) => (
              <section
                key={branch.id}
                className="srdSection"
                ref={(el) => {
                  sectionRefs.current[branch.id] = el;
                }}
              >
                <div className="srdSection__header">
                  <h2 className="srdSection__title">📰{branch.name}</h2>
                  {branch.summary && (
                    <div className="srdSection__summary">{branch.summary}</div>
                  )}
                  <div className="srdSection__meta">
                    <div className="srdSection__metaItem">
                      <span>📄</span>
                      <span>{branch.news?.length || 0} 篇新聞</span>
                    </div>
                    {branch.news?.length > 0 && (
                      <div className="srdSection__metaItem">
                        <span>📊</span>
                        <span>共 {branch.news.reduce((sum, n) => sum + (n.sourceCount || 0), 0)} 來源</span>
                      </div>
                    )}
                  </div>
                  <div className="srdSection__progress"></div>
                </div>

                <div className="srdSection__content">
                  {/* 用 UnifiedNewsCard 呈現該分支的新聞：使用 customData 精準渲染 */}
                  <div className="uncContainer">
                    {branch.news && branch.news.length > 0 ? (
                      <UnifiedNewsCard customData={branch.news} instanceId={`branch_${branch.id}`} />
                    ) : (
                      <div style={{ 
                        textAlign: 'center', padding: '2rem', color: '#6b7280',
                        backgroundColor: '#f8fafc', borderRadius: '12px', 
                        border: '2px dashed #d1d5db',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        gap: '0.5rem', fontSize: '1.1rem'
                      }}>
                        <span>📭</span>
                        <span>此分支暫無新聞內容</span>
                      </div>
                    )}
                  </div>
                </div>
              </section>
            ))}
          </div>

          {/* Sidebar */}
          <aside className="srdSidebar">
            <div className="srdSidebarCard">
              <h3 className="srdSidebarTitle">專題導覽</h3>
              <nav className="srdNav">
                {branches.length === 0 ? (
                  <div className="srdNavEmpty">尚無分支</div>
                ) : (
                  branches.map((b) => (
                    <button
                      key={b.id}
                      className={`srdNavItem ${activeEvent === b.id ? 'is-active' : ''}`}
                      onClick={() => handleNavClick(b.id)}
                      type="button"
                    >
                      {b.name}
                    </button>
                  ))
                )}
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
          <TopicChatRoom topic_id={id} topic_title={report.topic_title} />
        </div>
      </div>
      {/* 新增：5W1H關聯圖放大模態框 */}
      {is5W1HExpanded && (
        <div className="srd5W1HModal" onClick={close5W1HExpanded}>
          <div className="srd5W1HModal__content" onClick={(e) => e.stopPropagation()}>
            <button 
              className="srd5W1HModal__closeBtn" 
              onClick={close5W1HExpanded}
              aria-label="關閉"
            >
              ✕
            </button>
            <div className="srd5W1HModal__title">
              <h2>{report.title} - 5W1H關聯分析</h2>
            </div>
            <div className="srd5W1HModal__visualization" ref={expanded5W1HRef}>
              <div id="expanded-mindmap" style={{ width: '100%', height: '100%' }}></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SpecialReportDetail;