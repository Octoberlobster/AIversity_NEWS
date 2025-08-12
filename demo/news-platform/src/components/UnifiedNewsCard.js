import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './../css/UnifiedNewsCard.css';
import TermTooltip from './TermTooltip';
import rawBackendData from './../final_comprehensive_reports_20250812_013357.json';
import keywordExplanations from './../keyword_explanations.json'

// 從 keywordExplanations 建立 termDefinitions
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
console.log(termDefinitions);

// 轉換後端資料為前端格式
const convertBackendToFrontend = (backendData) => {

  return backendData.map((story, index) => {
    const story_index = (index + 1).toString();
    const keywords = keywordExplanations[story_index]?.keywords || [];
    const terms = keywords.map(item => item.term);
    return {
      id: index + 2,
      title: story.comprehensive_report.title || "無標題",
      category: story.story_info.category || "未分類",
      date: story.processed_at || new Date().toISOString(),
      author: "Gemini",
      sourceCount: story.story_info.total_articles || 0,
      shortSummary: story.comprehensive_report.versions.ultra_short || "",
      relatedNews: [],
      views: `${Math.floor(Math.random() * 10)}.${Math.floor(Math.random() * 9)}k`,
      keywords: [],
      terms: terms,
    };
  });
}

// 組合預設資料和後端資料
export const defaultNewsData = [
  {
    id: 1,
    title: "人工智慧在醫療領域的突破性進展",
    category: "科學與科技",
    date: "2024-01-15 14:30",
    author: "張明華",
    sourceCount: 5,
    shortSummary: "最新研究顯示，人工智慧技術在疾病診斷和治療方案制定方面取得了重大突破。通過機器學習算法，AI系統能夠分析大量醫療數據，為精準醫療提供支持。",
    relatedNews: [
      { id: 101, title: "AI 診斷系統獲 FDA 批准" },
      { id: 102, title: "基因編輯技術與 AI 結合的新突破" },
      { id: 103, title: "遠程醫療中的 AI 應用" }
    ],
    views: "2.3k",
    keywords: ["AI", "醫療", "診斷"],
    terms: ["人工智慧", "機器學習", "精準醫療"]
  },
  ...convertBackendToFrontend(rawBackendData)
];

function UnifiedNewsCard({ limit, keyword, customData }) {
  const [expandedCards, setExpandedCards] = useState({});
  const [tooltipTerm, setTooltipTerm] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  let filteredNews = customData || defaultNewsData;
  if (keyword) {
    filteredNews = filteredNews.filter((news) =>
      (news.keywords && news.keywords.some((kw) => kw === keyword)) ||
      (news.title && news.title.includes(keyword)) ||
      (news.shortSummary && news.shortSummary.includes(keyword))
    );
  }
  const displayNews = limit ? filteredNews.slice(0, limit) : filteredNews;

  const toggleExpanded = (cardId) => {
    setExpandedCards((prev) => ({ ...prev, [cardId]: !prev[cardId] }));
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
    if (!newsTerms || !Array.isArray(newsTerms)) return text;

    // 建立正則表達式，匹配所有 terms（注意跳脫特殊字元）
    const termsPattern = new RegExp(
      `(${newsTerms.map(term => term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`,
      'g'
    );

    // 將文字分割成片段
    const parts = text.split(termsPattern);
      return parts.map((part, index) => {
      // 檢查這個片段是否是 term
      const isTerm = newsTerms.includes(part);

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

  return (
    <div className="unifiedNewsCard">
      <div className="newsGrid">
        {displayNews.map((news) => {
          const isExpanded = !!expandedCards[news.id];
          return (
            <div className="card" key={news.id}>
              <div className="card__header">
                <Link className="card__title" to={`/news/${news.id}`}>
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
                        {news.relatedNews.map((r) => (
                          <li className="relatedNews__item" key={r.id}>
                            <Link className="relatedNews__link" to={`/news/${r.id}`}>
                              {r.title}
                            </Link>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>

              <div className="card__actions">
                <div className="actionButtons">
                  <button className="actionButton" onClick={() => toggleExpanded(news.id)}>
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

      {tooltipTerm && (
        <TermTooltip
          term={tooltipTerm}
          definition={termDefinitions[tooltipTerm]}
          position={tooltipPosition}
          onClose={closeTooltip}
        />
      )}
    </div>
  );
}

export default UnifiedNewsCard;