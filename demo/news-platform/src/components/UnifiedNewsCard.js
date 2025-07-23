import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import TermTooltip from './TermTooltip';

const CardContainer = styled.div`
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  border-left: 4px solid #667eea;
  margin-bottom: 1.5rem;
  position: relative;
  
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
  margin-bottom: 1rem;
`;

const CardTitle = styled(Link)`
  margin: 0;
  color: #1e3a8a;
  font-size: 1.4rem;
  font-weight: 600;
  line-height: 1.3;
  flex: 1;
  text-decoration: none;
  transition: color 0.3s ease;
  
  &:hover {
    color: #667eea;
  }
`;

const CardMeta = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
`;

const CategoryTag = styled.span`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.3rem 0.8rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
`;

const DateText = styled.span`
  color: #6b7280;
  font-size: 0.9rem;
`;

const SourceCount = styled.span`
  background: #f3f4f6;
  color: #4b5563;
  padding: 0.3rem 0.8rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
`;

const KeywordChip = styled.span`
  background: #e0e7ff;
  color: #3730a3;
  border-radius: 12px;
  padding: 0.2rem 0.9rem;
  font-size: 0.95rem;
  font-weight: 500;
  margin-left: 0.3rem;
`;

const CardContent = styled.div`
  margin-bottom: 1rem;
`;

const SummaryText = styled.p`
  color: #4b5563;
  line-height: 1.6;
  margin: 0;
  font-size: ${props => props.isExpanded ? '1rem' : '0.95rem'};
  transition: all 0.3s ease;
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

const ToggleButton = styled.button`
  background: #fbbf24;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: #f59e0b;
    transform: translateY(-1px);
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

const ReadMoreButton = styled.div`
  color: #667eea;
  font-weight: 500;
  font-size: 0.9rem;
  margin-top: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: color 0.3s ease;
  
  &:hover {
    color: #7c3aed;
  }
`;

const HighlightedTerm = styled.span`
  background: linear-gradient(120deg, #fbbf24 0%, #f59e0b 100%);
  color: white;
  padding: 0.1rem 0.3rem;
  border-radius: 4px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: linear-gradient(120deg, #f59e0b 0%, #d97706 100%);
    transform: scale(1.05);
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
  "永續發展": "永續發展指在滿足當代需求的同時，不損害後代滿足其需求的能力。"
};

// 模擬新聞資料
export const defaultNewsData = [
  {
    id: 1,
    title: "人工智慧在醫療領域的突破性進展",
    category: "科技",
    date: "2024-01-15",
    sourceCount: 5,
    shortSummary: "最新研究顯示，<term>人工智慧</term>技術在疾病診斷和治療方案制定方面取得了重大突破。通過<term>機器學習</term>算法，AI系統能夠分析大量醫療數據，為<term>精準醫療</term>提供支持。",
    longSummary: `人工智慧技術在醫療領域的應用正經歷前所未有的發展。最新研究顯示，<term>人工智慧</term>技術在疾病診斷和治療方案制定方面取得了重大突破。

根據多家權威醫療機構的報告，AI輔助診斷系統的準確率已達到95%以上，在某些特定疾病的診斷中甚至超過了資深醫師的判斷。這項技術的應用不僅提高了診斷效率，還大幅降低了誤診率。

在治療方案制定方面，AI系統能夠根據患者的基因組數據、病史和當前症狀，為每位患者量身定制最適合的治療方案。這種<term>精準醫療</term>模式正在改變傳統的醫療模式。

目前，全球已有超過200家醫院開始採用AI輔助診斷系統，預計在未來三年內，這一數字將增長到1000家以上。專家預測，<term>人工智慧</term>技術將在未來十年內徹底改變醫療行業的運作方式。`,
    relatedNews: [
      { id: 101, title: "AI 診斷系統獲 FDA 批准" },
      { id: 102, title: "基因編輯技術與 AI 結合的新突破" },
      { id: 103, title: "遠程醫療中的 AI 應用" }
    ],
    views: "2.3k",
    comments: "45",
    likes: "128",
    keywords: ["人工智慧", "機器學習", "精準醫療"]
  },
  {
    id: 2,
    title: "全球氣候變遷對經濟的影響分析",
    category: "環境",
    date: "2024-01-14",
    sourceCount: 3,
    shortSummary: "專家預測<term>氣候變遷</term>將對全球經濟產生深遠影響，各國政府正積極制定<term>碳中和</term>策略。實現<term>永續發展</term>目標需要全球合作和創新技術。",
    longSummary: `全球<term>氣候變遷</term>已成為21世紀最嚴峻的挑戰之一。最新研究顯示，氣候變遷對全球經濟的影響遠超預期，各國政府正積極制定應對策略。

根據聯合國氣候變遷專門委員會的報告，如果不採取積極行動，到2050年，氣候變遷可能導致全球GDP損失高達18%。這將影響所有經濟部門，從農業到製造業，從金融服務到旅遊業。

各國政府正在加速推進<term>碳中和</term>目標，通過減少溫室氣體排放和增加碳吸收來實現淨零碳排放。這需要大規模的能源轉型、技術創新和投資。

實現<term>永續發展</term>目標需要全球合作，包括發達國家和發展中國家的共同努力。創新技術如再生能源、電動汽車、碳捕獲和儲存等將在這一過程中發揮關鍵作用。`,
    relatedNews: [
      { id: 201, title: "再生能源發展新突破" },
      { id: 202, title: "碳交易市場的發展趨勢" },
      { id: 203, title: "綠色金融創新案例" }
    ],
    views: "1.8k",
    comments: "32",
    likes: "95",
    keywords: ["氣候變遷", "碳中和", "永續發展"]
  },
  {
    id: 3,
    title: "數位貨幣發展趨勢與監管挑戰",
    category: "金融",
    date: "2024-01-13",
    sourceCount: 4,
    shortSummary: "隨著<term>加密貨幣</term>的普及，各國監管機構面臨新的挑戰。<term>數位貨幣</term>的發展正在重塑全球金融體系，<term>金融科技</term>創新推動支付方式變革。",
    longSummary: `<term>數位貨幣</term>的發展正在重塑全球金融體系，各國央行和監管機構面臨前所未有的挑戰和機遇。

隨著<term>加密貨幣</term>如比特幣、以太坊等的普及，傳統金融體系正在經歷深刻變革。這些基於<term>區塊鏈</term>技術的數字資產為金融服務帶來了新的可能性，但也帶來了監管挑戰。

各國央行正在積極研發央行數位貨幣（CBDC），這將是貨幣發行和支付系統的重大創新。CBDC有望提高支付效率、降低交易成本，並增強金融包容性。

<term>金融科技</term>創新正在推動支付方式的變革，從移動支付到跨境支付，從智能合約到去中心化金融（DeFi），新技術正在改變人們使用金融服務的方式。`,
    relatedNews: [
      { id: 301, title: "央行數位貨幣試點進展" },
      { id: 302, title: "加密貨幣監管新政策" },
      { id: 303, title: "區塊鏈在金融中的應用" }
    ],
    views: "3.1k",
    comments: "67",
    likes: "156",
    keywords: ["數位貨幣", "金融科技", "區塊鏈"]
  },
  {
    id: 4,
    title: "太空探索新紀元：火星殖民計劃",
    category: "太空",
    date: "2024-01-12",
    sourceCount: 6,
    shortSummary: "NASA 和 SpaceX 等機構正在推進<term>火星殖民</term>計劃，預計在未來十年內實現人類登陸火星。<term>太空探索</term>技術的進步為人類開拓新的生存空間。",
    longSummary: `人類<term>太空探索</term>正進入一個新紀元，<term>火星殖民</term>計劃代表了人類歷史上最雄心勃勃的科學工程之一。

NASA、SpaceX、歐洲航天局等機構正在積極推進火星探索計劃。SpaceX的星際飛船（Starship）計劃在2024年進行首次載人火星任務，而NASA的阿爾忒彌斯計劃則為火星任務奠定基礎。

火星殖民面臨諸多技術挑戰，包括長途太空旅行、火星環境適應、資源利用等。科學家正在開發先進的生命支持系統、3D打印建築技術、以及利用火星資源的方法。

這項計劃不僅關乎科學探索，更關乎人類的未來。如果成功，火星將成為人類的第二個家園，為人類文明的延續提供新的可能性。`,
    relatedNews: [
      { id: 401, title: "火星探測器最新發現" },
      { id: 402, title: "太空居住艙設計創新" },
      { id: 403, title: "火星資源開發技術" }
    ],
    views: "2.7k",
    comments: "89",
    likes: "234",
    keywords: ["太空探索", "火星殖民", "火星探測"]
  },
  {
    id: 5,
    title: "量子計算技術的商業化應用",
    category: "科技",
    date: "2024-01-11",
    sourceCount: 4,
    shortSummary: "<term>量子計算</term>技術正從實驗室走向商業應用，將在密碼學、藥物研發等領域帶來革命性變化。結合<term>人工智慧</term>技術，量子計算的潛力將進一步釋放。",
    longSummary: `<term>量子計算</term>技術正從實驗室走向商業應用，這將為多個領域帶來革命性變化。量子計算機利用量子力學原理，能夠同時處理大量信息，解決傳統計算機無法處理的複雜問題。

在密碼學領域，量子計算機能夠破解現有的加密算法，但也為量子加密技術的發展提供了機會。科學家正在開發抗量子攻擊的加密方法，以保護信息安全。

在藥物研發方面，量子計算機能夠精確模擬分子結構和化學反應，加速新藥的發現和開發過程。這將大大縮短藥物研發週期，降低研發成本。

結合<term>人工智慧</term>技術，量子計算的潛力將進一步釋放。量子機器學習算法能夠處理更大規模的數據，提供更準確的預測和決策支持。`,
    relatedNews: [
      { id: 501, title: "量子加密技術突破" },
      { id: 502, title: "量子計算在藥物研發中的應用" },
      { id: 503, title: "量子機器學習新進展" }
    ],
    views: "1.9k",
    comments: "41",
    likes: "112",
    keywords: ["量子計算", "量子加密", "量子機器學習"]
  }
];

function UnifiedNewsCard({ limit, keyword }) {
  const [expandedCards, setExpandedCards] = useState({});
  const [tooltipTerm, setTooltipTerm] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  let filteredNews = defaultNewsData;
  if (keyword) {
    filteredNews = defaultNewsData.filter(news =>
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

  const renderHighlightedText = (text) => {
    const parts = text.split(/(<term>.*?<\/term>)/);
    return parts.map((part, index) => {
      if (part.startsWith('<term>') && part.endsWith('</term>')) {
        const term = part.replace(/<\/?term>/g, '');
        return (
          <HighlightedTerm
            key={index}
            onClick={(e) => handleTermClick(term, e)}
            title={`點擊查看 ${term} 的定義`}
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
      {displayNews.map(news => {
        const isExpanded = expandedCards[news.id] || false;
        return (
          <CardContainer key={news.id}>
            <CardHeader>
              <CardTitle to={`/news/${news.id}`}>{news.title}</CardTitle>
            </CardHeader>
            <CardMeta>
              <CategoryTag>{news.category}</CategoryTag>
              <DateText>{news.date}</DateText>
              <SourceCount>{news.sourceCount} 個來源</SourceCount>
              {news.keywords && news.keywords.map(kw => (
                <KeywordChip key={kw}>{kw}</KeywordChip>
              ))}
            </CardMeta>
            <CardContent>
              <SummaryText isExpanded={isExpanded}>
                {isExpanded ? renderHighlightedText(news.shortSummary) : renderHighlightedText(news.shortSummary.substring(0, 150))}
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
            <ReadMoreButton>
              <Link to={`/news/${news.id}`} style={{ color: 'inherit', textDecoration: 'none' }}>
                閱讀全文 →
              </Link>
            </ReadMoreButton>
          </CardContainer>
        );
      })}
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