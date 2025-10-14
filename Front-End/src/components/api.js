// src/api.js
export const API_BASE =
  process.env.REACT_APP_API_BASE || 'http://localhost:5000';

export async function fetchJson(path, body) {
  //console.log('fetchJson', path, JSON.stringify(body));
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(res.status + ' ' + txt);
  }
  return res.json();
}

// 搜尋新聞功能 - 調用 Advanced_Search_Service API
export async function searchNews(query) {
  //console.log('searchNews called with query:', query);
  return await fetchJson('/api/Advanced_Search_Service/search', { query });
}

/**
 * 從 Supabase 根據 story_ids 獲取新聞資料（輔助函數）
 */
export async function fetchNewsDataFromSupabase(supabaseClient, storyIds) {
  if (!supabaseClient || !storyIds || storyIds.length === 0) {
    return [];
  }

  try {
    // 類別映射
    const categoryMapping = {
      'Politics': '政治',
      'Taiwan News': '台灣',
      'International News': '國際',
      'Science & Technology': '科學與科技',
      'Lifestyle & Consumer': '生活',
      'Sports': '體育',
      'Entertainment': '娛樂',
      'Business & Finance': '商業財經',
      'Health & Wellness': '健康'
    };

    // 從 Supabase 查詢新聞資料
    const { data, error } = await supabaseClient
      .from('single_news')
      .select('*')
      .in('story_id', storyIds);

    if (error) {
      console.error('Supabase 查詢錯誤:', error);
      throw error;
    }

    if (!data || data.length === 0) {
      console.log('Supabase 沒有返回資料，story_ids:', storyIds);
      return [];
    }

    console.log('從 Supabase 查詢到的原始資料:', data);
    console.log('第一筆原始資料結構:', data[0]);

    // 轉換資料格式以符合 UnifiedNewsCard 需求
    const newsData = data.map((news, index) => {
      console.log(`轉換第 ${index + 1} 筆新聞:`, news);
      
      return {
        story_id: news.story_id,
        title: news.news_title || news.title,
        category: categoryMapping[news.category] || '未分類',
        author:'Gemini',
        date: news.generated_date || '未知日期',  // 使用 generated_date
        shortSummary: news.ultra_short,  // 使用 ultra_short
        sourceCount: news.total_articles,  // 使用 total_articles
        views: 0,  // 改為數字
        keywords: [], // 將在後續步驟中填充
        terms: [],    // 將在後續步驟中填充
        relatedNews: [] // 將在後續步驟中填充
      };
    });

    console.log(`轉換後的新聞資料:`, newsData);

    console.log(`成功獲取 ${newsData.length} 篇搜尋結果新聞`);
    return newsData;

  } catch (error) {
    console.error('從 Supabase 獲取新聞資料時發生錯誤:', error);
    throw error;
  }
}