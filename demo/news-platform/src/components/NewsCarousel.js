import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import './../css/NewsCarousel.css';

// 模擬輪播新聞資料（原樣搬過來）
const carouselNews = [
  {
    id: 1,
    title: "AI 技術突破：量子計算與人工智慧的融合",
    description: "最新研究顯示，量子計算技術與人工智慧的結合將為科技發展帶來革命性突破，預計在未來五年內實現商業化應用。",
    category: "科技",
    gradientStart: "#667eea",
    gradientEnd: "#764ba2",
    imageUrl: "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=800&h=600&fit=crop"
  },
  {
    id: 2,
    title: "全球氣候變遷：各國積極應對的新政策",
    description: "面對日益嚴峻的氣候挑戰，各國政府紛紛推出新的環保政策，致力於實現碳中和目標。",
    category: "環境",
    gradientStart: "#11998e",
    gradientEnd: "#38ef7d",
    imageUrl: "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800&h=600&fit=crop"
  },
  {
    id: 3,
    title: "數位貨幣革命：央行數位貨幣的全球趨勢",
    description: "各國央行加速推進數位貨幣研發，這將重塑全球金融體系和支付方式。",
    category: "金融",
    gradientStart: "#f093fb",
    gradientEnd: "#f5576c",
    imageUrl: "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=800&h=600&fit=crop"
  },
  {
    id: 4,
    title: "太空探索新紀元：火星殖民計劃進展",
    description: "NASA 和 SpaceX 等機構在火星探索方面取得重大進展，人類登陸火星的夢想即將實現。",
    category: "太空",
    gradientStart: "#4facfe",
    gradientEnd: "#00f2fe",
    imageUrl: "https://images.unsplash.com/photo-1446776877081-d282a0f896e2?w=800&h=600&fit=crop"
  },
  {
    id: 5,
    title: "醫療科技創新：精準醫療的未來發展",
    description: "基因編輯和精準醫療技術的發展，為治療罕見疾病和癌症帶來新的希望。",
    category: "醫療",
    gradientStart: "#fa709a",
    gradientEnd: "#fee140",
    imageUrl: "https://images.unsplash.com/photo-1576091160399-112ba8d25d1f?w=800&h=600&fit=crop"
  }
];

function NewsCarousel() {
  const [currentSlide, setCurrentSlide] = useState(0);

  // 自動輪播
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % carouselNews.length);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  const goToSlide = useCallback((index) => {
    setCurrentSlide(index);
  }, []);

  const goToPrevious = useCallback(() => {
    setCurrentSlide((prev) => (prev - 1 + carouselNews.length) % carouselNews.length);
  }, []);

  const goToNext = useCallback(() => {
    setCurrentSlide((prev) => (prev + 1) % carouselNews.length);
  }, []);

  // 鍵盤快捷（← / →）
  const onKeyDown = (e) => {
    if (e.key === 'ArrowLeft') goToPrevious();
    if (e.key === 'ArrowRight') goToNext();
  };

  return (
    <div>
      <h2 className="carousel__sectionTitle">熱門新聞</h2>

      <section
        className="carousel"
        role="region"
        aria-roledescription="carousel"
        aria-label="熱門新聞輪播"
        onKeyDown={onKeyDown}
        tabIndex={0}
      >
        {carouselNews.map((news, index) => {
          const isActive = index === currentSlide;
          return (
            <div
              key={news.id}
              className={`carousel__slide ${isActive ? 'is-active' : ''}`}
              style={{
                '--gStart': news.gradientStart,
                '--gEnd': news.gradientEnd
              }}
              aria-hidden={!isActive}
            >
              <div className="carousel__content">
                <span className="carousel__category">{news.category}</span>
                <h2 className="carousel__title">{news.title}</h2>
                <p className="carousel__desc">{news.description}</p>
                <Link className="carousel__btn" to={`/news/${news.id}`}>
                  閱讀全文 →
                </Link>
              </div>

              {/* 右側背景圖，前面多加一層漸層遮罩 */}
              <div
                className="carousel__img"
                style={{
                  backgroundImage:
                    `linear-gradient(45deg, rgba(0,0,0,0) 0%, rgba(0,0,0,.4) 100%), url(${news.imageUrl})`
                }}
                aria-hidden="true"
              />
            </div>
          );
        })}

        <div className="carousel__controls" aria-hidden="false">
          <button
            className="carousel__controlBtn"
            onClick={goToPrevious}
            aria-label="上一張"
            type="button"
          >
            ‹
          </button>
          <button
            className="carousel__controlBtn"
            onClick={goToNext}
            aria-label="下一張"
            type="button"
          >
            ›
          </button>
        </div>

        <div className="carousel__indicators" role="tablist" aria-label="選擇投影片">
          {carouselNews.map((_, index) => {
            const active = index === currentSlide;
            return (
              <button
                key={index}
                className="carousel__dot"
                onClick={() => goToSlide(index)}
                aria-label={`前往第 ${index + 1} 張`}
                aria-current={active ? 'true' : 'false'}
                role="tab"
                type="button"
              />
            );
          })}
        </div>
      </section>
    </div>
  );
}

export default NewsCarousel;
