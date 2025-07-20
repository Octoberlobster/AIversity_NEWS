import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import TermTooltip from './TermTooltip';

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
`;

const Title = styled.h2`
  color: #1e3a8a;
  margin-bottom: 2rem;
  font-size: 2rem;
  font-weight: 600;
`;

const NewsGrid = styled.div`
  display: grid;
  gap: 1.5rem;
`;

const NewsCard = styled(Link)`
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  text-decoration: none;
  color: inherit;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  border-left: 4px solid #667eea;
  position: relative;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    border-left-color: #7c3aed;
  }
`;

const NewsTitle = styled.h3`
  margin: 0 0 0.5rem 0;
  color: #1e3a8a;
  font-size: 1.3rem;
  font-weight: 600;
  line-height: 1.4;
`;

const NewsMeta = styled.div`
  color: #6b7280;
  font-size: 0.9rem;
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
  align-items: center;
`;

const NewsPreview = styled.p`
  color: #4b5563;
  margin: 0.5rem 0 0 0;
  line-height: 1.6;
  font-size: 0.95rem;
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

const CategoryTag = styled.span`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.3rem 0.8rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
`;

const StatsRow = styled.div`
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
  font-size: 0.8rem;
  color: #6b7280;
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
const mockNews = [
  {
    id: 1,
    title: "人工智慧在醫療領域的突破性進展",
    preview: "最新研究顯示，<term>人工智慧</term>技術在疾病診斷和治療方案制定方面取得了重大突破。通過<term>機器學習</term>算法，AI系統能夠分析大量醫療數據，為<term>精準醫療</term>提供支持。",
    date: "2024-01-15",
    category: "科技",
    views: "2.3k",
    comments: "45",
    likes: "128"
  },
  {
    id: 2,
    title: "全球氣候變遷對經濟的影響分析",
    preview: "專家預測<term>氣候變遷</term>將對全球經濟產生深遠影響，各國政府正積極制定<term>碳中和</term>策略。實現<term>永續發展</term>目標需要全球合作和創新技術。",
    date: "2024-01-14",
    category: "環境",
    views: "1.8k",
    comments: "32",
    likes: "95"
  },
  {
    id: 3,
    title: "數位貨幣發展趨勢與監管挑戰",
    preview: "隨著<term>加密貨幣</term>的普及，各國監管機構面臨新的挑戰。<term>數位貨幣</term>的發展正在重塑全球金融體系，<term>金融科技</term>創新推動支付方式變革。",
    date: "2024-01-13",
    category: "金融",
    views: "3.1k",
    comments: "67",
    likes: "156"
  },
  {
    id: 4,
    title: "太空探索新紀元：火星殖民計劃",
    preview: "NASA 和 SpaceX 等機構正在推進<term>火星殖民</term>計劃，預計在未來十年內實現人類登陸火星。<term>太空探索</term>技術的進步為人類開拓新的生存空間。",
    date: "2024-01-12",
    category: "太空",
    views: "2.7k",
    comments: "89",
    likes: "234"
  },
  {
    id: 5,
    title: "量子計算技術的商業化應用",
    preview: "<term>量子計算</term>技術正從實驗室走向商業應用，將在密碼學、藥物研發等領域帶來革命性變化。結合<term>人工智慧</term>技術，量子計算的潛力將進一步釋放。",
    date: "2024-01-11",
    category: "科技",
    views: "1.9k",
    comments: "41",
    likes: "112"
  }
];

function EnhancedNewsList({ hideTitle }) {
  const [tooltipTerm, setTooltipTerm] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

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
    <Container>
      {!hideTitle && <Title>最新新聞</Title>}
      <NewsGrid>
        {mockNews.map(news => (
          <NewsCard key={news.id} to={`/news/${news.id}`}>
            <NewsTitle>{news.title}</NewsTitle>
            <NewsPreview>
              {renderHighlightedText(news.preview)}
            </NewsPreview>
            <NewsMeta>
              <CategoryTag>{news.category}</CategoryTag>
              <span>{news.date}</span>
            </NewsMeta>
            <StatsRow>
              <StatItem>👁️ {news.views}</StatItem>
              <StatItem>💬 {news.comments}</StatItem>
              <StatItem>⭐ {news.likes}</StatItem>
            </StatsRow>
            <ReadMoreButton>
              閱讀全文 →
            </ReadMoreButton>
          </NewsCard>
        ))}
      </NewsGrid>

      {tooltipTerm && (
        <TermTooltip
          term={tooltipTerm}
          definition={termDefinitions[tooltipTerm]}
          position={tooltipPosition}
          onClose={closeTooltip}
        />
      )}
    </Container>
  );
}

export default EnhancedNewsList; 