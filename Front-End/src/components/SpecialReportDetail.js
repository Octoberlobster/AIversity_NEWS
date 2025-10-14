import React, { useState, useRef, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import ReactMarkdown from 'react-markdown';
import TopicChatRoom from './TopicChatRoom';
import UnifiedNewsCard from './UnifiedNewsCard';
import { useSupabase } from './supabase';
import { createHeaderVisualization } from './FiveW1HVisualization';
import { useLanguageFields } from '../utils/useLanguageFields';
import './../css/SpecialReportDetail.css';

function SpecialReportDetail() {
  const { t } = useTranslation();
  const { getCurrentLanguage, getFieldName, getMultiLanguageSelect } = useLanguageFields();
  const { id } = useParams();
  
  const getLanguageRoute = (path) => {
    return `/${getCurrentLanguage()}${path}`;
  };
  const [report, setReport] = useState(null);
  const [branches, setBranches] = useState([]); // 專題分支列表
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeEvent, setActiveEvent] = useState(null); // 目前導覽中的分支 ID
  const [isChatOpen, setIsChatOpen] = useState(false);
  const sectionRefs = useRef({});
  const supabase = useSupabase();
  const [is5W1HExpanded, setIs5W1HExpanded] = useState(false);
  const expanded5W1HRef = useRef(null);
  const expandedVizInstanceRef = useRef(null);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [integrationReport, setIntegrationReport] = useState('');
  
  // 專家分析（從資料庫讀取）
  const [expertAnalysis, setExpertAnalysis] = useState([]);
  const [analysisLoading, setAnalysisLoading] = useState(true);
  
  // 專家分析彈出視窗狀態
  const [selectedExpert, setSelectedExpert] = useState(null);
  const [isExpertModalOpen, setIsExpertModalOpen] = useState(false);

  // 開啟專家分析彈出視窗
  const openExpertModal = (expert) => {
    setSelectedExpert(expert);
    setIsExpertModalOpen(true);
  };

  // 關閉專家分析彈出視窗
  const closeExpertModal = () => {
    setIsExpertModalOpen(false);
    setTimeout(() => setSelectedExpert(null), 300); // 等待動畫結束後清除
  };

  // 截斷文字函數
  const truncateText = (text, maxLength = 48) => {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  // 處理5W1H關聯圖顯示
  useEffect(() => {
    if (is5W1HExpanded && expanded5W1HRef.current && !expandedVizInstanceRef.current) {
      const timer = setTimeout(() => {
        if (expanded5W1HRef.current) {
          expandedVizInstanceRef.current = createHeaderVisualization(
            expanded5W1HRef, 
            report?.topic_title || t('fiveW1H.defaultTitle'),
            true,
            report?.topic_id || id,
            t,
            getFieldName
          );
        }
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [is5W1HExpanded, report?.topic_title, report?.topic_id, id, t, getFieldName]);

  const close5W1HExpanded = () => {
    setIs5W1HExpanded(false);
    if (expandedVizInstanceRef.current) {
      expandedVizInstanceRef.current = null;
    }
  };

  const handle5W1HClick = () => {
    setIs5W1HExpanded(true);
  };

  // 生成專題報告功能
  const generateIntegrationReport = async () => {
    setIsReportModalOpen(true);
    
    // 模擬報告生成過程
    setIntegrationReport(t('specialReportDetail.modal.report.generating'));
    
    // 模擬API調用延遲
    setTimeout(() => {
      setIntegrationReport(report.report || '');
    }, 2000);
  };

  // 載入專家分析資料
  useEffect(() => {
    const fetchExpertAnalysis = async () => {
      if (!id || !supabase) return;
      
      setAnalysisLoading(true);
      
      try {
        // 查詢專家分析，支援多語言
        const analyzeMultiLangFields = ['analyze'];
        const analyzeSelectFields = getMultiLanguageSelect(analyzeMultiLangFields);
        
        const { data, error } = await supabase
          .from('pro_analyze_topic')
          .select(`analyze_id, category, ${analyzeSelectFields}`)
          .eq('topic_id', id);
        
        if (error) {
          console.error(`Error fetching expert analysis for topic ${id}:`, error);
          setExpertAnalysis([]);
          setAnalysisLoading(false);
          return;
        }

        // 處理多語言分析資料
        const analysisData = (data || []).map(item => ({
          analyze_id: item.analyze_id,
          category: item.category,
          analyze: item[getFieldName('analyze')] || item.analyze
        }));
        
        setExpertAnalysis(analysisData);
      } catch (error) {
        console.error(`Error fetching expert analysis for topic ${id}:`, error);
        setExpertAnalysis([]);
      } finally {
        setAnalysisLoading(false);
      }
    };

    fetchExpertAnalysis();
  }, [id, supabase, getFieldName, getMultiLanguageSelect]);

  // 獲取專題詳細資料
  const fetchSpecialReportDetail = async () => {
    try {
      setLoading(true);
      setError(null);

      // 專題基本資訊
      const topicMultiLangFields = ['topic_title', 'topic_short', 'topic_long', 'report'];
      const topicSelectFields = getMultiLanguageSelect(topicMultiLangFields);
      
      const { data: topicData, error: topicError } = await supabase
        .from('topic')
        .select(`topic_id, ${topicSelectFields}, generated_date, who_talk`)
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
      const branchMultiLangFields = ['topic_branch_title', 'topic_branch_content'];
      const branchSelectFields = getMultiLanguageSelect(branchMultiLangFields);
      
      const { data: branchData, error: branchError } = await supabase
        .from('topic_branch')
        .select(`topic_branch_id, topic_id, ${branchSelectFields}`)
        .eq('topic_id', id);
      if (branchError) console.warn('無法獲取分支列表:', branchError);

      const normalizedBranches = (branchData || []).map((b, idx) => ({
        id: b.topic_branch_id,
        name: b[getFieldName('topic_branch_title')] || b.topic_branch_title || `分支 ${idx + 1}`,
        summary: b[getFieldName('topic_branch_content')] || b.topic_branch_content || ''
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

            const newsMultiLangFields = ['news_title', 'ultra_short'];
            const newsSelectFields = getMultiLanguageSelect(newsMultiLangFields);
            
            const { data: stories, error: storiesError } = await supabase
              .from('single_news')
              .select(`story_id, ${newsSelectFields}, category, generated_date, total_articles`)
              .in('story_id', storyIds);
            if (storiesError) {
              console.warn(`無法獲取分支 ${branch.id} 的新聞內容:`, storiesError);
              return { ...branch, news: [] };
            }

            const customData = (stories || []).map(s => ({
              story_id: s.story_id,
              title: s[getFieldName('news_title')] || s.news_title,
              category: s.category, // 若需中文化，可在這裡自行映射
              date: s.generated_date,
              author: 'Gemini',
              sourceCount: s.total_articles,
              shortSummary: s[getFieldName('ultra_short')] || s.ultra_short,
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
        topic_title: topicData[getFieldName('topic_title')] || topicData.topic_title,
        description: topicData[getFieldName('topic_long')] || topicData[getFieldName('topic_short')] || topicData.topic_long || topicData.topic_short || '',
        articles: newsCountData ? newsCountData.length : 0,
        views: `${(Math.floor(Math.random() * 20) + 1).toFixed(1)}k`,
        lastUpdate: topicData.generated_date ? new Date(topicData.generated_date).toLocaleDateString('zh-TW') : '',
        report: topicData[getFieldName('report')] || topicData.report || '',
        who_talk: topicData.who_talk || ''
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
  }, [id, supabase, getCurrentLanguage()]);

  if (loading) {
    return (
      <div className="srdPage">
        <div className="srdMain">
          <div style={{ textAlign: 'center', padding: '3rem' }}>
            <h2>{t('specialReportDetail.loading')}</h2>
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
            <h2>{t('specialReportDetail.error.notFound')}</h2>
            <p>{error || t('specialReportDetail.error.fallback')}</p>
            <Link to={getLanguageRoute("/special-reports")} style={{ color: '#667eea' }}>
              {t('specialReportDetail.backToList')}
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
        title={isChatOpen ? t('specialReportDetail.chat.close') : t('specialReportDetail.chat.open')}
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

      <div className="srdMain">
        {/* Header */}
        <div className="srdHeader">
          <div className="srdHeader__content">
            <br />
            <h1 className="srdHeader__title">{report.topic_title}</h1>
            <p className="srdHeader__summary">{report.description}</p>
            <div className="srdHeader__meta">
              <div className="srdHeader__metaItem">
                <span>📅</span>
                <span>{report.lastUpdate}</span>
              </div>
              <div className="srdHeader__metaItem">
                <span>📄</span>
                <span>{report.articles} {t('specialReportDetail.header.articlesCount')}</span>
              </div>
              <button 
                className="srdHeader__reportBtn"
                onClick={generateIntegrationReport}
                title={t('specialReportDetail.header.reportButtonTitle')}
              >
                📊 {t('specialReportDetail.header.reportButton')}
              </button>
              <button 
                className="srdHeader__5w1hBtn"
                onClick={handle5W1HClick}
                title="查看 5W1H 關聯圖"
              >
                🔍 5W1H {t('specialReportDetail.header.relationMap')}
              </button>
            </div>
          </div>
          
          {/* 專家分析區塊 - 手風琴模式 */}
          <div className="srdHeader__expertAnalysis">
            <h4 className="srdHeader__expertTitle">
              💡 {t('specialReportDetail.header.expertAnalysis')}
            </h4>
            <div className="srdHeader__expertContent">
              {analysisLoading ? (
                <div className="srdHeader__analysisLoading">
                  <div className="srdHeader__spinner"></div>
                  <span>{t('specialReportDetail.header.loadingAnalysis')}</span>
                </div>
              ) : expertAnalysis && expertAnalysis.length > 0 ? (
                <div className="srdHeader__expertCards">
                  {expertAnalysis.map((analysis, index) => {
                    // 確保 analyze 是物件
                    const analyzeData = typeof analysis.analyze === 'string' 
                      ? JSON.parse(analysis.analyze) 
                      : analysis.analyze;
                    
                    const expertData = {
                      ...analysis,
                      analyzeData
                    };
                    
                    return (
                      <div 
                        className="srdHeader__expertCard"
                        key={analysis.analyze_id || index}
                        onClick={() => openExpertModal(expertData)}
                      >
                        <div className="srdHeader__expertCardHeader">
                          <span className="srdHeader__categoryTag">
                            {analyzeData?.Role || analysis.category || t('specialReportDetail.header.expert')}
                          </span>
                        </div>
                        <div className="srdHeader__expertCardPreview">
                          {truncateText(analyzeData?.Analyze || t('specialReportDetail.header.noContent'))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="srdHeader__noAnalysis">
                  {t('specialReportDetail.header.noExpertAnalysis')}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Layout */}
        <div className="srdLayout">
          {/* Sidebar - 移到左邊 */}
          <aside className="srdSidebar srdSidebar--left">
            <div className="srdSidebarCard">
              <h3 className="srdSidebarTitle">{t('specialReportDetail.navigation.title')}</h3>
              <nav className="srdNav">
                {branches.length === 0 ? (
                  <div className="srdNavEmpty">{t('specialReportDetail.navigation.noBranches')}</div>
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
                      <span>{branch.news?.length || 0} {t('specialReportDetail.section.newsCount')}</span>
                    </div>
                    {branch.news?.length > 0 && (
                      <div className="srdSection__metaItem">
                        <span>📊</span>
                        <span>{t('specialReportDetail.section.sourcesTotal', { count: branch.news.reduce((sum, n) => sum + (n.sourceCount || 0), 0) })}</span>
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
                        <span>{t('specialReportDetail.section.noContent')}</span>
                      </div>
                    )}
                  </div>
                </div>
              </section>
            ))}
          </div>
        </div>
      </div>

      {/* 側邊聊天室 */}
      <div className={`chat-sidebar ${isChatOpen ? 'open' : ''}`}>
        <div className="chat-sidebar-content">
          <TopicChatRoom 
            topic_id={id} 
            topic_title={report.topic_title}
            topic_who_talk={report.who_talk}
            topicExperts={expertAnalysis} 
            onClose={() => setIsChatOpen(false)} 
          />
        </div>
      </div>
      {/* 新增：5W1H關聯圖放大模態框 */}
      {is5W1HExpanded && (
        <div className="srd5W1HModal" onClick={close5W1HExpanded}>
          <div className="srd5W1HModal__content" onClick={(e) => e.stopPropagation()}>
            <button 
              className="srd5W1HModal__closeBtn" 
              onClick={close5W1HExpanded}
              aria-label={t('specialReportDetail.modal.5w1h.close')}
            >
              ✕
            </button>
            <div className="srd5W1HModal__title">
               <h2>{report.topic_title} - {t('specialReportDetail.modal.5w1h.title')}</h2>
            </div>
            <div className="srd5W1HModal__visualization" ref={expanded5W1HRef}>
              <div id="expanded-mindmap" style={{ width: '100%', height: '100%' }}></div>
            </div>
          </div>
        </div>
      )}

      {/* 新增：專題報告彈出式視窗 */}
      {isReportModalOpen && (
        <div className="srdReportModal" onClick={() => setIsReportModalOpen(false)}>
          <div className="srdReportModal__content" onClick={(e) => e.stopPropagation()}>
            <div className="srdReportModal__header">
              <h2 className="srdReportModal__title">📊 {t('specialReportDetail.modal.report.title')}</h2>
              <button 
                className="srdReportModal__close"
                onClick={() => setIsReportModalOpen(false)}
                title={t('specialReportDetail.modal.report.close')}
              >
                ✕
              </button>
            </div>
            <div className="srdReportModal__body">
              {integrationReport === t('specialReportDetail.modal.report.generating') ? (
                <div className="srdReportModal__loading">
                  <div className="srdReportModal__spinner"></div>
                  <p>{t('specialReportDetail.modal.report.generatingDetail')}</p>
                </div>
              ) : (
                <div className="srdReportModal__report">
                  <ReactMarkdown>{integrationReport}</ReactMarkdown>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 專家分析彈出視窗 */}
      {isExpertModalOpen && selectedExpert && (
        <div className="srdExpertModal" onClick={closeExpertModal}>
          <div className="srdExpertModal__content" onClick={(e) => e.stopPropagation()}>
            <div className="srdExpertModal__header">
              <div className="srdExpertModal__title">
                <span className="srdExpertModal__icon">👤</span>
                <span className="srdHeader__categoryTag">
                  {selectedExpert.analyzeData?.Role || selectedExpert.category || t('specialReportDetail.header.expert')}
                </span>
              </div>
              <button 
                className="srdExpertModal__close"
                onClick={closeExpertModal}
                title={t('specialReportDetail.modal.expert.close')}
              >
                ✕
              </button>
            </div>
            <div className="srdExpertModal__body">
              <div className="srdExpertModal__analysis">
                {selectedExpert.analyzeData?.Analyze || t('specialReportDetail.header.noContent')}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SpecialReportDetail;