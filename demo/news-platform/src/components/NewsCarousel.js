import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';

const CarouselContainer = styled.div`
  position: relative;
  width: 100%;
  height: 400px;
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
`;

const SectionTitle = styled.h2`
  color: #1e3a8a;
  font-size: 1.8rem;
  font-weight: 700;
  margin: 0 0 1rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  
  &::before {
    content: "🔥";
    font-size: 1.5rem;
  }
`;

const CarouselSlide = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: ${props => props.active ? 1 : 0};
  transition: opacity 0.8s ease-in-out;
  background: linear-gradient(135deg, ${props => props.gradientStart} 0%, ${props => props.gradientEnd} 100%);
  display: flex;
  align-items: center;
  padding: 2rem;
`;

const SlideContent = styled.div`
  color: white;
  max-width: 600px;
  z-index: 2;
`;

const SlideCategory = styled.span`
  background: rgba(255, 255, 255, 0.2);
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 500;
  margin-bottom: 1rem;
  display: inline-block;
`;

const SlideTitle = styled.h2`
  font-size: 2.5rem;
  font-weight: 700;
  margin: 0 0 1rem 0;
  line-height: 1.2;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
`;

const SlideDescription = styled.p`
  font-size: 1.1rem;
  line-height: 1.6;
  margin: 0 0 1.5rem 0;
  opacity: 0.9;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
`;

const SlideButton = styled(Link)`
  background: rgba(255, 255, 255, 0.2);
  color: white;
  text-decoration: none;
  padding: 0.75rem 2rem;
  border-radius: 25px;
  font-weight: 600;
  transition: all 0.3s ease;
  border: 2px solid rgba(255, 255, 255, 0.3);
  
  &:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }
`;

const CarouselIndicators = styled.div`
  position: absolute;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 0.5rem;
  z-index: 3;
`;

const Indicator = styled.button`
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: none;
  background: ${props => props.active ? 'white' : 'rgba(255, 255, 255, 0.4)'};
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: ${props => props.active ? 'white' : 'rgba(255, 255, 255, 0.6)'};
    transform: scale(1.2);
  }
`;

const CarouselControls = styled.div`
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 100%;
  display: flex;
  justify-content: space-between;
  padding: 0 1rem;
  z-index: 3;
`;

const ControlButton = styled.button`
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 1.5rem;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: scale(1.1);
  }
`;

const SlideOverlay = styled.div`
  position: absolute;
  top: 0;
  right: 0;
  width: 40%;
  height: 100%;
  background: linear-gradient(45deg, transparent 0%, rgba(0, 0, 0, 0.3) 100%);
  z-index: 1;
`;

// 模擬輪播新聞資料
const carouselNews = [
  {
    id: 1,
    title: "AI 技術突破：量子計算與人工智慧的融合",
    description: "最新研究顯示，量子計算技術與人工智慧的結合將為科技發展帶來革命性突破，預計在未來五年內實現商業化應用。",
    category: "科技",
    gradientStart: "#667eea",
    gradientEnd: "#764ba2"
  },
  {
    id: 2,
    title: "全球氣候變遷：各國積極應對的新政策",
    description: "面對日益嚴峻的氣候挑戰，各國政府紛紛推出新的環保政策，致力於實現碳中和目標。",
    category: "環境",
    gradientStart: "#11998e",
    gradientEnd: "#38ef7d"
  },
  {
    id: 3,
    title: "數位貨幣革命：央行數位貨幣的全球趨勢",
    description: "各國央行加速推進數位貨幣研發，這將重塑全球金融體系和支付方式。",
    category: "金融",
    gradientStart: "#f093fb",
    gradientEnd: "#f5576c"
  },
  {
    id: 4,
    title: "太空探索新紀元：火星殖民計劃進展",
    description: "NASA 和 SpaceX 等機構在火星探索方面取得重大進展，人類登陸火星的夢想即將實現。",
    category: "太空",
    gradientStart: "#4facfe",
    gradientEnd: "#00f2fe"
  },
  {
    id: 5,
    title: "醫療科技創新：精準醫療的未來發展",
    description: "基因編輯和精準醫療技術的發展，為治療罕見疾病和癌症帶來新的希望。",
    category: "醫療",
    gradientStart: "#fa709a",
    gradientEnd: "#fee140"
  }
];

function NewsCarousel() {
  const [currentSlide, setCurrentSlide] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % carouselNews.length);
    }, 5000);

    return () => clearInterval(timer);
  }, []);

  const goToSlide = (index) => {
    setCurrentSlide(index);
  };

  const goToPrevious = () => {
    setCurrentSlide((prev) => (prev - 1 + carouselNews.length) % carouselNews.length);
  };

  const goToNext = () => {
    setCurrentSlide((prev) => (prev + 1) % carouselNews.length);
  };

  return (
    <div>
      <SectionTitle>熱門新聞</SectionTitle>
      <CarouselContainer>
        {carouselNews.map((news, index) => (
          <CarouselSlide
            key={news.id}
            active={index === currentSlide}
            gradientStart={news.gradientStart}
            gradientEnd={news.gradientEnd}
          >
            <SlideContent>
              <SlideCategory>{news.category}</SlideCategory>
              <SlideTitle>{news.title}</SlideTitle>
              <SlideDescription>{news.description}</SlideDescription>
              <SlideButton to={`/news/${news.id}`}>
                閱讀全文 →
              </SlideButton>
            </SlideContent>
            <SlideOverlay />
          </CarouselSlide>
        ))}

        <CarouselControls>
          <ControlButton onClick={goToPrevious}>‹</ControlButton>
          <ControlButton onClick={goToNext}>›</ControlButton>
        </CarouselControls>

        <CarouselIndicators>
          {carouselNews.map((_, index) => (
            <Indicator
              key={index}
              active={index === currentSlide}
              onClick={() => goToSlide(index)}
            />
          ))}
        </CarouselIndicators>
      </CarouselContainer>
    </div>
  );
}

export default NewsCarousel; 