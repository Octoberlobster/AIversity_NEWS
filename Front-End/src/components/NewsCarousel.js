import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './../css/NewsCarousel.css';
import { useSupabase } from './supabase';

function NewsCarousel() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [newsData, setNewsData] = useState([]);
  const [newsWithImages, setNewsWithImages] = useState([]);
  const supabaseClient = useSupabase();

  useEffect(() => {
    const fetchNewsData = async () => {
      const { data, error } = await supabaseClient
          .from('single_news')
          .select('story_id, news_title')
          .limit(5);
   
        if (error) {
          console.error(`Error fetching news data:`, error);
          setNewsData([]);
          return;
        }
        
        console.log('獲取到的新聞資料:', data);
        setNewsData(data || []);
    };

    fetchNewsData();
  }, [supabaseClient]);

  // 根據 newsData 抓取對應的圖片
  useEffect(() => {
    const fetchNewsImages = async () => {
      if (!newsData || newsData.length === 0) {
        return;
      }

      try {
        const newsWithImagePromises = newsData.map(async (news) => {
          // 參考 NewsDetail.js 的圖片抓取方式
          const { data: imageData, error } = await supabaseClient
            .from('generated_image')
            .select('*')
            .eq('story_id', news.story_id)
            .limit(1);

          if (error) {
            console.error(`Error fetching image for story_id ${news.story_id}:`, error);
            return {
              id: news.story_id,
              title: news.news_title,
              imageUrl: "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=1200&h=600&fit=crop" // 預設圖片
            };
          }

          let imageUrl = "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=1200&h=600&fit=crop"; // 預設圖片

          if (imageData && imageData.length > 0) {
            const imageItem = imageData[0];
            if (imageItem.image) {
              // 將純 base64 字串轉換為完整的 data URL
              imageUrl = `data:image/png;base64,${imageItem.image}`;
            }
          }

          return {
            id: news.story_id,
            title: news.news_title,
            imageUrl: imageUrl
          };
        });

        const results = await Promise.all(newsWithImagePromises);
        console.log('處理完成的新聞與圖片資料:', results);
        setNewsWithImages(results);
      } catch (error) {
        console.error('Error fetching news images:', error);
        // 如果出錯，使用沒有圖片的版本
        const fallbackData = newsData.map(news => ({
          id: news.story_id,
          title: news.news_title,
          imageUrl: "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=1200&h=600&fit=crop"
        }));
        setNewsWithImages(fallbackData);
      }
    };

    fetchNewsImages();
  }, [newsData, supabaseClient]);

  // 自動輪播 - 每5秒切換
  useEffect(() => {
    if (newsWithImages.length === 0) return;
    
    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % newsWithImages.length);
    }, 5000);
    return () => clearInterval(timer);
  }, [newsWithImages.length]);

  const goToPrevious = () => {
    setCurrentIndex((prev) => (prev - 1 + newsWithImages.length) % newsWithImages.length);
  };

  const goToNext = () => {
    setCurrentIndex((prev) => (prev + 1) % newsWithImages.length);
  };

  const goToSlide = (index) => {
    setCurrentIndex(index);
  };

  // 如果還沒載入完成，顯示載入中
  if (newsWithImages.length === 0) {
    return (
      <div className="news-carousel">
        <div className="carousel-container">
          <div className="loading">載入中...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="news-carousel">
      <div className="carousel-container">
        <div className="carousel-wrapper">
          {newsWithImages.map((news, index) => (
            <div
              key={news.id}
              className={`carousel-slide ${index === currentIndex ? 'active' : ''}`}
            >
              <div className="slide-image">
                {/* 圖片可點擊 */}
                <Link to={`/news/${news.id}`} className="slide-link">
                  <img src={news.imageUrl} alt={news.title} />
                </Link>
                {/* 標題和按鈕在覆蓋層 */}
                <div className="slide-overlay">
                  <Link to={`/news/${news.id}`} className="slide-title-link">
                    <h3 className="slide-title">{news.title}</h3>
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
          {newsWithImages.map((_, index) => (
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
