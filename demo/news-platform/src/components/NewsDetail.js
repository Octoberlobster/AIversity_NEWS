import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import './../css/NewDetail.css';
import ChatRoom from './ChatRoom';
import TermTooltip from './TermTooltip';

// --- 導入後端新聞資料 ---
import rawBackendData from './../final_comprehensive_reports_20250812_013357.json';

// 將後端資料轉換為前端詳細頁面格式
const convertBackendToDetailFormat = (backendData) => {
  const result = {};
  backendData.forEach((story, index) => {
    result[index + 2] = {
      title: story.comprehensive_report.title || "無標題",
      date: story.processed_at || new Date().toISOString(),
      author: "Gemini",
      image: "",
      imageCaption: "",
      short: story.comprehensive_report.versions.short || "",
      long: story.comprehensive_report.versions.long || "",
      keywords: [],
      terms: [],
      related: [],
      source: story.comprehensive_report.source_urls || []
    };
  });
  return result;
};

// --- mock data ---
const mockNewsData = {
  1: {
    title: "人工智慧在醫療領域的突破性進展",
    date: "2024-01-15 14:30",
    author: "張明華",
    image: "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=800&h=500&fit=crop",
    imageCaption: "AI 技術在醫療影像識別中的應用示意圖",
    short: `最新研究顯示，**人工智慧**技術在疾病診斷和治療方案制定方面取得了重大突破。研究團隊利用**機器學習**算法分析了數千個病例，成功提高了診斷準確率達95%以上。\n\n這項技術特別在**影像識別**方面表現出色，能夠快速識別X光片、CT掃描等醫學影像中的異常情況。專家表示，這將大大減輕醫護人員的工作負擔，並提高醫療效率。\n\n然而，這項技術的應用也面臨著**倫理考量**和**隱私保護**等挑戰。如何在提高醫療效率的同時保護患者隱私，成為業界關注的焦點。`,
    long: `最新研究顯示，**人工智慧**技術在疾病診斷和治療方案制定方面取得了重大突破。這項由國際頂尖醫療機構聯合進行的研究，歷時三年，投入資金超過數千萬美元，最終在**機器學習**和**深度學習**技術的結合下，成功開發出了新一代醫療AI系統。\n\n研究團隊利用**機器學習**算法分析了數千個病例，涵蓋了從常見疾病到罕見病症的各種情況。通過對大量數據的深度學習，AI系統能夠識別出人類醫生可能忽略的細微症狀，成功提高了診斷準確率達95%以上，遠超傳統診斷方法的準確率。\n\n這項技術特別在**影像識別**方面表現出色，能夠快速識別X光片、CT掃描、核磁共振等各種醫學影像中的異常情況。AI系統不僅能夠識別腫瘤、骨折等明顯病變，還能夠發現早期癌症的微小徵兆，為早期治療提供了寶貴的時間窗口。\n\n專家表示，這將大大減輕醫護人員的工作負擔，並提高醫療效率。在資源緊張的醫療環境中，AI助手可以幫助醫生快速篩選病例，讓醫生能夠將更多時間投入到需要專業判斷的複雜病例中。\n\n然而，這項技術的應用也面臨著**倫理考量**和**隱私保護**等挑戰。如何在提高醫療效率的同時保護患者隱私，成為業界關注的焦點。此外，AI診斷結果的責任歸屬問題也需要法律和倫理框架的完善。\n\n未來，這項技術有望在全球範圍內推廣應用，為更多患者提供更準確、更快速的醫療服務。同時，研究團隊也正在開發針對不同地區和人群的個性化AI模型，以確保技術的普適性和有效性。`,
    keywords: ["AI", "醫療", "影像識別"],
    terms: ["人工智慧", "機器學習", "影像識別", "倫理考量", "隱私保護", "深度學習"],
    related: [
      { id: 2, title: "AI助力癌症早期診斷", relevance: "本篇新聞介紹的 AI 技術在醫療領域的應用，與延伸閱讀中 AI 協助癌症早期診斷的主題密切相關，皆強調 AI 如何提升診斷準確率。" },
      { id: 3, title: "醫療影像新技術", relevance: "本篇強調 AI 在影像識別的突破，延伸閱讀則深入介紹醫療影像技術的最新發展，兩者皆聚焦於醫療影像的創新。" }
    ],
    source: "https://www.healthai-news.com/article/ai-medical-breakthrough"
  },
  ...convertBackendToDetailFormat(rawBackendData)
};

const termDefinitions = {
  "人工智慧": "人工智慧（Artificial Intelligence, AI）是指由機器展現的智能，與人類和其他動物的自然智能相對。",
  "機器學習": "機器學習是人工智慧的一個分支，使計算機能夠在沒有明確編程的情況下學習和改進。",
  "影像識別": "影像識別是指計算機視覺技術，能夠自動識別和分析圖像中的內容和特徵。",
  "倫理考量": "倫理考量是指在技術發展和應用過程中需要考慮的道德和價值觀問題。",
  "隱私保護": "隱私保護是指保護個人信息不被未經授權的訪問、使用或披露的措施。",
  "深度學習": "深度學習是機器學習的一個子集，使用多層神經網絡來模擬人腦的學習過程。",
  "技術標準化": "技術標準化是指建立統一的技術規範和標準，確保技術在不同環境下的一致性和互操作性。",
  "醫生培訓": "醫生培訓是指對醫療人員進行新技術、新方法的專業教育和技能提升。",
  "設備更新": "設備更新是指醫療機構引進新的醫療設備和技術，以提升診斷和治療能力。",
  "人員培訓": "人員培訓是指對醫療工作人員進行專業技能和知識的培訓，以適應新技術的應用。"
};

// --- NewsDetail 元件 ---
function NewsDetail() {
  const { id } = useParams();
  const [showLongContent, setShowLongContent] = useState(false);
  const [articleWidth, setArticleWidth] = useState('2');
  const [isResizing, setIsResizing] = useState(false);
  const [tooltipTerm, setTooltipTerm] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const [dragStartX, setDragStartX] = useState(0);
  const [dragStartWidth, setDragStartWidth] = useState(0);

  // 確保頁面載入時滾動到頂部
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [id]); // 當 id 改變時執行

  const newsData = mockNewsData[id];

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

  // 將 **term** 轉成 <strong>，並加上 class 控制樣式
  const renderArticleText = (text) => {
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        const term = part.slice(2, -2);
        const isClickable = newsData.terms && newsData.terms.includes(term);
        const classNames = `term ${isClickable ? 'term--clickable' : ''}`;
        return (
          <strong
            key={index}
            className={classNames}
            onClick={isClickable ? (e) => handleTermClick(term, e) : undefined}
          >
            {term}
          </strong>
        );
      }
      return part;
    });
  };

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
      {/* chips */}
      {newsData.keywords && (
        <div className="chipsRow">
          {newsData.keywords.map(kw => (
            <span className="keywordChip" key={kw}>{kw}</span>
          ))}
        </div>
      )}

      <div className="article-container articleContainer">
        <div
          className={`articleContent ${isResizing ? 'is-resizing' : ''}`}
          style={{ '--width': articleWidth }}  /* CSS 變數用 var() 讀取 */
        >
          <h2 className="articleTitle">{newsData.title}</h2>
          <div className="articleInfo">
            <span className="articleDate">{newsData.date}</span>
            <span className="articleAuthor">記者 {newsData.author}</span>
          </div>

          {newsData.image && (
            <div className="articleImage">
              <img src={newsData.image} alt={newsData.imageCaption} />
              {newsData.imageCaption && (
                <div className="imageCaption">{newsData.imageCaption}</div>
              )}
            </div>
          )}

          <div className="articleText">
            {renderArticleText(newsData.short)}
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
                  {renderArticleText(newsData.long)}
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

        <ChatRoom />
      </div>

      {/* 延伸閱讀 */}
      {newsData.related && newsData.related.length > 0 && (
        <div className="relatedSection">
          <h4 className="sectionTitle">相關報導</h4>
          <div className="relatedGrid">
            {newsData.related.map(item => (
              <div className="relatedItem" key={item.id}>
                <Link to={`/news/${item.id}`}>
                  {item.title}
                  <span className="relatedBadge">相關</span>
                </Link>
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
          definition={termDefinitions[tooltipTerm]}
          position={tooltipPosition}
          onClose={() => setTooltipTerm(null)}
        />
      )}

      {/* 資料來源 */}
      {newsData.source && (
        <div className="sourceBlock">
          <div className="sourceTitle">資料來源：</div>
          {Array.isArray(newsData.source) ? (
            <ul className="sourceList">
              {newsData.source.map((url, index) => (
                <li key={index}>
                  <a href={url} target="_blank" rel="noopener noreferrer">
                    {url}
                  </a>
                </li>
              ))}
            </ul>
          ) : (
            <a href={newsData.source} target="_blank" rel="noopener noreferrer">
              {newsData.source}
            </a>
          )}
        </div>
      )}
    </div>
  );
}

export default NewsDetail;