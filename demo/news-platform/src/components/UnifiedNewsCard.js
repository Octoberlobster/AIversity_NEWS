import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import TermTooltip from './TermTooltip';

const NewsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
  
  @media (max-width: 1200px) {
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  }
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const CardContainer = styled.div`
  background: white;
  border-radius: 16px;
  padding: 1.2rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  border-left: 4px solid #667eea;
  position: relative;
  height: fit-content;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    border-left-color: #7c3aed;
  }
`;

const CardHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.8rem;
`;

const CardTitle = styled(Link)`
  margin: 0;
  color: #1e3a8a;
  font-size: 1.2rem;
  font-weight: 600;
  line-height: 1.3;
  flex: 1;
  text-decoration: none;
  transition: color 0.3s ease;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  
  &:hover {
    color: #667eea;
  }
`;

const CardMeta = styled.div`
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin-bottom: 0.8rem;
  flex-wrap: wrap;
`;

const CardInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin-bottom: 0.8rem;
  flex-wrap: wrap;
  font-size: 0.8rem;
  color: #6b7280;
`;

const CategoryTag = styled.span`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.2rem 0.6rem;
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 500;
`;

const DateText = styled.span`
  color: #6b7280;
  font-size: 0.8rem;
`;

const AuthorText = styled.span`
  color: #6b7280;
  font-size: 0.8rem;
`;

const SourceCount = styled.span`
  background: #f3f4f6;
  color: #4b5563;
  padding: 0.2rem 0.6rem;
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 500;
`;

const KeywordChip = styled.span`
  background: #e0e7ff;
  color: #3730a3;
  border-radius: 10px;
  padding: 0.15rem 0.7rem;
  font-size: 0.8rem;
  font-weight: 500;
  margin-left: 0.2rem;
`;

const CardContent = styled.div`
  margin-bottom: 0.8rem;
`;

const SummaryText = styled.p`
  color: #4b5563;
  line-height: 1.5;
  margin: 0;
  font-size: ${props => props.isExpanded ? '0.9rem' : '0.85rem'};
  transition: all 0.3s ease;
  display: -webkit-box;
  -webkit-line-clamp: ${props => props.isExpanded ? 'none' : '3'};
  -webkit-box-orient: vertical;
  overflow: hidden;
`;

const ExpandedContent = styled.div`
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
  animation: slideDown 0.3s ease;
  
  @keyframes slideDown {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
`;

const RelatedNews = styled.div`
  margin-top: 1rem;
`;

const RelatedNewsTitle = styled.h4`
  color: #374151;
  font-size: 1rem;
  margin: 0 0 0.5rem 0;
  font-weight: 600;
`;

const RelatedNewsList = styled.ul`
  list-style: none;
  padding: 0;
  margin: 0;
`;

const RelatedNewsItem = styled.li`
  padding: 0.5rem 0;
  border-bottom: 1px solid #f3f4f6;
  
  &:last-child {
    border-bottom: none;
  }
`;

const RelatedNewsLink = styled(Link)`
  color: #4b5563;
  text-decoration: none;
  font-size: 0.9rem;
  transition: color 0.3s ease;
  
  &:hover {
    color: #667eea;
  }
`;

const CardActions = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  flex-wrap: wrap;
  gap: 1rem;
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
`;

const ActionButton = styled.button`
  background: ${props => props.primary ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : '#f3f4f6'};
  color: ${props => props.primary ? 'white' : '#4b5563'};
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
`;

const StatsContainer = styled.div`
  display: flex;
  gap: 1rem;
  font-size: 0.8rem;
  color: #6b7280;
  flex-wrap: wrap;
`;

const StatItem = styled.span`
  display: flex;
  align-items: center;
  gap: 0.3rem;
`;

const HighlightedTerm = styled.strong`
  color: #667eea;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    color: #5a67d8;
    text-decoration: underline;
  }
`;

// 關鍵字定義
const termDefinitions = {
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
  "SDGs": "可持續發展目標（Sustainable Development Goals），是聯合國在2015年制定的17個全球發展目標，旨在2030年前消除貧窮、保護地球並確保所有人享有和平與繁榮。",
  "逆行行星": "行星在天空中看似反方向運動的天文現象，實際由觀測位置與軌道差異造成。",
  "聯星系統": "由兩顆或多顆恆星互相繞行組成，透過引力維持穩定運動的恆星系統。",
  "南極座ν": "位於南極座的一顆恆星，肉眼可見，常作為南天星圖定位參考之一。",
  "白矮星": "恆星演化末期形成的高密度天體，體積小但質量接近太陽，表面極熱。",
  "逕向速度": "天體沿視線方向相對觀測者的速度，透過多普勒效應測量，常用於探測系外行星。"
};

// 模擬新聞資料
export const defaultNewsData = [
  {
    id: 1,
    title: "逆行行星挑戰行星形成理論：南極座ν聯星系統發現“第二代行星”",
    category: "科學與科技",
    date: "2025-08-10 19:22",
    sourceCount: 3,
    shortSummary: "國際團隊在南極座ν聯星系統發現逆行行星，質量約木星14倍，挑戰傳統行星形成理論，或為第二代行星有力證據。",
    relatedNews: [
      { id: 101, title: "AI 診斷系統獲 FDA 批准" },
      { id: 102, title: "基因編輯技術與 AI 結合的新突破" },
      { id: 103, title: "遠程醫療中的 AI 應用" }
    ],
    views: "2",
    keywords: ["逆行行星", "天文"], // 領域關鍵字
    terms: ["逆行行星", "聯星系統", "南極座ν", "白矮星", "逕向速度"] // 專有名詞
  },
];

function UnifiedNewsCard({ limit, keyword, customData }) {
  const [expandedCards, setExpandedCards] = useState({});
  const [tooltipTerm, setTooltipTerm] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  let filteredNews = customData || defaultNewsData;
  if (keyword) {
    filteredNews = filteredNews.filter(news =>
      (news.keywords && news.keywords.some(kw => kw === keyword)) ||
      (news.title && news.title.includes(keyword)) ||
      (news.shortSummary && news.shortSummary.includes(keyword))
    );
  }
  const displayNews = limit ? filteredNews.slice(0, limit) : filteredNews;

  const toggleExpanded = (cardId) => {
    setExpandedCards(prev => ({
      ...prev,
      [cardId]: !prev[cardId]
    }));
  };

  const handleTermClick = (term, event) => {
    event.preventDefault();
    const rect = event.target.getBoundingClientRect();
    setTooltipPosition({
      x: rect.left + rect.width / 2,
      y: rect.top - 10
    });
    setTooltipTerm(term);
  };

  const closeTooltip = () => {
    setTooltipTerm(null);
  };

  const renderHighlightedText = (text, newsTerms) => {
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        const term = part.slice(2, -2);
        const isClickable = newsTerms && newsTerms.includes(term);
        return (
          <HighlightedTerm
            key={index}
            onClick={isClickable ? (e) => handleTermClick(term, e) : undefined}
            title={isClickable ? `點擊查看 ${term} 的定義` : undefined}
            style={{
              cursor: isClickable ? 'pointer' : 'default',
              color: isClickable ? '#667eea' : 'inherit',
              textDecoration: isClickable ? 'underline' : 'none'
            }}
          >
            {term}
          </HighlightedTerm>
        );
      }
      return part;
    });
  };

  return (
    <div>
      <NewsGrid>
        {displayNews.map(news => {
          const isExpanded = expandedCards[news.id] || false;
          return (
            <CardContainer key={news.id}>
              <CardHeader>
                <CardTitle to={`/news/${news.id}`}>{news.title}</CardTitle>
              </CardHeader>
              <CardInfo>
                <DateText>{news.date}</DateText>
                <AuthorText>記者 {news.author}</AuthorText>
              </CardInfo>
              <CardMeta>
                <CategoryTag>{news.category}</CategoryTag>
                <SourceCount>{news.sourceCount} 個來源</SourceCount>
                {news.keywords && news.keywords.map(kw => (
                  <KeywordChip key={kw}>{kw}</KeywordChip>
                ))}
              </CardMeta>
              <CardContent>
                <SummaryText isExpanded={isExpanded}>
                  {isExpanded ? renderHighlightedText(news.shortSummary, news.terms) : renderHighlightedText(news.shortSummary, news.terms)}
                </SummaryText>
                {isExpanded && (
                  <ExpandedContent>
                    <RelatedNews>
                      <RelatedNewsTitle>相關報導</RelatedNewsTitle>
                      <RelatedNewsList>
                        {news.relatedNews.map(relatedNews => (
                          <RelatedNewsItem key={relatedNews.id}>
                            <RelatedNewsLink to={`/news/${relatedNews.id}`}>
                              {relatedNews.title}
                            </RelatedNewsLink>
                          </RelatedNewsItem>
                        ))}
                      </RelatedNewsList>
                    </RelatedNews>
                  </ExpandedContent>
                )}
              </CardContent>
              <CardActions>
                <ActionButtons>
                  <ActionButton onClick={() => toggleExpanded(news.id)}>
                    {isExpanded ? '收起' : '展開'}
                  </ActionButton>
                </ActionButtons>
                <StatsContainer>
                  <StatItem>👁️ {news.views}</StatItem>
                </StatsContainer>
              </CardActions>
            </CardContainer>
          );
        })}
      </NewsGrid>
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