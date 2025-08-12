import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import './../css/NewDetail.css';
import ChatRoom from './ChatRoom';
import TermTooltip from './TermTooltip';

// --- 導入後端新聞資料 ---
import rawBackendData from './../final_comprehensive_reports_20250812_013357.json';
import keywordExplanations from './../keyword_explanations.json'
import imageMatadata from './../image_metadata.json';

// 將後端資料轉換為前端詳細頁面格式
const convertBackendToDetailFormat = (backendData) => {
  const result = {};
  backendData.forEach((story, index) => {
    const story_index = (index + 1).toString();
    const keywords = keywordExplanations[story_index]?.keywords || [];
    const terms = keywords.map(item => item.term);
    const description = imageMatadata.images[index].description || "";
    result[index + 2] = {
      title: story.comprehensive_report.title || "無標題",
      date: story.processed_at || new Date().toISOString(),
      author: "Gemini",
      image: `/ke-xue-yu-ke-ji-/${story_index}.png`,
      imageCaption: description,
      short: story.comprehensive_report.versions.short || "",
      long: story.comprehensive_report.versions.long || "",
      keywords: [],
      terms: terms,
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
    short: `最新研究顯示，人工智慧技術在疾病診斷和治療方案制定方面取得了重大突破。研究團隊利用機器學習算法分析了數千個病例，成功提高了診斷準確率達95%以上。\n\n這項技術特別在影像識別方面表現出色，能夠快速識別X光片、CT掃描等醫學影像中的異常情況。專家表示，這將大大減輕醫護人員的工作負擔，並提高醫療效率。\n\n然而，這項技術的應用也面臨著倫理考量和隱私保護等挑戰。如何在提高醫療效率的同時保護患者隱私，成為業界關注的焦點。`,
    long: `最新研究顯示，人工智慧技術在疾病診斷和治療方案制定方面取得了重大突破。這項由國際頂尖醫療機構聯合進行的研究，歷時三年，投入資金超過數千萬美元，最終在機器學習和深度學習技術的結合下，成功開發出了新一代醫療AI系統。\n\n研究團隊利用機器學習算法分析了數千個病例，涵蓋了從常見疾病到罕見病症的各種情況。通過對大量數據的深度學習，AI系統能夠識別出人類醫生可能忽略的細微症狀，成功提高了診斷準確率達95%以上，遠超傳統診斷方法的準確率。\n\n這項技術特別在影像識別方面表現出色，能夠快速識別X光片、CT掃描、核磁共振等各種醫學影像中的異常情況。AI系統不僅能夠識別腫瘤、骨折等明顯病變，還能夠發現早期癌症的微小徵兆，為早期治療提供了寶貴的時間窗口。\n\n專家表示，這將大大減輕醫護人員的工作負擔，並提高醫療效率。在資源緊張的醫療環境中，AI助手可以幫助醫生快速篩選病例，讓醫生能夠將更多時間投入到需要專業判斷的複雜病例中。\n\n然而，這項技術的應用也面臨著倫理考量和隱私保護等挑戰。如何在提高醫療效率的同時保護患者隱私，成為業界關注的焦點。此外，AI診斷結果的責任歸屬問題也需要法律和倫理框架的完善。\n\n未來，這項技術有望在全球範圍內推廣應用，為更多患者提供更準確、更快速的醫療服務。同時，研究團隊也正在開發針對不同地區和人群的個性化AI模型，以確保技術的普適性和有效性。`,
    keywords: ["AI", "醫療", "影像識別"],
    terms: ["人工智慧", "機器學習", "影像識別", "倫理考量", "隱私保護", "深度學習"],
    related: [],
    source: "https://www.healthai-news.com/article/ai-medical-breakthrough"
  },
  ...convertBackendToDetailFormat(rawBackendData)
};

console.log(mockNewsData);

const buildTermDefinitions = () => {
  const definitions = {};
  
  // 遍歷所有新聞的關鍵字
  Object.values(keywordExplanations).forEach(story => {
    story.keywords.forEach(keyword => {
      if (keyword.term && keyword.definition) {
        definitions[keyword.term] = keyword.definition;
      }
    });
  });

  // 合併原有的通用定義
  return {
      ...definitions,
      "人工智慧": "人工智慧（AI）是模擬人類智能的計算機系統，能夠學習、推理、感知和解決問題。",
      "機器學習": "機器學習是AI的一個子集，通過算法讓計算機從數據中學習模式，無需明確編程。",
      "深度學習": "深度學習使用多層神經網絡來處理複雜的數據模式，是機器學習的先進技術。",
      "量子計算": "量子計算利用量子力學原理進行信息處理，具有超越傳統計算機的潛力。",
      "區塊鏈": "區塊鏈是一種分散式數據庫技術，用於安全記錄和驗證交易信息。",
      "加密貨幣": "加密貨幣是基於區塊鏈技術的數字貨幣，如比特幣、以太坊等。",
      "氣候變遷": "氣候變遷指地球氣候系統的長期變化，主要由人類活動和自然因素引起。",
      "碳中和": "碳中和指通過減少碳排放和增加碳吸收，實現淨零碳排放的目標。",
      "精準醫療": "精準醫療根據個人的基因、環境和生活方式制定個性化治療方案。",
      "基因編輯": "基因編輯技術可以精確修改生物體的DNA序列，用於治療疾病和改良作物。",
      "太空探索": "太空探索是人類對宇宙的科學研究和探索活動，包括行星探測和載人航天。",
      "火星殖民": "火星殖民計劃旨在在火星建立人類永久居住地，是人類太空探索的重要目標。",
      "數位貨幣": "數位貨幣是中央銀行發行的電子形式法定貨幣，具有法定地位。",
      "金融科技": "金融科技（FinTech）結合金融服務和技術創新，改變傳統金融業態。",
      "永續發展": "永續發展指在滿足當代需求的同時，不損害後代滿足其需求的能力。",
      "三級三審": "指案件經過地方法院、高等法院、最高法院三級法院，以及各級法院三次審判程序的制度。確保司法審查的嚴謹性與公正性。",
      "IRB" : "在台灣，IRB 通常指「人體試驗委員會」（Institutional Review Board），負責審查和監督涉及人體的研究，以確保研究的倫理性和參與者的安全與權益。",
      "SDGs": "可持續發展目標（Sustainable Development Goals），是聯合國在2015年制定的17個全球發展目標，旨在2030年前消除貧窮、保護地球並確保所有人享有和平與繁榮。"
  };
};
const termDefinitions = buildTermDefinitions();

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

  const renderArticleText = (text) => {
    if (!text) return '';
    if (!newsData.terms || !Array.isArray(newsData.terms)) {
      return text;
    }

    // 建立正則表達式，匹配所有 terms
    const termsPattern = new RegExp(
      `(${newsData.terms.map(term => term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`,
      'g'
    );

    // 將文字分割成片段
    const parts = text.split(termsPattern);

    return parts.map((part, index) => {
      const isTerm = newsData.terms.includes(part);
      if (isTerm) {
        return (
          <strong
            key={index}
            className="term term--clickable"
            onClick={(e) => handleTermClick(part, e)}
          >
            {part}
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