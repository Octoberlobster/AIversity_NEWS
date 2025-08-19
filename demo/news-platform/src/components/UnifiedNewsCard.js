import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import './../css/UnifiedNewsCard.css';
import TermTooltip from './TermTooltip';
import { useSupabase } from './supabase';

// 全域狀態管理，確保在 StrictMode 下也能正常工作
const globalExpandedState = new Map();

// 為每個組件實例生成唯一 ID
let instanceCounter = 0;
const generateInstanceId = () => {
  instanceCounter++;
  return `instance_${instanceCounter}_${Math.random().toString(36).substr(2, 9)}`;
};

// 從資料庫動態載入術語定義的函數
const loadTermDefinitions = async (supabase) => {
  try {
    const { data, error } = await supabase
      .from('term')
      .select('term, definition, example');
    
    if (error) {
      console.error('載入術語定義時發生錯誤:', error);
    }

    // 轉換為物件格式
    const definitions = {};
    data.forEach(item => {
      if (item.term && item.definition) {
        definitions[item.term] = {
          definition: item.definition,
          example: item.example || null
        };
      }
    });
    return definitions;
  } catch (error) {
    console.error('載入術語定義時發生錯誤:', error);
  }
};

// 建立英文分類到中文分類的映射
const categoryMapping = {
  'Politics': '政治',
  'Taiwan News': '台灣',
  'International News': '國際',
  'Science & Technology': '科學與科技',
  'Lifestyle & Consumer': '生活',
  'Sports': '體育',
  'Entertainment': '娛樂',
  'Business & Finance': '商業財經',
  'Health & Wellness': '健康'
};

// 組合預設資料和後端資料
export const defaultNewsData = [
  {
    story_id: 1,
    title: "人工智慧在醫療領域的突破性進展",
    category: "科學與科技",
    date: "2024-01-15 14:30",
    author: "張明華",
    sourceCount: 5,
    shortSummary: "最新研究顯示，人工智慧技術在疾病診斷和治療方案制定方面取得了重大突破。通過機器學習算法，AI系統能夠分析大量醫療數據，為精準醫療提供支持。",
    relatedNews: [
      { story_id: 101, title: "AI 診斷系統獲 FDA 批准" },
      { story_id: 102, title: "基因編輯技術與 AI 結合的新突破" },
      { story_id: 103, title: "遠程醫療中的 AI 應用" }
    ],
    views: "2.3k",
    keywords: ["AI", "醫療", "診斷"],
    terms: ["人工智慧", "機器學習", "精準醫療"]
  },
];

function UnifiedNewsCard({ limit, keyword, customData, onNewsCountUpdate, instanceId: propInstanceId }) {
  const [newsData, setNewsData] = useState([]);
  const [refreshKey, setRefreshKey] = useState(0); // 用於強制重新渲染
  const [tooltipTerm, setTooltipTerm] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const [termDefinitions, setTermDefinitions] = useState({});
  const supabaseClient = useSupabase(); 

  // 優先使用傳入的 instanceId，否則生成一個
  const [instanceId] = useState(() => propInstanceId || generateInstanceId());

  // 確保實例在全域 Map 中有自己的狀態
  if (!globalExpandedState.has(instanceId)) {
    globalExpandedState.set(instanceId, new Map());
  }

  // 載入術語定義
  useEffect(() => {
    const loadTerms = async () => {
      const definitions = await loadTermDefinitions(supabaseClient);
      setTermDefinitions(definitions);
    };
    loadTerms();
  }, [supabaseClient]);

  useEffect(() => {

      // 獲取單一新聞的 keywords
      const fetchNewsKeywords = async (storyId) => {
        try {
          const { data, error } = await supabaseClient
            .from('keywords_map')
            .select('keyword')
            .eq('story_id', storyId);
          
          if (error) {
            console.error(`Error fetching keywords for story ${storyId}:`, error);
            return [];
          }
          return data?.map(item => item.keyword) || [];
        } catch (error) {
          console.error(`Error fetching keywords for story ${storyId}:`, error);
          return [];
        }
      };

      // 獲取單一新聞的術語（terms）
      const fetchNewsTerms = async (storyId) => {
        try {
          const { data, error } = await supabaseClient
            .from('term_map')
            .select('term')
            .eq('story_id', storyId);
          
          if (error) {
            console.error(`Error fetching terms for story ${storyId}:`, error);
            return [];
          }
          return data?.map(item => item.term) || [];
        } catch (error) {
          console.error(`Error fetching terms for story ${storyId}:`, error);
          return [];
        }
      };

      // 獲取單一新聞的相關新聞
      const fetchRelatedNews = async (storyId) => {
        try {
          // 先查詢相關新聞關係
          const { data: relatedData, error: relatedError } = await supabaseClient
            .from('relative_news')
            .select('dst_story_id, reason')
            .eq('src_story_id', storyId);
          
          if (relatedError) {
            console.error(`Error fetching related news for story ${storyId}:`, relatedError);
            return [];
          }

          if (!relatedData || relatedData.length === 0) {
            return [];
          }

          // 獲取目標新聞的標題
          const targetStoryIds = relatedData.map(item => item.dst_story_id);
          const { data: newsData, error: newsError } = await supabaseClient
            .from('single_news')
            .select('story_id, news_title')
            .in('story_id', targetStoryIds);

          if (newsError) {
            console.error(`Error fetching related news titles for story ${storyId}:`, newsError);
            return [];
          }

          // 合併資料
          return relatedData.map(relatedItem => {
            const newsItem = newsData?.find(n => n.story_id === relatedItem.dst_story_id);
            return {
              id: relatedItem.dst_story_id,
              title: newsItem?.news_title || `新聞 ID: ${relatedItem.dst_story_id}`
            };
          });
        } catch (error) {
          console.error(`Error fetching related news for story ${storyId}:`, error);
          return [];
        }
      };

      // 如果有傳入 customData，就使用 customData，不需要從資料庫抓取
      if (customData && customData.length > 0) {
        const fetchCustomDataWithKeywords = async () => {
          const newsWithKeywords = await Promise.all(
                customData.map(async (news) => {
                  const keywords = await fetchNewsKeywords(news.story_id);
                  const terms = await fetchNewsTerms(news.story_id);
                  const relatedNews = await fetchRelatedNews(news.story_id);
                  return {
                    ...news,
                    keywords: keywords,
                    terms: terms,
                    relatedNews: relatedNews
                  };
                })
              );
          setNewsData(newsWithKeywords);
        };
        
        fetchCustomDataWithKeywords();
        return;
      }

      const fetchEventDataWithKeywords = async () => {
        try {
          const { data, error } = await supabaseClient
            .from('single_news')
            .select('*')       

          if (error) throw error;

          if (data && data.length > 0) {
            
            // 先轉換基本資料
            const basicNewsData = data.map(news => ({
              story_id: news.story_id, 
              title: news.news_title, 
              category: categoryMapping[news.category] || news.category,
              date: news.generated_date,
              author: 'Gemini',
              sourceCount: news.total_articles,
              shortSummary: news.ultra_short,
              relatedNews: [],
              views: 0,
              keywords: [], // 先設為空，稍後補齊
              terms: [],
            }));

            // 為每個新聞獲取 keywords、terms 和 relatedNews
            const newsWithKeywords = await Promise.all(
              basicNewsData.map(async (news) => {
                const keywords = await fetchNewsKeywords(news.story_id);
                const terms = await fetchNewsTerms(news.story_id);
                const relatedNews = await fetchRelatedNews(news.story_id);
                return {
                  ...news,
                  keywords: keywords,
                  terms: terms,
                  relatedNews: relatedNews
                };
              })
            );

            setNewsData(newsWithKeywords);
            
            // 通知父組件新聞總數量
            if (onNewsCountUpdate) {
              onNewsCountUpdate(newsWithKeywords.length);
            }
          } else {
            if (onNewsCountUpdate) {
              onNewsCountUpdate(0);
            }
          }
        } 
        catch (error) {
          console.error('Error fetching Single_News:', error);
        } 
      };
      
      fetchEventDataWithKeywords();
    }, [supabaseClient, customData, onNewsCountUpdate, termDefinitions]);

  

  let filteredNews = newsData;
  if (keyword) {
    filteredNews = filteredNews.filter((news) =>
      (news.keywords && news.keywords.some((kw) => kw === keyword)) ||
      (news.title && news.title.includes(keyword)) ||
      (news.shortSummary && news.shortSummary.includes(keyword))
    );
  }
  const displayNews = limit ? filteredNews.slice(0, limit) : filteredNews;

  // 切換展開狀態
  const toggleExpanded = (cardId) => {
    const instanceState = globalExpandedState.get(instanceId);
    if (!instanceState) return;
    
    const currentState = instanceState.get(cardId) || false;
    instanceState.set(cardId, !currentState);
    
    // 強制組件重新渲染
    setRefreshKey(prev => prev + 1);
  };

  const handleTermClick = (term, event) => {
    event.preventDefault();
    const rect = event.target.getBoundingClientRect();
    setTooltipPosition({ x: rect.left + rect.width / 2, y: rect.top - 10 });
    setTooltipTerm(term);
  };
  const closeTooltip = () => setTooltipTerm(null);

  const renderHighlightedText = (text, newsTerms) => {
    if (!text) return '';
    if (!newsTerms || !Array.isArray(newsTerms) || newsTerms.length === 0) return text;

    // 去重、過濾空字串，並用「長詞優先」避免 AI 先吃掉 生成式AI
    const terms = Array.from(new Set(newsTerms.filter(Boolean))).sort((a, b) => b.length - a.length);
    if (terms.length === 0) return text;

    const escapeReg = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');  //正則式轉義特殊字符
    const pattern = new RegExp(`(${terms.map(escapeReg).join('|')})`, 'g'); // 匹配所有關鍵詞

    // 用 Set 記錄「此文字塊內」哪些 term 已經出現過
    const seenOnce = new Set();
    const termsSet = new Set(terms);

    // 用 split + 捕獲群組的方式保留 term 本身
    const parts = String(text).split(pattern);

    return parts.map((part, index) => {
      if (termsSet.has(part)) {
        if (!seenOnce.has(part)) {
          // 第一次出現：高亮＋可點
          seenOnce.add(part);
          return (
            <strong
              key={`term-${index}`}
              className="term term--clickable"
              onClick={(e) => handleTermClick(part, e)}
            >
              {part}
            </strong>
          );
        }
        // 之後出現：純文字（不高亮、不可點）
        return <React.Fragment key={`txt-${index}`}>{part}</React.Fragment>;
      }
      return <React.Fragment key={`txt-${index}`}>{part}</React.Fragment>;
    });
  };

  return (
    <div className="unifiedNewsCard" key={refreshKey} style={{ position: 'relative' }}>
      
      <div className="newsGrid">
        {displayNews.map((news, index) => {
          const uniqueKey = `${instanceId}_${news.story_id}`;
          const instanceState = globalExpandedState.get(instanceId);
          const isExpanded = instanceState ? instanceState.get(news.story_id) || false : false;
          
          return (
            <div 
              className={`card ${isExpanded ? 'expanded' : ''}`} 
              key={uniqueKey}
              style={{
                minHeight: isExpanded ? 'auto' : '225px',
                height: isExpanded ? 'auto' : '225px'
              }}
            >
              <div className="card__header">
                <Link className="card__title" to={`/news/${news.story_id}`}>
                  {news.title}
                </Link>
              </div>

              <div className="card__info">
                <span className="dateText">{news.date}</span>
                <span className="authorText">記者 {news.author}</span>
              </div>

              <div className="card__meta">
                <span className="tag--category">{news.category}</span>
                <span className="sourceCount">{news.sourceCount} 個來源</span>
                {news.keywords?.map((kw) => (
                  <span className="keywordChip" key={kw}>{kw}</span>
                ))}
              </div>

              <div className="card__content">
                <p className={`summaryText ${isExpanded ? 'is-expanded' : ''}`}>
                  {isExpanded
                    ? renderHighlightedText(news.shortSummary, news.terms)
                    : renderHighlightedText(news.shortSummary.substring(0, 150), news.terms)}
                </p>

                {isExpanded && (
                  <div className="expandedContent">
                    <div className="relatedNews">
                      <h4 className="relatedNews__title">相關報導</h4>
                      <ul className="relatedNews__list">
                        {news.relatedNews && news.relatedNews.length > 0 ? (
                          news.relatedNews.map((r) => (
                            <li className="relatedNews__item" key={r.id}>
                              <Link className="relatedNews__link" to={`/news/${r.id}`}>
                                {r.title}
                              </Link>
                            </li>
                          ))
                        ) : (
                          <li className="relatedNews__item">暫無相關報導</li>
                        )}
                      </ul>
                    </div>
                  </div>
                )}
              </div>

              <div className="card__actions">
                <div className="actionButtons">
                  <button className="actionButton" onClick={() => toggleExpanded(news.story_id)}>
                    {isExpanded ? '收起' : '展開'}
                  </button>
                </div>
                <div className="stats">
                  <span className="stat">👁️ {news.views}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {tooltipTerm && termDefinitions[tooltipTerm] && (
        <TermTooltip
          term={tooltipTerm}
          definition={termDefinitions[tooltipTerm].definition}
          example={termDefinitions[tooltipTerm].example}
          position={tooltipPosition}
          onClose={closeTooltip}
        />
      )}
    </div>
  );
}

export default UnifiedNewsCard;