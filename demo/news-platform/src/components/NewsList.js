import React from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
`;

const Title = styled.h2`
  color: #333;
  margin-bottom: 2rem;
  font-size: 2.5rem;
  text-align: center;
`;

const NewsGrid = styled.div`
  display: grid;
  gap: 1.5rem;
`;

const NewsCard = styled(Link)`
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  text-decoration: none;
  color: inherit;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  border-left: 4px solid #667eea;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    border-left-color: #764ba2;
  }
`;

const NewsTitle = styled.h3`
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 1.3rem;
  font-weight: 600;
`;

const NewsMeta = styled.div`
  color: #666;
  font-size: 0.9rem;
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
`;

const NewsPreview = styled.p`
  color: #555;
  margin: 0.5rem 0 0 0;
  line-height: 1.5;
`;

// 模擬新聞資料
const mockNews = [
  {
    id: 1,
    title: "人工智慧在醫療領域的突破性進展",
    preview: "最新研究顯示，AI 技術在疾病診斷和治療方案制定方面取得了重大突破...",
    date: "2024-01-15",
    category: "科技"
  },
  {
    id: 2,
    title: "全球氣候變遷對經濟的影響分析",
    preview: "專家預測氣候變遷將對全球經濟產生深遠影響，各國政府正積極制定應對策略...",
    date: "2024-01-14",
    category: "環境"
  },
  {
    id: 3,
    title: "數位貨幣發展趨勢與監管挑戰",
    preview: "隨著加密貨幣的普及，各國監管機構面臨新的挑戰，需要平衡創新與風險控制...",
    date: "2024-01-13",
    category: "金融"
  },
  {
    id: 4,
    title: "太空探索新紀元：火星殖民計劃",
    preview: "NASA 和 SpaceX 等機構正在推進火星殖民計劃，預計在未來十年內實現人類登陸火星...",
    date: "2024-01-12",
    category: "太空"
  },
  {
    id: 5,
    title: "量子計算技術的商業化應用",
    preview: "量子計算技術正從實驗室走向商業應用，將在密碼學、藥物研發等領域帶來革命性變化...",
    date: "2024-01-11",
    category: "科技"
  }
];

function NewsList({ hideTitle }) {
  return (
    <Container>
      {!hideTitle && <Title>最新新聞</Title>}
      <NewsGrid>
        {mockNews.map(news => (
          <NewsCard key={news.id} to={`/news/${news.id}`}>
            <NewsTitle>{news.title}</NewsTitle>
            <NewsPreview>{news.preview}</NewsPreview>
            <NewsMeta>
              <span>{news.date}</span>
              <span>•</span>
              <span>{news.category}</span>
            </NewsMeta>
          </NewsCard>
        ))}
      </NewsGrid>
    </Container>
  );
}

export default NewsList; 