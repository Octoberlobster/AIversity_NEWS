import React, { useState, useEffect, useMemo, useRef} from 'react';
import { useParams, Link} from 'react-router-dom';
import './../css/NewsDetail.css';
import ChatRoom from './ChatRoom';
import TermTooltip from './TermTooltip';
import { useSupabase } from './supabase';
import { fetchJson } from './api';

// 從資料庫動態載入術語定義的函數
const loadTermDefinitions = async (supabase) => {
  try {
    const { data, error } = await supabase
      .from('term')
      .select('term, term_id, definition, example');
    
    if (error) {
      console.error('載入術語定義時發生錯誤:', error);
    }

    // 轉換為物件格式
    const definitions = {};
    data.forEach(item => {
      if (item.term && item.definition) {
        definitions[item.term_id] = {
          term: item.term,
          definition: item.definition,
          example: item.example || null
        };
      }
    });

    return definitions
  } catch (error) {
    console.error('載入術語定義時發生錯誤:', error);
  }
};

const experts = [
  { id: 1, name: "政治專家", category: "Politics" },
  { id: 2, name: "台灣議題分析師", category: "Taiwan News" },
  { id: 3, name: "國際專家", category: "International News" },
  { id: 4, name: "科技專家", category: "Science & Technology" },
  { id: 5, name: "生活達人", category: "Lifestyle & Consumer News" },
  { id: 6, name: "體育專家", category: "Sports" },
  { id: 7, name: "娛樂專家", category: "Entertainment" },
  { id: 8, name: "財經專家", category: "Business & Finance" },
  { id: 9, name: "健康顧問", category: "Health & Wellness" },
];

function NewsDetail() {
  const { id } = useParams();
  // 移除了 showLongContent state，直接顯示完整內容
  const [tooltipTerm, setTooltipTerm] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const [showAllSources, setShowAllSources] = useState(false);
  const [newsData, setNewsData] = useState(null);
  const [newsImage, setNewsImage] = useState(null);
  const [newsUrl, setNewsUrl] = useState(null);
  const [newsKeywords, setNewsKeywords] = useState([]);
  const [termDefinitions, setTermDefinitions] = useState({});
  const [newsTerms, setNewsTerms] = useState([]);
  const [relatedNews, setRelatedNews] = useState([]);
  const [relatedTopics, setRelatedTopics] = useState([]);
  const [positionData, setPositionData] = useState({ positive: [], negative: [] }); // 正反方立場資料
  const [positionLoading, setPositionLoading] = useState(true); // 正反方立場載入狀態
  const [expertAnalysis, setExpertAnalysis] = useState([]); // 專家分析資料
  const [analysisLoading, setAnalysisLoading] = useState(true); // 專家分析載入狀態
  const [showContent, setShowContent] = useState('loading'); // 'loading', 'position', 'expert', 'none'
  const [isChatOpen, setIsChatOpen] = useState(false); // 聊天室開關狀態
  
  // 文字選取和溯源驗證相關狀態
  const [selectedText, setSelectedText] = useState('');
  const [selectionPosition, setSelectionPosition] = useState({ x: 0, y: 0 });
  const [showFactCheckButton, setShowFactCheckButton] = useState(false);
  
  // ChatRoom組件的ref
  const chatRoomRef = useRef(null);

  // 確保頁面載入時滾動到頂部
  useEffect(() => {
    window.scrollTo(0, 0);
    setShowAllSources(false);
    setPositionLoading(true); // 重置載入狀態
    setAnalysisLoading(true); // 重置專家分析載入狀態
    setShowContent('loading'); // 重置顯示狀態
  }, [id]); // 當 id 改變時執行

  // 使用 Supabase 客戶端獲取新聞數據
  const supabaseClient = useSupabase();

  // 載入術語定義
  useEffect(() => {
    const initTermDefinitions = async () => {
      const definitions = await loadTermDefinitions(supabaseClient);
      setTermDefinitions(definitions);
    };
    initTermDefinitions();
  }, [supabaseClient]);

  // 載入特定新聞的術語
  useEffect(() => {
    const fetchNewsTerms = async () => {
      if (!id || !supabaseClient) return;
      
      try {
        // 先從 term_map 獲取 term_id 列表
        const { data: termMapData, error: termMapError } = await supabaseClient
          .from('term_map')
          .select('term_id')
          .eq('story_id', id);
        
        if (termMapError) {
          console.error(`Error fetching term mapping for story ${id}:`, termMapError);
          setNewsTerms([]);
          return;
        }

        const termIds = termMapData?.map(item => item.term_id) || [];
        
        if (termIds.length === 0) {
          setNewsTerms([]);
          return;
        }

        // 根據 term_id 獲取實際的術語文字
        const { data: termsData, error: termsError } = await supabaseClient
          .from('term')
          .select('term_id, term, definition, example')
          .in('term_id', termIds);
        
        if (termsError) {
          console.error(`Error fetching terms for story ${id}:`, termsError);
          setNewsTerms([]);
          return;
        }

        const terms = termsData?.map(item => ({
          term: item.term,
          definition: item.definition,
          example: item.example
        })) || [];
        setNewsTerms(terms);
      } catch (error) {
        console.error(`Error fetching terms for story ${id}:`, error);
        setNewsTerms([]);
      }
    };

    fetchNewsTerms();
  }, [id, supabaseClient]);

  // 載入正反方立場資料
  useEffect(() => {
    const fetchPositionData = async () => {
      if (!id || !supabaseClient) {
        setPositionLoading(false);
        setShowContent('none');
        return;
      }
      
      setPositionLoading(true);
      
      try {
        const { data, error } = await supabaseClient
          .from('position')
          .select('positive, negative')
          .eq('story_id', id);
        
        if (error) {
          console.error(`Error fetching position data for story ${id}:`, error);
          setPositionData({ positive: [], negative: [] });
          setPositionLoading(false);
          // 如果正反方立場載入失敗，嘗試載入專家分析
          setShowContent('loadExpert');
          return;
        }

        const positionRow = data?.[0];
        if (positionRow && ((positionRow.positive && positionRow.positive.length > 0) || (positionRow.negative && positionRow.negative.length > 0))) {
          // 有正反方立場資料
          setPositionData({
            positive: positionRow.positive || [],
            negative: positionRow.negative || []
          });
          setShowContent('position');
        } else {
          // 沒有正反方立場資料，需要載入專家分析
          setPositionData({ positive: [], negative: [] });
          setShowContent('loadExpert');
        }
      } catch (error) {
        console.error(`Error fetching position data for story ${id}:`, error);
        setPositionData({ positive: [], negative: [] });
        setShowContent('loadExpert');
      } finally {
        setPositionLoading(false);
      }
    };

    fetchPositionData();
  }, [id, supabaseClient]);

  // 載入專家分析資料 - 只在沒有正反方立場時載入
  useEffect(() => {
    const fetchExpertAnalysis = async () => {
      if (!id || !supabaseClient || showContent !== 'loadExpert') {
        if (showContent === 'loadExpert') {
          setAnalysisLoading(false);
          setShowContent('none');
        }
        return;
      }
      
      setAnalysisLoading(true);
      
      try {
        const { data, error } = await supabaseClient
          .from('pro_analyze')
          .select('analyze_id, category, analyze')
          .eq('story_id', id);
        
        if (error) {
          console.error(`Error fetching expert analysis for story ${id}:`, error);
          setExpertAnalysis([]);
          setAnalysisLoading(false);
          setShowContent('none');
          return;
        }

        // 處理分析資料
        const analysisData = data || [];
        if (analysisData.length > 0) {
          setExpertAnalysis(analysisData);
          setShowContent('expert');
        } else {
          setExpertAnalysis([]);
          setShowContent('none');
        }
      } catch (error) {
        console.error(`Error fetching expert analysis for story ${id}:`, error);
        setExpertAnalysis([]);
        setShowContent('none');
      } finally {
        setAnalysisLoading(false);
      }
    };

    fetchExpertAnalysis();
  }, [id, supabaseClient, showContent]);

  useEffect(() => {
    const fetchNewsData = async () => {
      const { data, error } = await supabaseClient
        .from('single_news')
        .select('*')
        .eq('story_id', id);
      if (error) {
        console.error('Error fetching news data:', error);
      } else {
        const row = data?.[0];
        setNewsData(row ? {
          title: row.news_title,
          date: row.generated_date,
          author: 'Gemini',
          short: row.short,
          long: row.long,
          terms: [],
          keywords: [],
          source: [],
          category: row.category,
          story_id: row.story_id,
          who_talk: row.who_talk
        } : null);
      }
    };

    fetchNewsData();
  }, [id, supabaseClient]);

  useEffect(() => {
    const fetchNewsImage = async () => {
      const { data, error } = await supabaseClient
        .from('generated_image')
        .select('*')
        .eq('story_id', id);

      if (error) {
        console.error('Error fetching news image:', error);
        setNewsImage([]);
        return;
      }

      const processed = (data || []).map(item => {
        // 將純 base64 字串轉換為完整的 data URL
        const src = item.image ? `data:image/png;base64,${item.image}` : '';
        return {
          src,                               // 給 <img src={x} />
          description: item.description || '',
        };
      });

      setNewsImage(processed);
    };

    fetchNewsImage();
  }, [id, supabaseClient]);

  useEffect(() => {
    const fetchNewsImage = async () => {
      const { data, error } = await supabaseClient
        .from('cleaned_news')
        .select('article_title, article_url, media')
        .eq('story_id', id);

      if (error) {
        console.error('Error fetching news url:', error);
        setNewsUrl(null);
        return;
      }
      setNewsUrl(data);
    };

    fetchNewsImage();
  }, [id, supabaseClient]);

  useEffect(() => {
    const fetchNewsKeywords = async () => {
      const { data, error } = await supabaseClient
        .from('keywords_map')
        .select('keyword')
        .eq('story_id', id)
        .limit(3); // 限制為 3 個關鍵字

      if (error) {
        console.error('Error fetching news keywords:', error);
        setNewsKeywords([]);
        return;
      }
      setNewsKeywords(data);
    };

    fetchNewsKeywords();
  }, [id, supabaseClient]);

  // 載入相關新聞
  useEffect(() => {
    const fetchRelatedNews = async () => {
      if (!id || !supabaseClient) return;
      
      try {
        // 查詢相關新聞 - 找出以當前新聞為 src_story_id 的相關新聞
        const { data: relatedData, error: relatedError } = await supabaseClient
          .from('relative_news')
          .select(`
            dst_story_id,
            reason
          `)
          .eq('src_story_id', id);

        if (relatedError) {
          console.error('Error fetching related news:', relatedError);
          setRelatedNews([]);
          return;
        }

        // 如果有相關新聞，再查詢對應的新聞標題
        if (!relatedData || relatedData.length === 0) {
          setRelatedNews([]);
          return;
        }

        // 獲取所有目標新聞的 story_id
        const targetStoryIds = relatedData.map(item => item.dst_story_id);
        
        // 查詢目標新聞的詳細資料
        const { data: newsData, error: newsError } = await supabaseClient
          .from('single_news')
          .select('story_id, news_title')
          .in('story_id', targetStoryIds);

        if (newsError) {
          console.error('Error fetching related news titles:', newsError);
          setRelatedNews([]);
          return;
        }

        // 合併資料並進行資料清理
        const related = relatedData.map(relatedItem => {
          const newsItem = newsData?.find(n => n.story_id === relatedItem.dst_story_id);
          
          // 資料清理：如果 reason 過長，可能是錯誤的內容，截短它
          let reason = relatedItem.reason || '無相關性說明';
          if (reason.length > 200) {
            reason = reason.substring(0, 200) + '...';
          }
          
          // 確保有有效的標題
          let title = newsItem?.news_title || `新聞 ID: ${relatedItem.dst_story_id}`;
          if (!title.trim()) {
            title = `新聞 ID: ${relatedItem.dst_story_id}`;
          }
          
          return {
            id: relatedItem.dst_story_id,
            title: title.trim(),
            relevance: reason.trim()
          };
        });
        setRelatedNews(related);
      } catch (error) {
        console.error('Error fetching related news:', error);
        setRelatedNews([]);
      }
    };

    fetchRelatedNews();
  }, [id, supabaseClient]);

  // 載入相關專題
  useEffect(() => {
    const fetchRelatedTopics = async () => {
      if (!id || !supabaseClient) return;
      
      try {
        // 查詢相關專題 - 找出以當前新聞為 src_story_id 的相關專題
        const { data: relatedData, error: relatedError } = await supabaseClient
          .from('relative_topics')
          .select(`
            dst_topic_id,
            reason
          `)
          .eq('src_story_id', id);

        if (relatedError) {
          console.error('Error fetching related topics:', relatedError);
          setRelatedTopics([]);
          return;
        }

        // 如果有相關專題，再查詢對應的專題標題
        if (!relatedData || relatedData.length === 0) {
          setRelatedTopics([]);
          return;
        }

        // 獲取所有目標專題的 topic_id
        const targetTopicIds = relatedData.map(item => item.dst_topic_id);
        
        // 查詢目標專題的詳細資料
        const { data: topicData, error: topicError } = await supabaseClient
          .from('topic')
          .select('topic_id, topic_title')
          .in('topic_id', targetTopicIds);

        if (topicError) {
          console.error('Error fetching related topic titles:', topicError);
          setRelatedTopics([]);
          return;
        }

        // 合併資料並進行資料清理
        const related = relatedData.map(relatedItem => {
          const topicItem = topicData?.find(t => t.topic_id === relatedItem.dst_topic_id);
          
          // 資料清理：如果 reason 過長，可能是錯誤的內容，截短它
          let reason = relatedItem.reason || '無相關性說明';
          if (reason.length > 200) {
            reason = reason.substring(0, 200) + '...';
          }
          
          // 確保有有效的標題
          let title = topicItem?.topic_title || `專題 ID: ${relatedItem.dst_topic_id}`;
          if (!title.trim()) {
            title = `專題 ID: ${relatedItem.dst_topic_id}`;
          }
          
          return {
            id: relatedItem.dst_topic_id,
            title: title.trim(),
            relevance: reason.trim()
          };
        });
        setRelatedTopics(related);
      } catch (error) {
        console.error('Error fetching related topics:', error);
        setRelatedTopics([]);
      }
    };

    fetchRelatedTopics();
  }, [id, supabaseClient]);

  // 名詞解釋 tooltip
  const handleTermClick = (term, e) => {
    const rect = e.target.getBoundingClientRect();
    setTooltipTerm(term);
    setTooltipPosition({ x: rect.left + rect.width / 2, y: rect.top - 10 });
  };

  // 處理文字選取
  const handleTextSelection = () => {
    // 延遲執行，確保selection已經完成
    setTimeout(() => {
      const selection = window.getSelection();
      const selectedText = selection.toString().trim();
      
      if (selectedText.length > 0 && selection.rangeCount > 0) {
        const range = selection.getRangeAt(0);
        const rect = range.getBoundingClientRect();
        
        // 確保選取的是文章內容區域的文字
        const container = range.commonAncestorContainer;
        const articleElement = container.nodeType === Node.TEXT_NODE 
          ? container.parentElement 
          : container;
        
        if (articleElement.closest('.articleText')) {
          setSelectedText(selectedText);
          // 修復位置計算 - 使用相對於viewport的座標
          const buttonY = Math.max(rect.top - 60, 10); // 不要加window.scrollY，因為position:fixed已經相對於viewport
          const buttonX = Math.min(Math.max(rect.left + rect.width / 2, 60), window.innerWidth - 60); // 確保不超出螢幕邊界
          
          setSelectionPosition({
            x: buttonX,
            y: buttonY
          });
          setShowFactCheckButton(true);
        }
      } else {
        setShowFactCheckButton(false);
        setSelectedText('');
      }
    }, 100); // 增加延遲時間
  };

  // 處理溯源驗證API調用
  const handleFactCheck = async () => {
    if (!selectedText || !newsData?.story_id) return;
    
    try {
      const response = await fetchJson('/fact_check', {
        statement: selectedText,
        story_id: newsData.story_id
      });
      
      console.log('Fact check result:', response);
      
      // 創建溯源驗證訊息
      const factCheckMessage = {
        id: Date.now(),
        text: response.result,
        isOwn: false,
        time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' }),
      };

      // 通知ChatRoom組件添加溯源驗證結果
      if (chatRoomRef.current) {
        chatRoomRef.current.addFactCheckMessage(factCheckMessage);
      }
      
      // 隱藏按鈕
      setShowFactCheckButton(false);
      setSelectedText('');
    } catch (error) {
      console.error('Error during fact check:', error);
      
      // 創建錯誤訊息
      const errorMessage = {
        id: Date.now(),
        text: '❌ 溯源驗證失敗\n\n無法取得查核結果，請稍後再試。',
        isOwn: false,
        time: new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' }),
      };

      // 通知ChatRoom組件添加錯誤訊息
      if (chatRoomRef.current) {
        chatRoomRef.current.addFactCheckMessage(errorMessage);
      }
      
      // 隱藏按鈕
      setShowFactCheckButton(false);
      setSelectedText('');
    }
  };

  // 點擊其他地方時隱藏按鈕
  const handleDocumentClick = (e) => {
    // 如果點擊的是溯源按鈕本身，不要隱藏
    if (e.target.closest('.fact-check-button')) {
      return;
    }
    
    // 如果點擊的是文章內容區域，允許重新選取
    if (e.target.closest('.articleText')) {
      return;
    }
    
    // 其他情況隱藏按鈕
    setShowFactCheckButton(false);
    setSelectedText('');
    
    // 清除選取
    window.getSelection().removeAllRanges();
  };

  // 添加事件監聽器
  useEffect(() => {
    const handleSelectionChange = () => {
      handleTextSelection();
    };

    const handleMouseUp = () => {
      handleTextSelection();
    };

    const handleDocumentClickEvent = (e) => {
      handleDocumentClick(e);
    };

    // 監聽選取變化和滑鼠釋放
    document.addEventListener('selectionchange', handleSelectionChange);
    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('click', handleDocumentClickEvent);
    
    return () => {
      document.removeEventListener('selectionchange', handleSelectionChange);
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('click', handleDocumentClickEvent);
    };
  }, []);

  const renderArticleText = (text) => {
    if (!text) return null;

    // 以「空一行」分段；段內的單一換行會轉成 <br/>
    const paragraphs = String(text).split(/\r?\n\s*\r?\n/);

    const terms = sortedTerms; // 直接用 useMemo 的排序結果
    const escapeReg = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const termsPattern = terms.length
      ? new RegExp(`(${terms.map(escapeReg).join('|')})`, 'g')
      : null;
    const seenTerms = new Set(); // 記錄已經高亮過的 terms

    const highlightTermsInLine = (line) => {
      if (!termsPattern) return line;

      return line.split(termsPattern).map((part, i) => {
        if (terms.includes(part)) {
          // 只有第一次出現的 term 才高亮
          if (!seenTerms.has(part)) {
            seenTerms.add(part);
            return (
              <strong
                key={`term-${i}`}
                className="term term--clickable"
                onClick={(e) => handleTermClick(part, e)}
              >
                {part}
              </strong>
            );
          } else {
            // 已經出現過的 term 不高亮
            return <React.Fragment key={`txt-${i}`}>{part}</React.Fragment>;
          }
        }
        return <React.Fragment key={`txt-${i}`}>{part}</React.Fragment>;
      });
    };

    // 渲染：每段用 <p> 包起來，段內單行換行 → <br/>
    return paragraphs.map((para, pi) => {
      const lines = para.split(/\r?\n/);
      return (
        <p key={`p-${pi}`}>
          {lines.map((line, li) => (
            <React.Fragment key={`l-${pi}-${li}`}>
              {highlightTermsInLine(line)}
              {li < lines.length - 1 && <br />}
            </React.Fragment>
          ))}
        </p>
      );
    });
  };

  const { sortedTerms, termDefinitionsFromDB } = useMemo(() => {
    // 使用從資料庫載入的術語，如果沒有則使用 newsData.terms 作為後備
    const raw = newsTerms.length > 0 ? newsTerms : (Array.isArray(newsData?.terms) ? newsData.terms : []);
    
    // 如果 newsTerms 是物件陣列（包含 definition 和 example）
    if (newsTerms.length > 0 && typeof newsTerms[0] === 'object') {
      const termStrings = newsTerms.map(item => item.term);
      const definitions = {};
      newsTerms.forEach(item => {
        definitions[item.term] = {
          definition: item.definition,
          example: item.example
        };
      });
      
      return {
        sortedTerms: Array.from(new Set(termStrings)).sort((a, b) => b.length - a.length),
        termDefinitionsFromDB: definitions
      };
    }
    
    // 如果是字串陣列（舊格式或 newsData.terms）
    const termStrings = Array.isArray(raw) ? raw : [];
    return {
      sortedTerms: Array.from(new Set(termStrings)).sort((a, b) => b.length - a.length),
      termDefinitionsFromDB: {}
    };
  }, [newsData, newsTerms]);


  if (!newsData) {
    return (
      <div className="newsDetail">
        <Link to="/" className="backButton">← 返回首頁</Link>
        <p>找不到該新聞</p>
      </div>
    );
  }

  

  return (
    <div className="newsDetail">
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

      {/* 溯源驗證按鈕 */}
      {showFactCheckButton && (
        <div 
          className="fact-check-button"
          style={{
            left: selectionPosition.x,
            top: selectionPosition.y,
          }}
          onClick={handleFactCheck}
          onMouseEnter={(e) => {
            e.target.style.background = '#f8f9fa';
            e.target.style.transform = 'translateX(-50%) translateY(-2px)';
            e.target.style.boxShadow = '0 6px 20px rgba(0, 0, 0, 0.2)';
          }}
          onMouseLeave={(e) => {
            e.target.style.background = '#ffffff';
            e.target.style.transform = 'translateX(-50%)';
            e.target.style.boxShadow = '0 4px 16px rgba(0, 0, 0, 0.15), 0 2px 4px rgba(0, 0, 0, 0.1)';
          }}
        >
          🔍 溯源驗證
        </div>
      )}

      <div className={`article-container articleContainer ${isChatOpen ? 'chat-open' : ''}`}>
        {/* 主要內容區域 - 左右佈局 */}
        <div className="content-layout">
          {/* 左側：新聞主要內容 */}
          <div className="main-content">
            <div className="articleContent">
              <h2 className="articleTitle">{newsData.title}</h2>
              <div className="articleInfo">
                <span className="articleDate">{newsData.date}</span>
                <span className="articleAuthor">作者 {newsData.author}</span>
                {newsKeywords && newsKeywords.length > 0 && (
                  <div className="articleKeywords">
                    {newsKeywords.map((kw, index) => (
                      <span className="keywordChip" key={index}>{kw.keyword}</span>
                    ))}
                  </div>
                )}
              </div>

              {newsImage?.map((img, i) => (
                <div className="articleImage" key={i}>
                  <img src={img.src} alt={img.description} />
                  {img.description && (
                    <div className="imageCaption">{img.description}</div>
                  )}
                </div>
              ))}
              <div className="articleText" style={{ userSelect: 'text' }}>
                {renderArticleText(newsData.long)}
              </div>
            </div>
          </div>

          {/* 右側：正反方立場 或 專家分析 */}
          <div className="sidebar-content">
            {showContent === 'loading' || positionLoading || (showContent === 'loadExpert' && analysisLoading) ? (
              <div className="prosConsSection">
                <h4 className="prosConsTitle">載入中...</h4>
                <div className="loadingMessage">正在載入資料...</div>
              </div>
            ) : showContent === 'position' ? (
              <div className="prosConsSection">
                <h4 className="prosConsTitle">正反方立場</h4>
                <div className="prosConsGrid">
                  {/* 正方立場 */}
                  <div className="prosColumn">
                    <div className="prosHeader">
                      <h5 className="prosTitle">正方</h5>
                    </div>
                    <div className="prosContent">
                      {positionData.positive && positionData.positive.length > 0 ? (
                        positionData.positive.map((point, index) => (
                          <div className="prosPoint" key={index}>
                            • {point}
                          </div>
                        ))
                      ) : (
                        <div className="prosPoint">
                          • 暫無正方觀點資料
                        </div>
                      )}
                    </div>
                  </div>

                  {/* 反方立場 */}
                  <div className="consColumn">
                    <div className="consHeader">
                      <h5 className="consTitle">反方</h5>
                    </div>
                    <div className="consContent">
                      {positionData.negative && positionData.negative.length > 0 ? (
                        positionData.negative.map((point, index) => (
                          <div className="consPoint" key={index}>
                            • {point}
                          </div>
                        ))
                      ) : (
                        <div className="consPoint">
                          • 暫無反方觀點資料
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ) : showContent === 'expert' ? (
              <div className="expertAnalysisSection">
                <h4 className="expertAnalysisTitle">專家分析</h4>
                <div className="expertAnalysisContent">
                  {expertAnalysis && expertAnalysis.length > 0 ? (
                    expertAnalysis.map((analysis, index) => {
                      // 根據 category 找到對應的專家名稱
                      const expert = experts.find(exp => exp.category === analysis.category);
                      const expertName = expert ? expert.name : analysis.category;
                      
                      return (
                        <div className="analysisItem" key={analysis.analyze_id || index}>
                          {expertName && (
                            <div className="analysisCategory">
                              <span className="categoryTag">{expertName}</span>
                            </div>
                          )}
                          <div className="analysisText">
                            {analysis.analyze}
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div className="noAnalysisMessage">
                      暫無專家分析資料
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="prosConsSection">
                <h4 className="prosConsTitle">暫無分析資料</h4>
                <div className="noAnalysisMessage">
                  目前沒有正反方立場或專家分析資料
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 相關內容區塊 - 移動到資料來源上面 */}
      {((relatedNews && relatedNews.length > 0) || (relatedTopics && relatedTopics.length > 0)) && (
        <div className="relatedSection relatedSection--main">
          <div className="container">
            <div className="relatedGrid relatedGrid--horizontal">
              {/* 相關新聞 */}
              {relatedNews && relatedNews.length > 0 && (
                <div className="relatedColumn">
                  <h5 className="sectionTitle">相關新聞</h5>
                  <div className="relatedItems">
                    {relatedNews.map(item => (
                      <div className="relatedItem" key={`news-${item.id}`}>
                        <Link to={`/news/${item.id}`}>
                          {item.title}
                        </Link>
                        <div className="relevanceText">{item.relevance}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* 相關專題 */}
              {relatedTopics && relatedTopics.length > 0 && (
                <div className="relatedColumn">
                  <h5 className="sectionTitle">相關專題</h5>
                  <div className="relatedItems">
                    {relatedTopics.map(item => (
                      <div className="relatedItem" key={`topic-${item.id}`}>
                        <Link to={`/special-report/${item.id}`}>
                          {item.title}
                        </Link>
                        <div className="relevanceText">{item.relevance}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 資料來源區塊 - 放在頁面底部 */}
      {(newsUrl || newsData.source) && (() => {
        const MAX = 3;
        
        // 處理從 Supabase 來的資料 (包含媒體、標題、URL)
        let sources = [];
        if (newsUrl && Array.isArray(newsUrl)) {
          sources = newsUrl.filter(item => item.article_url && item.article_title).map(item => ({
            url: item.article_url,
            title: item.article_title,
            media: item.media || '未知媒體'
          }));
        }
        
        // 如果沒有 Supabase 資料，使用原本的 source 資料
        if (sources.length === 0 && newsData.source) {
          const all = Array.isArray(newsData.source)
            ? newsData.source.filter(Boolean)
            : (newsData.source ? [newsData.source] : []);
          sources = all.map(url => ({
            url: url,
            title: url,
            media: '未知媒體'
          }));
        }

        // 去重，避免重複網址
        const uniq = sources.filter((source, index, self) => 
          index === self.findIndex(s => s.url === source.url)
        );
        const total = uniq.length;
        const visible = showAllSources ? uniq : uniq.slice(0, MAX);
        const hasMore = total > MAX;

        return (
          <div className="sourceBlock">
            <div className="sourceTitle">資料來源：</div>

            {visible.length > 0 ? (
              <ul className="sourceList">
                {visible.map((source, i) => (
                  <li key={i}>
                    <span className="sourceMedia">{source.media}</span>
                    <span className="sourceSeparator">：</span>
                    <a href={source.url} target="_blank" rel="noopener noreferrer" className="sourceLink">
                      {source.title}
                    </a>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="sourceEmpty">（無資料來源）</div>
            )}

            {hasMore && (
              <button
                className="sourceToggleButton"
                onClick={() => setShowAllSources(s => !s)}
              >
                {showAllSources ? '收起' : `觀看更多（還有 ${total - MAX} 筆）`}
              </button>
            )}
          </div>
        );
      })()}

      {/* 側邊聊天室 */}
      <div className={`chat-sidebar ${isChatOpen ? 'open' : ''}`}>
        <div className="chat-sidebar-content" style={{ flex: 1, overflow: 'hidden' }}>
          <ChatRoom ref={chatRoomRef} newsData={newsData} onClose={() => setIsChatOpen(false)} />
        </div>
      </div>

      {/* Tooltip */}
      {tooltipTerm && (
        <TermTooltip
          term={tooltipTerm}
          definition={
            termDefinitionsFromDB[tooltipTerm]?.definition || 
            termDefinitions[tooltipTerm]?.definition || 
            `未找到「${tooltipTerm}」的定義`
          }
          example={
            termDefinitionsFromDB[tooltipTerm]?.example || 
            termDefinitions[tooltipTerm]?.example
          }
          position={tooltipPosition}
          onClose={() => setTooltipTerm(null)}
        />
      )}
    </div>
  );
}

export default NewsDetail;