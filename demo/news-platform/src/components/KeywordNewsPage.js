import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import UnifiedNewsCard from './UnifiedNewsCard';
import FloatingChat from './FloatingChat';

const AppContainer = styled.div`
  min-height: 100vh;
  background-color: #f8fafc;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
`;

const MainContent = styled.main`
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
`;

const ContentGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 350px;
  gap: 2rem;
  margin-top: 2rem;
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
`;

const MainColumn = styled.div`
  display: flex;
  flex-direction: column;
  gap: 2rem;
`;

const Sidebar = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  position: sticky;
  top: 2rem;
  height: fit-content;
`;

const SidebarCard = styled.div`
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
`;

const SidebarTitle = styled.h3`
  color: #1e3a8a;
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
`;

const KeywordCloud = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 0.7rem 1.1rem;
  padding: 0.5rem 0.2rem 0.5rem 0.2rem;
`;

const Keyword = styled.span`
  display: inline-block;
  background: linear-gradient(135deg, #f3f4f6 0%, #e0e7ef 100%);
  color: #667eea;
  font-weight: 600;
  font-size: ${props => props.size || 1.1}rem;
  border-radius: 18px;
  padding: 0.3rem 1.1rem;
  cursor: pointer;
  transition: background 0.2s, color 0.2s, box-shadow 0.2s;
  box-shadow: 0 1px 2px rgba(102,126,234,0.04);
  &:hover {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    box-shadow: 0 2px 8px rgba(102,126,234,0.10);
  }
`;

const StatsCard = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
`;

const StatBox = styled.div`
  text-align: center;
  padding: 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
`;

const StatNumber = styled.div`
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
`;

const StatLabel = styled.div`
  font-size: 0.8rem;
  opacity: 0.9;
`;

const SectionTitle = styled.h2`
  color: #1e3a8a;
  font-size: 1.8rem;
  font-weight: 700;
  margin: 2rem 0 1rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  &::before {
    content: "#";
    font-size: 1.5rem;
  }
`;

const hotKeywords = [
  '女足', '大罷免', '颱風', '疫苗', 'AI', '房價', '能源', '選舉', '地震', '股市', 'ChatGPT', '缺水', '升息', '碳中和', '罷工', '通膨', '烏俄戰爭', '台積電', 'AI醫療', '元宇宙'
];

function KeywordNewsPage() {
  const { keyword } = useParams();
  const [showAllNews, setShowAllNews] = useState(false);
  const navigate = useNavigate();

  return (
    <AppContainer>
      <MainContent>
        <ContentGrid>
          <MainColumn>
            <SectionTitle>{keyword}</SectionTitle>
            <UnifiedNewsCard limit={showAllNews ? undefined : 6} keyword={keyword} />
            {(() => {
              // 取得該關鍵字新聞數量
              const { defaultNewsData } = require('./UnifiedNewsCard');
              const filtered = defaultNewsData.filter(news =>
                (news.keywords && news.keywords.some(kw => kw === keyword)) ||
                (news.title && news.title.includes(keyword)) ||
                (news.shortSummary && news.shortSummary.includes(keyword))
              );
              if (!showAllNews && filtered.length >= 4) {
                return (
                  <div style={{ textAlign: 'center', marginTop: '1.5rem' }}>
                    <button
                      style={{
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        color: 'white',
                        border: 'none',
                        borderRadius: '25px',
                        padding: '0.7rem 2.2rem',
                        fontSize: '1rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        boxShadow: '0 2px 8px rgba(102,126,234,0.10)',
                        transition: 'all 0.2s',
                      }}
                      onClick={() => setShowAllNews(true)}
                    >
                      閱讀更多新聞
                    </button>
                  </div>
                );
              }
              return null;
            })()}
          </MainColumn>
          <Sidebar>
            <SidebarCard>
              <SidebarTitle>🔥 熱門搜尋關鍵字</SidebarTitle>
              <KeywordCloud>
                {hotKeywords.map((kw, i) => (
                  <Keyword
                    key={kw}
                    size={1 + Math.random()*0.5}
                    onClick={() => navigate(`/keyword/${encodeURIComponent(kw)}`)}
                  >
                    {kw}
                  </Keyword>
                ))}
              </KeywordCloud>
            </SidebarCard>
            <SidebarCard>
              <SidebarTitle>📊 平台統計</SidebarTitle>
              <StatsCard>
                <StatBox>
                  <StatNumber>1.2T</StatNumber>
                  <StatLabel>總閱讀量</StatLabel>
                </StatBox>
                <StatBox>
                  <StatNumber>45T</StatNumber>
                  <StatLabel>活躍用戶</StatLabel>
                </StatBox>
                <StatBox>
                  <StatNumber>2.8T</StatNumber>
                  <StatLabel>今日文章</StatLabel>
                </StatBox>
                <StatBox>
                  <StatNumber>156T</StatNumber>
                  <StatLabel>專家在線</StatLabel>
                </StatBox>
              </StatsCard>
            </SidebarCard>
          </Sidebar>
        </ContentGrid>
      </MainContent>
      <FloatingChat />
    </AppContainer>
  );
}

export default KeywordNewsPage; 