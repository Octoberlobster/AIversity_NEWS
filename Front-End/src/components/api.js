// src/api.js
export const API_BASE =
  process.env.REACT_APP_API_BASE || 'http://localhost:5000';

export async function fetchJson(path, body) {
  //console.log('fetchJson 請求:', path, JSON.stringify(body, null, 2));
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  //console.log('fetchJson 回應狀態:', res.status, res.statusText);
  if (!res.ok) {
    const txt = await res.text();
    //console.error('fetchJson 錯誤回應:', txt);
    throw new Error(res.status + ' ' + txt);
  }
  const data = await res.json();
  //console.log('fetchJson 回應資料:', data);
  return data;
}

// 搜尋新聞功能 - 調用 Advanced_Search_Service API
export async function searchNews(query) {
  //console.log('searchNews called with query:', query);
  return await fetchJson('/api/Advanced_Search_Service/search', { query });
}

// 換專家功能 - 調用專家更換 API
export async function changeExperts(userId, roomId, storyId, language, currentExperts, expertsToRegenerate) {
  console.log('changeExperts 被呼叫，參數:', {
    userId,
    roomId,
    storyId,
    language,
    currentExperts,
    expertsToRegenerate
  });

  const requestBody = {
    user_id: userId,
    room_id: roomId,
    story_id: storyId,
    language: language,
    current_experts: currentExperts,
    experts_to_regenerate: expertsToRegenerate
  };

  console.log('準備送出的請求 body:', JSON.stringify(requestBody, null, 2));

  const result = await fetchJson('/api/experts/change', requestBody);
  
  console.log('changeExperts 收到結果:', result);
  
  // 處理後端回傳的資料結構 (可能有 success_response 包裝)
  if (result.success_response) {
    console.log('檢測到 success_response 包裝，解包中...');
    return result.success_response;
  }
  
  // 處理錯誤回應
  if (result.error_response) {
    console.error('檢測到 error_response:', result.error_response);
    throw new Error(result.error_response.error || '換專家失敗');
  }
  
  return result;
}

export async function changeExpertsTopic(userId, roomId, topicId, language, currentExperts, expertsToRegenerate) {
  console.log('changeExpertsTopic 被呼叫，參數:', {
    userId,
    roomId,
    topicId,
    language,
    currentExperts,
    expertsToRegenerate
  });

  const requestBody = {
    user_id: userId,
    room_id: roomId,
    topic_id: topicId,
    language: language,
    current_experts: currentExperts,
    experts_to_regenerate: expertsToRegenerate
  };

  console.log('準備送出的請求 body:', JSON.stringify(requestBody, null, 2));

  const result = await fetchJson('/api/experts/change_topic', requestBody);

  console.log('changeExpertsTopic 收到結果:', result);

  // 處理後端回傳的資料結構 (可能有 success_response 包裝)
  if (result.success_response) {
    console.log('檢測到 success_response 包裝，解包中...');
    return result.success_response;
  }

  // 處理錯誤回應
  if (result.error_response) {
    console.error('檢測到 error_response:', result.error_response);
    throw new Error(result.error_response.error || '換專家失敗');
  }

  return result;
}

// 提交專家分析反饋（有益/無益）
export async function submitExpertFeedback(analyzeId, feedbackType) {
  console.log('submitExpertFeedback 被呼叫，參數:', {
    analyzeId,
    feedbackType
  });

  const requestBody = {
    analyze_id: analyzeId,
    feedback_type: feedbackType  // "useful" or "useless"
  };

  console.log('準備送出的反饋請求 body:', JSON.stringify(requestBody, null, 2));

  const result = await fetchJson('/api/experts/feedback', requestBody);
  
  console.log('submitExpertFeedback 收到結果:', result);
  
  return result;
}

// 生成國家觀點分析
export async function generateCountryAnalysis(storyId, country) {
  console.log('generateCountryAnalysis 被呼叫，參數:', {
    storyId,
    country
  });

  const requestBody = {
    story_id: storyId,
    country: country  // "Taiwan"
  };

  console.log('準備送出的國家觀點請求 body:', JSON.stringify(requestBody, null, 2));

  const result = await fetchJson('/api/experts/country_analyze', requestBody);
  
  console.log('generateCountryAnalysis 收到結果:', result);
  
  return result;
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