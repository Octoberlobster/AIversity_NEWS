import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './../css/NewsCarousel.css';

// 熱門新聞資料 - 簡化版本，只保留標題和圖片
const hotNews = [
  {
    id: 1,
    title: "AI 技術突破：量子計算與人工智慧的融合",
    imageUrl: "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=1200&h=600&fit=crop"
  },
  {
    id: 2,
    title: "全球氣候變遷：各國積極應對的新政策",
    imageUrl: "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1200&h=600&fit=crop"
  },
  {
    id: 3,
    title: "數位貨幣革命：央行數位貨幣的全球趨勢",
    imageUrl: "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=1200&h=600&fit=crop"
  },
  {
    id: 4,
    title: "太空探索新紀元：火星殖民計劃進展",
    imageUrl: "https://images.unsplash.com/photo-1446776877081-d282a0f896e2?w=1200&h=600&fit=crop"
  },
  {
    id: 5,
    title: "醫療科技創新：精準醫療的未來發展",
    imageUrl: "https://images.unsplash.com/photo-1576091160399-112ba8d25d1f?w=1200&h=600&fit=crop"
  }
];

function NewsCarousel() {
  const [currentIndex, setCurrentIndex] = useState(0);

  // 自動輪播 - 每5秒切換
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % hotNews.length);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  const goToPrevious = () => {
    setCurrentIndex((prev) => (prev - 1 + hotNews.length) % hotNews.length);
  };

  const goToNext = () => {
    setCurrentIndex((prev) => (prev + 1) % hotNews.length);
  };

  const goToSlide = (index) => {
    setCurrentIndex(index);
  };

  return (
    <div className="news-carousel">
      <div className="carousel-container">
        <div className="carousel-wrapper">
          {hotNews.map((news, index) => (
            <div
              key={news.id}
              className={`carousel-slide ${index === currentIndex ? 'active' : ''}`}
            >
              <div className="slide-image">
                <img src={news.imageUrl} alt={news.title} />
                <div className="slide-overlay">
                  <h3 className="slide-title">{news.title}</h3>
                  <Link to={`/news/${news.id}`} className="read-more-btn">
                    閱讀全文
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* 左右控制按鈕 */}
        <button className="carousel-btn prev" onClick={goToPrevious}>
          ‹
        </button>
        <button className="carousel-btn next" onClick={goToNext}>
          ›
        </button>

        {/* 底部指示點 */}
        <div className="carousel-indicators">
          {hotNews.map((_, index) => (
            <button
              key={index}
              className={`indicator ${index === currentIndex ? 'active' : ''}`}
              onClick={() => goToSlide(index)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export default NewsCarousel;
