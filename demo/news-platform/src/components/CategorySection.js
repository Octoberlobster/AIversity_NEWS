import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';

const SectionContainer = styled.div`
  margin: 2rem 0;
`;

const SectionHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
`;

const SectionTitle = styled.h2`
  color: #1e3a8a;
  font-size: 1.8rem;
  font-weight: 600;
  margin: 0;
`;

const ViewAllButton = styled(Link)`
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  transition: all 0.3s ease;
  
  &:hover {
    background: #f3f4f6;
    transform: translateY(-1px);
  }
`;

const CategoryTabs = styled.div`
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  overflow-x: auto;
  padding-bottom: 0.5rem;
  
  &::-webkit-scrollbar {
    height: 4px;
  }
  
  &::-webkit-scrollbar-track {
    background: #f1f5f9;
    border-radius: 2px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 2px;
  }
`;

const CategoryTab = styled.button`
  background: ${props => props.active ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : '#f3f4f6'};
  color: ${props => props.active ? 'white' : '#4b5563'};
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 25px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
  
  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
`;

const NewsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
`;

const NewsCard = styled.div`
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  border-top: 3px solid ${props => props.categoryColor};
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
  }
`;

const NewsCardHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
`;

const NewsCardTitle = styled.h3`
  margin: 0;
  color: #1e3a8a;
  font-size: 1.1rem;
  font-weight: 600;
  line-height: 1.4;
  flex: 1;
`;

const NewsCardMeta = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
`;

const CategoryBadge = styled.span`
  background: ${props => props.color};
  color: white;
  padding: 0.2rem 0.6rem;
  border-radius: 8px;
  font-size: 0.7rem;
  font-weight: 500;
`;

const TimeBadge = styled.span`
  background: #f3f4f6;
  color: #6b7280;
  padding: 0.2rem 0.6rem;
  border-radius: 8px;
  font-size: 0.7rem;
`;

const NewsCardDescription = styled.p`
  color: #4b5563;
  font-size: 0.9rem;
  line-height: 1.5;
  margin: 0 0 1rem 0;
`;

const NewsCardActions = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const ReadMoreLink = styled(Link)`
  color: #667eea;
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
  transition: color 0.3s ease;
  
  &:hover {
    color: #7c3aed;
  }
`;

const StatsRow = styled.div`
  display: flex;
  gap: 1rem;
  font-size: 0.8rem;
  color: #6b7280;
`;

const StatItem = styled.span`
  display: flex;
  align-items: center;
  gap: 0.2rem;
`;

// 分類配置
const categories = [
  { id: 'tech', name: '科技', color: '#667eea' },
  { id: 'finance', name: '金融', color: '#10b981' },
  { id: 'environment', name: '環境', color: '#059669' },
  { id: 'health', name: '醫療', color: '#ef4444' },
  { id: 'space', name: '太空', color: '#8b5cf6' },
  { id: 'education', name: '教育', color: '#f59e0b' },
  { id: 'sports', name: '體育', color: '#06b6d4' },
  { id: 'culture', name: '文化', color: '#ec4899' }
];

// 模擬新聞資料
const newsData = {
  tech: [
    {
      id: 1,
      title: "量子計算技術取得重大突破",
      description: "研究團隊成功實現了100量子比特的穩定控制，為量子計算的商業化應用奠定基礎。",
      time: "2小時前",
      views: "1.5k",
      comments: "23"
    },
    {
      id: 2,
      title: "AI 語言模型能力再升級",
      description: "最新版本的語言模型在理解和生成能力方面都有顯著提升，應用範圍進一步擴大。",
      time: "4小時前",
      views: "2.1k",
      comments: "45"
    }
  ],
  finance: [
    {
      id: 3,
      title: "全球央行數位貨幣發展趨勢",
      description: "各國央行加速推進數位貨幣研發，這將重塑全球金融體系和支付方式。",
      time: "1小時前",
      views: "3.2k",
      comments: "67"
    },
    {
      id: 4,
      title: "加密貨幣市場新動向",
      description: "比特幣價格突破新高，機構投資者對加密貨幣的興趣持續增加。",
      time: "3小時前",
      views: "2.8k",
      comments: "89"
    }
  ],
  environment: [
    {
      id: 5,
      title: "全球氣候變遷最新報告",
      description: "聯合國氣候變遷報告顯示，全球溫室氣體排放量仍在上升，需要更積極的減碳行動。",
      time: "5小時前",
      views: "4.1k",
      comments: "156"
    },
    {
      id: 6,
      title: "再生能源發展新突破",
      description: "太陽能發電效率創新高，成本持續下降，為能源轉型帶來新希望。",
      time: "6小時前",
      views: "2.9k",
      comments: "78"
    }
  ],
  health: [
    {
      id: 7,
      title: "新冠疫苗研發新進展",
      description: "科學家發現新的疫苗技術，可能對變種病毒提供更好的保護效果。",
      time: "2小時前",
      views: "5.3k",
      comments: "234"
    },
    {
      id: 8,
      title: "精準醫療技術突破",
      description: "基因編輯技術在治療罕見疾病方面取得重大進展，為患者帶來新希望。",
      time: "4小時前",
      views: "3.7k",
      comments: "123"
    }
  ]
};

function CategorySection() {
  const [activeCategory, setActiveCategory] = useState('tech');

  const handleCategoryChange = (categoryId) => {
    setActiveCategory(categoryId);
  };

  const currentNews = newsData[activeCategory] || [];
  const currentCategory = categories.find(cat => cat.id === activeCategory);

  return (
    <SectionContainer>
      <SectionHeader>
        <SectionTitle>分類精選</SectionTitle>
        <ViewAllButton to={`/categories/${activeCategory}`}>
          查看全部 →
        </ViewAllButton>
      </SectionHeader>
      
      <CategoryTabs>
        {categories.map(category => (
          <CategoryTab
            key={category.id}
            active={activeCategory === category.id}
            onClick={() => handleCategoryChange(category.id)}
          >
            {category.name}
          </CategoryTab>
        ))}
      </CategoryTabs>
      
      <NewsGrid>
        {currentNews.map(news => (
          <NewsCard key={news.id} categoryColor={currentCategory.color}>
            <NewsCardHeader>
              <NewsCardTitle>{news.title}</NewsCardTitle>
            </NewsCardHeader>
            
            <NewsCardMeta>
              <CategoryBadge color={currentCategory.color}>
                {currentCategory.name}
              </CategoryBadge>
              <TimeBadge>{news.time}</TimeBadge>
            </NewsCardMeta>
            
            <NewsCardDescription>{news.description}</NewsCardDescription>
            
            <NewsCardActions>
              <ReadMoreLink to={`/news/${news.id}`}>
                閱讀全文 →
              </ReadMoreLink>
              <StatsRow>
                <StatItem>👁️ {news.views}</StatItem>
                <StatItem>💬 {news.comments}</StatItem>
              </StatsRow>
            </NewsCardActions>
          </NewsCard>
        ))}
      </NewsGrid>
    </SectionContainer>
  );
}

export default CategorySection; 