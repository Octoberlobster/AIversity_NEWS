import React, { useState, useEffect, useMemo} from 'react';
import { useParams, Link} from 'react-router-dom';
import './../css/NewsDetail.css';
import ChatRoom from './ChatRoom';
import TermTooltip from './TermTooltip';
import { useSupabase } from './supabase';

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

    return definitions
  } catch (error) {
    console.error('載入術語定義時發生錯誤:', error);
  }
};

function NewsDetail() {
  const { id } = useParams();
  const [showLongContent, setShowLongContent] = useState(false);
  const [articleWidth, setArticleWidth] = useState('2');
  const [isResizing, setIsResizing] = useState(false);
  const [tooltipTerm, setTooltipTerm] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const [dragStartX, setDragStartX] = useState(0);
  const [dragStartWidth, setDragStartWidth] = useState(0);
  const [showAllSources, setShowAllSources] = useState(false);
  const [newsData, setNewsData] = useState(null);
  const [newsImage, setNewsImage] = useState(null);
  const [newsUrl, setNewsUrl] = useState(null);
  const [newsKeywords, setNewsKeywords] = useState([]);
  const [termDefinitions, setTermDefinitions] = useState({});
  const [newsTerms, setNewsTerms] = useState([]);
  const [relatedNews, setRelatedNews] = useState([]);

  // 確保頁面載入時滾動到頂部
  useEffect(() => {
    window.scrollTo(0, 0);
    setShowAllSources(false);
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
        const { data, error } = await supabaseClient
          .from('term_map')
          .select('term')
          .eq('story_id', id);
        
        if (error) {
          console.error(`Error fetching terms for story ${id}:`, error);
          setNewsTerms([]);
          return;
        }
        const terms = data?.map(item => item.term) || [];
        setNewsTerms(terms);
      } catch (error) {
        console.error(`Error fetching terms for story ${id}:`, error);
        setNewsTerms([]);
      }
    };

    fetchNewsTerms();
  }, [id, supabaseClient]);

  useEffect(() => {
    const fetchNewsData = async () => {
      const { data, error } = await supabaseClient
        .from('single_news')
        .select('*')
        .eq('story_id', id);
      if (error) {
        console.error('Error fetching news data:', error);
      } else {
        console.log("Fetched news data:", data);
        const row = data?.[0];
        setNewsData(row ? {
          title: row.news_title,
          date: row.generated_date,
          author: 'Gemini',
          short: row.short,
          long: row.long,
          terms: [],
          keywords: [],
          source: []
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
        const mime =
          item.mime_type || item.image_mime || 'image/jpeg'; // 若表有存 mime，就用它
        const b64 = (item.image || '').replace(/\s/g, '');   // 清掉換行/空白
        const src = b64.startsWith('data:')
          ? b64
          : `data:${mime};base64,${b64}`;
        console.log(src);
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
        .eq('story_id', id);

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

  useEffect(() => {
    if (!isResizing) return;
    const handleMouseMove = (e) => {
      const container = document.querySelector('.article-container');
      if (!container) return;
      const containerRect = container.getBoundingClientRect();
      const currentMouseX = e.clientX - containerRect.left;
      const deltaX = currentMouseX - dragStartX;
      const widthChange = deltaX / 100;            // 100px -> flex 改變 1
      const newWidth = Math.max(1, Math.min(4, dragStartWidth + widthChange));
      setArticleWidth(newWidth.toFixed(1));
    };
    const handleMouseUp = () => {
      setIsResizing(false);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, dragStartX, dragStartWidth]);

  const handleMouseDown = (e) => {
    e.preventDefault();
    const container = document.querySelector('.article-container');
    if (container) {
      const rect = container.getBoundingClientRect();
      setDragStartX(e.clientX - rect.left);
      setDragStartWidth(parseFloat(articleWidth));
    }
    setIsResizing(true);
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  };

  // 名詞解釋 tooltip
  const handleTermClick = (term, e) => {
    const rect = e.target.getBoundingClientRect();
    setTooltipTerm(term);
    setTooltipPosition({ x: rect.left + rect.width / 2, y: rect.top - 10 });
  };

  const renderArticleText = (text, allowedFirstSet) => {
    if (!text) return null;

    // 以「空一行」分段；段內的單一換行會轉成 <br/>
    const paragraphs = String(text).split(/\r?\n\s*\r?\n/);

    const terms = sortedTerms; // 直接用 useMemo 的排序結果
    const escapeReg = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const termsPattern = terms.length
      ? new RegExp(`(${terms.map(escapeReg).join('|')})`, 'g')
      : null;
    const seenInThisBlock = new Map(); // term -> count

    const highlightTermsInLine = (line) => {
      if (!termsPattern) return line;

      return line.split(termsPattern).map((part, i) => {
        if (terms.includes(part)) {
          const count = seenInThisBlock.get(part) || 0;
          const canHighlight = allowedFirstSet?.has(part) && count === 0;
          if (canHighlight) {
            seenInThisBlock.set(part, 1);
            return (
              <strong
                key={`term-${i}`}
                className="term term--clickable"
                onClick={(e) => handleTermClick(part, e)}
              >
                {part}
              </strong>
            );
          }
          // 之後出現：純文字，不高亮、不可點
          return <React.Fragment key={`txt-${i}`}>{part}</React.Fragment>;
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

  const { sortedTerms, firstInShort, firstInLong } = useMemo(() => {
    // 使用從資料庫載入的術語，如果沒有則使用 newsData.terms 作為後備
    const raw = newsTerms.length > 0 ? newsTerms : (Array.isArray(newsData?.terms) ? newsData.terms : []);
    // 去重 + 長詞優先，避免短詞吃掉長詞
    const termsArr = Array.from(new Set(raw)).sort((a, b) => b.length - a.length);

    const shortStr = String(newsData?.short || '');
    const longStr  = String(newsData?.long  || '');

    const escapeReg = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const buildRe = (list) =>
      list.length ? new RegExp(`(${list.map(escapeReg).join('|')})`, 'g') : null;

    // 掃描某段文字，回傳「實際有出現過的 term」集合
    const collectPresent = (text, list) => {
      const set = new Set();
      const re = buildRe(list);
      if (!re) return set;
      re.lastIndex = 0;
      let m;
      while ((m = re.exec(text)) !== null) {
        // m[0] 就是匹配到的 term（因為 alternation 是整詞們）
        set.add(m[0]);
      }
      return set;
    };

    const inShort = collectPresent(shortStr, termsArr); // 只要在 short 出現過，就允許 short 高亮一次
    const inLong  = collectPresent(longStr,  termsArr); // 只要在 long 出現過，就允許 long 高亮一次

    return { sortedTerms: termsArr, firstInShort: inShort, firstInLong: inLong };
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
      <div className="article-container articleContainer">
        <div className={`articleContent ${isResizing ? 'is-resizing' : ''}`}>
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

          <div className="articleText">
            {renderArticleText(newsData.short, firstInShort)}
          </div>

          {!showLongContent && (
            <button className="readMoreButton" onClick={() => setShowLongContent(true)}>
              閱讀更多 →
            </button>
          )}

          {showLongContent && (
            <>
              <div className="longContent">
                <div className="articleText">
                  {renderArticleText(newsData.long, firstInLong)}
                </div>
              </div>
              <button className="readMoreButton" onClick={() => setShowLongContent(false)}>
                閱讀較少 ←
              </button>
            </>
          )}
        </div>

        <div className="resizeCol">
          <div
            className="resizeHandle"
            onMouseDown={handleMouseDown}
            style={{
              '--bar': isResizing ? '#667eea' : '#e5e7eb',
              '--dots-color': isResizing ? 'white' : '#6b7280',
              '--dots-opacity': isResizing ? 1 : 0.4,
              '--dots-bg': isResizing ? '#667eea' : '#f3f4f6',
            }}
          />
          <div className="resizeHint" onMouseDown={handleMouseDown}>
            拖動調整
          </div>
        </div>

        <ChatRoom news={newsData.long} />
      </div>

      {/* 延伸閱讀 */}
      {relatedNews && relatedNews.length > 0 && (
        <div className="relatedSection">
          <h4 className="sectionTitle">相關報導</h4>
          <div className="relatedGrid">
            {relatedNews.map(item => (
              <div className="relatedItem" key={item.id}>
                <Link to={`/news/${item.id}`}>
                  {item.title}
                </Link>
                <br></br>
                <div className="relevanceText">{item.relevance}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tooltip */}
      {tooltipTerm && (
        <TermTooltip
          term={tooltipTerm}
          definition={termDefinitions[tooltipTerm]?.definition || `未找到「${tooltipTerm}」的定義`}
          example={termDefinitions[tooltipTerm]?.example}
          exampleFromDB={termDefinitions[tooltipTerm]?.example}
          position={tooltipPosition}
          onClose={() => setTooltipTerm(null)}
        />
      )}

      {/* 資料來源 */}
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
    </div>
  );
}

export default NewsDetail;