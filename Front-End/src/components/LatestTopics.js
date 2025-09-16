import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useSupabase } from './supabase';
import '../css/LatestTopics.css';

function LatestTopics() {
  const [currentTopicIndex, setCurrentTopicIndex] = useState(0);
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const supabase = useSupabase();

  // 獲取最新專題數據
  useEffect(() => {
    const fetchLatestTopics = async () => {
      try {
        // 獲取專題基本資訊
        const { data: topicsData, error: topicsError } = await supabase
          .from('topic')
          .select('topic_id, topic_title, topic_short, generated_date')
          .not('topic_title', 'is', null)
          .neq('topic_title', '')
          .not('topic_short', 'is', null)
          .neq('topic_short', '')
          .not('generated_date', 'is', null)
          .order('generated_date', { ascending: false })
          .limit(10); // 先獲取10個，再過濾到5個有效專題

        if (topicsError) throw topicsError;

        if (!topicsData || topicsData.length === 0) {
          setError('沒有找到專題資料');
          return;
        }

        // 為每個專題獲取相關新聞和分支
        const topicsWithData = [];
        
        // 批量獲取所有專題的新聞映射
        const topicIds = topicsData.map(topic => topic.topic_id);
        const { data: allNewsMapData, error: allNewsMapError } = await supabase
          .from('topic_news_map')
          .select('topic_id, story_id')
          .in('topic_id', topicIds);

        if (allNewsMapError) {
          console.error('批量獲取專題新聞映射失敗:', allNewsMapError);
          setError('載入專題資料失敗');
          return;
        }

        // 組織新聞映射數據
        const newsMapByTopic = {};
        allNewsMapData.forEach(item => {
          if (!newsMapByTopic[item.topic_id]) {
            newsMapByTopic[item.topic_id] = [];
          }
          newsMapByTopic[item.topic_id].push(item.story_id);
        });

        // 收集所有需要圖片的 story_id
        const storyIdsForImages = [];
        const topicToStoryMap = {};
        
        for (const topic of topicsData) {
          const storyIds = newsMapByTopic[topic.topic_id];
          if (!storyIds || storyIds.length === 0) {
            console.log(`專題 ${topic.topic_title} 沒有相關新聞，跳過`);
            continue;
          }
          
          // 固定選擇第一個 story_id，避免圖片隨機變化
          const firstStoryId = storyIds[0];
          storyIdsForImages.push(firstStoryId);
          topicToStoryMap[topic.topic_id] = firstStoryId;
        }

        // 批量獲取所有圖片
        const { data: allImagesData, error: allImagesError } = await supabase
          .from('generated_image')
          .select('story_id, image, description')
          .in('story_id', storyIdsForImages);

        // 建立圖片映射表
        const imageMap = {};
        if (!allImagesError && allImagesData) {
          allImagesData.forEach(imageItem => {
            if (imageItem.image) {
              // 清理 base64 字串，移除可能的換行符和空白字符
              const cleanBase64 = imageItem.image.replace(/\s/g, '');
              // 將純 base64 字串轉換為完整的 data URL
              const imageUrl = `data:image/png;base64,${cleanBase64}`;
              
              imageMap[imageItem.story_id] = {
                imageUrl: imageUrl,
                description: imageItem.description || ''
              };
            }
          });
        }
        
        for (const topic of topicsData) {
          const storyIds = newsMapByTopic[topic.topic_id];
          if (!storyIds || storyIds.length === 0) continue;
          
          const firstStoryId = topicToStoryMap[topic.topic_id];
          const representativeImage = imageMap[firstStoryId] || null;

          // 獲取該專題的分支
          const { data: branchesData, error: branchesError } = await supabase
            .from('topic_branch')
            .select('topic_branch_id, topic_branch_title')
            .eq('topic_id', topic.topic_id)
            .not('topic_branch_title', 'is', null)
            .neq('topic_branch_title', '')
            .limit(5);

          if (branchesError) {
            console.error(`獲取專題 ${topic.topic_id} 分支失敗:`, branchesError);
          }

          // 處理分支數據 - 過濾掉空資料
          const branches = branchesData 
            ? branchesData.filter(branch => 
                branch.topic_branch_title && 
                branch.topic_branch_title.trim() !== ''
              ).map(branch => ({
                id: branch.topic_branch_id,
                title: branch.topic_branch_title
              }))
            : [];

          // 添加專題到結果中
          topicsWithData.push({
            ...topic,
            newsCount: storyIds.length, // 使用 storyIds 的長度
            branches: branches.slice(0, 4), // 最多顯示4個分支
            representativeImage: representativeImage
          });

          // 如果已經有5個有效專題，就停止
          if (topicsWithData.length >= 5) {
            break;
          }
        }

        setTopics(topicsWithData);
        setLoading(false);
      } catch (err) {
        console.error('獲取專題資料失敗:', err);
        setError('載入專題資料時發生錯誤');
        setLoading(false);
      }
    };

    fetchLatestTopics();
  }, [supabase]);

  // 自動輪播
  useEffect(() => {
    if (topics.length <= 1) return;

    const interval = setInterval(() => {
      setCurrentTopicIndex((prevIndex) => 
        (prevIndex + 1) % topics.length
      );
    }, 10000); // 每10秒切換一次

    return () => clearInterval(interval);
  }, [topics.length]);

  // 手動切換到下一個專題
  const nextTopic = () => {
    setCurrentTopicIndex((prevIndex) => 
      (prevIndex + 1) % topics.length
    );
  };

  // 手動切換到上一個專題
  const prevTopic = () => {
    setCurrentTopicIndex((prevIndex) => 
      prevIndex === 0 ? topics.length - 1 : prevIndex - 1
    );
  };

  // 手動切換到指定專題
  const goToTopic = (index) => {
    setCurrentTopicIndex(index);
  };

  if (loading) {
    return (
      <div className="latest-topics">
        <div className="latest-topics-loading">載入中...</div>
      </div>
    );
  }

  if (error || topics.length === 0) {
    return null; // 如果沒有數據就不顯示整個組件
  }

  const currentTopic = topics[currentTopicIndex];

  return (
    <div className="latest-topics">
      {/* 標題區域 - 仿照熱門新聞的樣式 */}
      <div className="latest-topics-title-section">
        <div className="latest-topics-title-content">
          <span className="star-icon">⭐</span>
          最新專題
        </div>
      </div>

      {/* 主要內容區域 */}
      <div className="latest-topics-main">
        {/* 左側：專題跑馬燈 - 仿照現有跑馬燈樣式 */}
        <div className="topic-carousel">
          <div className="carousel-container">
            <div className="carousel-main">
              <div className="carousel-wrapper">
                {topics.map((topic, index) => (
                  <div 
                    key={topic.topic_id}
                    className={`carousel-slide ${index === currentTopicIndex ? 'active' : ''}`}
                  >
                    {topic.representativeImage && (
                      <div className="slide-image">
                        <img 
                          src={topic.representativeImage.imageUrl || 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=1200&h=600&fit=crop'} 
                          alt={topic.representativeImage.description || topic.topic_title}
                          onError={(e) => {
                            e.target.src = 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=1200&h=600&fit=crop';
                          }}
                        />
                      </div>
                    )}
                    
                    <div className="slide-content">
                      <Link to={`/special-report/${topic.topic_id}`} className="slide-title-link">
                        <h2 className="slide-title">{topic.topic_title}</h2>
                      </Link>
                      <p className="slide-summary">
                        {topic.topic_short 
                          ? (topic.topic_short.length > 120 
                              ? topic.topic_short.substring(0, 120) + '...' 
                              : topic.topic_short)
                          : '探索這個重要專題的深度報導...'
                        }
                      </p>
                      <div className="slide-meta">
                        <span className="slide-date">
                          {new Date(topic.generated_date).toLocaleDateString('zh-TW')}
                        </span>
                        <span className="slide-news-count">
                          {topic.newsCount} 篇相關新聞
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* 控制按鈕 */}
              {topics.length > 1 && (
                <>
                  <button className="carousel-btn carousel-btn-prev" onClick={prevTopic}>
                    ‹
                  </button>
                  <button className="carousel-btn carousel-btn-next" onClick={nextTopic}>
                    ›
                  </button>
                </>
              )}

              {/* 指示器 */}
              {topics.length > 1 && (
                <div className="carousel-indicators">
                  {topics.map((_, index) => (
                    <button
                      key={index}
                      className={`indicator ${index === currentTopicIndex ? 'active' : ''}`}
                      onClick={() => goToTopic(index)}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 右側：專題分支 - 仿照側欄卡片樣式 */}
        <div className="topic-sidebar">
          <div className="sidebar-card">
            <h3 className="sidebar-title">專題分支</h3>
            <div className="branches-list">
              {currentTopic.branches.length > 0 ? (
                currentTopic.branches.map((branch, index) => (
                  <Link
                    key={branch.id}
                    to={`/special-report/${currentTopic.topic_id}?branch=${encodeURIComponent(branch.id)}`}
                    className="branch-item"
                  >
                    <span className="branch-icon">📰</span>
                    <span className="branch-name">{branch.title}</span>
                    <span className="branch-arrow">→</span>
                  </Link>
                ))
              ) : (
                <div className="no-branches">暫無分支專題</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LatestTopics;