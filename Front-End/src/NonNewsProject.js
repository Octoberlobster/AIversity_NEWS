import React, { useState, useEffect } from 'react';
import { useSupabase } from './supabase'; // 引入您的 useSupabase hook

function NonNewsProject() {
  const [groupedNews, setGroupedNews] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const supabase = useSupabase();

  // 新增狀態：用於追蹤當前展開的媒體名稱
  // null 代表所有項目都是收合的
  const [expandedMedia, setExpandedMedia] = useState(null);

  useEffect(() => {
    const fetchAndGroupNews = async () => {
      if (!supabase) return;
      try {
        setLoading(true);
        setError(null);

        // 步驟 1: 從 event_original_map 獲取所有已存在的 sourcecle_id
        const { data: mappedIdsData, error: mappedIdsError } = await supabase
          .from('event_original_map')
          .select('sourcecle_id');
        if (mappedIdsError) throw mappedIdsError;
        
        const idsToExclude = mappedIdsData
          .map(item => item.sourcecle_id)
          .filter(id => id !== null && id !== undefined);

        // 步驟 2: 從 cleaned_news 抓取資料
        const { data: newsData, error: newsError } = await supabase
          .from('cleaned_news')
          .select('sourcecle_id, title, url, sourcecle_media')
          .not('sourcecle_id', 'in', `(${idsToExclude.join(',')})`);
        if (newsError) throw newsError;

        // 步驟 3: 對資料按 media 進行分組
        const grouped = (newsData || []).reduce((acc, newsItem) => {
          const mediaName = newsItem.sourcecle_media || '未知媒體';
          if (!acc[mediaName]) {
            acc[mediaName] = [];
          }
          acc[mediaName].push(newsItem);
          return acc;
        }, {});

        setGroupedNews(grouped);
        console.log("已載入並按媒體分類未映射的新聞");

      } catch (err) {
        console.error('抓取或分類新聞時發生錯誤:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchAndGroupNews();
  }, [supabase]);

  // 新增點擊處理函式
  const handleMediaClick = (mediaName) => {
    // 如果點擊的媒體已經是展開狀態，則將其設為 null (收合)
    // 否則，將其設為新的展開目標
    setExpandedMedia(expandedMedia === mediaName ? null : mediaName);
  };

  if (loading) {
    return <div style={{ padding: '20px' }}>讀取中...</div>;
  }

  if (error) {
    return <div style={{ padding: '20px', color: 'red' }}>發生錯誤: {error}</div>;
  }

  return (
    <div style={{ padding: '20px' }}>
      <h2>非新聞專題內容 (未分類事件新聞 - 按媒體分類)</h2>
      
      {Object.keys(groupedNews).length > 0 ? (
        Object.keys(groupedNews).map(mediaName => (
          <div key={mediaName} style={{ marginBottom: '10px', borderBottom: '1px solid #eee' }}>
            {/* 將媒體標題變成可點擊的按鈕 */}
            <div 
              onClick={() => handleMediaClick(mediaName)}
              style={{
                cursor: 'pointer',
                padding: '10px 5px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontWeight: 'bold',
                color: expandedMedia === mediaName ? '#7DD1D1' : '#333' // 展開時變色
              }}
            >
              <span>{mediaName}</span>
              {/* 顯示 + 或 - 來表示狀態 */}
              <span style={{ fontSize: '20px' }}>{expandedMedia === mediaName ? '−' : '+'}</span>
            </div>
            
            {/* 條件渲染：只有當 expandedMedia 與當前媒體名稱相符時，才顯示新聞列表 */}
            {expandedMedia === mediaName && (
              <ul style={{ padding: '10px 20px', listStyleType: 'disc' }}>
                {groupedNews[mediaName].map(newsItem => (
                  <li key={newsItem.sourcecle_id} style={{ marginBottom: '10px' }}>
                    <strong>{newsItem.title}</strong>
                    <br />
                    <a href={newsItem.url} target="_blank" rel="noopener noreferrer" style={{ color: '#555', wordBreak: 'break-all' }}>
                      {newsItem.url}
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))
      ) : (
        <p>目前沒有尚未被映射的新聞。</p>
      )}
    </div>
  );
}

export default NonNewsProject;
