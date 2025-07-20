import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';

const CardContainer = styled.div`
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  border-left: 4px solid #667eea;
  margin-bottom: 1.5rem;
  
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

const CardTitle = styled.h3`
  margin: 0;
  color: #1e3a8a;
  font-size: 1.4rem;
  font-weight: 600;
  line-height: 1.3;
  flex: 1;
`;

const CardMeta = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
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
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 0.5rem;
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
`;

const StatItem = styled.span`
  display: flex;
  align-items: center;
  gap: 0.3rem;
`;

// 模擬摘要卡片資料
const summaryData = {
  id: 1,
  title: "AI 技術在醫療領域的突破性進展",
  category: "科技",
  date: "2024-01-15",
  sourceCount: 5,
  shortSummary: "最新研究顯示，AI 技術在疾病診斷和治療方案制定方面取得了重大突破，多個醫療機構已開始採用相關技術。",
  longSummary: `人工智慧技術在醫療領域的應用正經歷前所未有的發展。最新研究顯示，AI 技術在疾病診斷和治療方案制定方面取得了重大突破。

根據多家權威醫療機構的報告，AI 輔助診斷系統的準確率已達到 95% 以上，在某些特定疾病的診斷中甚至超過了資深醫師的判斷。這項技術的應用不僅提高了診斷效率，還大幅降低了誤診率。

在治療方案制定方面，AI 系統能夠根據患者的基因組數據、病史和當前症狀，為每位患者量身定制最適合的治療方案。這種個性化醫療模式正在改變傳統的醫療模式。

目前，全球已有超過 200 家醫院開始採用 AI 輔助診斷系統，預計在未來三年內，這一數字將增長到 1000 家以上。專家預測，AI 技術將在未來十年內徹底改變醫療行業的運作方式。`,
  relatedNews: [
    { id: 101, title: "AI 診斷系統獲 FDA 批准" },
    { id: 102, title: "基因編輯技術與 AI 結合的新突破" },
    { id: 103, title: "遠程醫療中的 AI 應用" }
  ]
};

function SummaryCard() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isLongForm, setIsLongForm] = useState(false);

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };

  const toggleForm = () => {
    setIsLongForm(!isLongForm);
  };

  const currentSummary = isLongForm ? summaryData.longSummary : summaryData.shortSummary;

  return (
    <CardContainer>
      <CardHeader>
        <CardTitle>{summaryData.title}</CardTitle>
      </CardHeader>
      
      <CardMeta>
        <CategoryTag>{summaryData.category}</CategoryTag>
        <DateText>{summaryData.date}</DateText>
        <SourceCount>{summaryData.sourceCount} 個來源</SourceCount>
      </CardMeta>
      
      <CardContent>
        <SummaryText isExpanded={isExpanded}>
          {isExpanded ? currentSummary : currentSummary.substring(0, 150) + '...'}
        </SummaryText>
        
        {isExpanded && (
          <ExpandedContent>
            <RelatedNews>
              <RelatedNewsTitle>相關報導</RelatedNewsTitle>
              <RelatedNewsList>
                {summaryData.relatedNews.map(news => (
                  <RelatedNewsItem key={news.id}>
                    <RelatedNewsLink to={`/news/${news.id}`}>
                      {news.title}
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
          <ActionButton onClick={toggleExpanded}>
            {isExpanded ? '收起' : '展開'}
          </ActionButton>
          <ActionButton>收藏</ActionButton>
          <ActionButton>分享</ActionButton>
        </ActionButtons>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <ToggleButton onClick={toggleForm}>
            {isLongForm ? '短篇模式' : '長篇模式'}
          </ToggleButton>
          
          <StatsContainer>
            <StatItem>👁️ 1.2k</StatItem>
            <StatItem>💬 45</StatItem>
            <StatItem>⭐ 89</StatItem>
          </StatsContainer>
        </div>
      </CardActions>
    </CardContainer>
  );
}

export default SummaryCard; 