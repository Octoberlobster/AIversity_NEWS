import { useQuery } from '@tanstack/react-query';
import { useSupabase } from '../components/supabase';

/**
 * 自定義 Hook: 拉取昨日焦點新聞
 * 使用 React Query 管理快取和狀態
 */
export function useYesterdayNews(country, yesterdayDate) {
  const supabase = useSupabase();

  return useQuery({
    // Query Key: 用於快取識別
    queryKey: ['yesterday-news', country, yesterdayDate],
    
    // Query Function: 實際的資料請求
    queryFn: async () => {
      console.log('[useYesterdayNews] 開始載入:', country, yesterdayDate);
      
      // 1. 拉取 top_ten_news
      const { data: topTenData, error: topTenError } = await supabase
        .from('top_ten_news')
        .select('*')
        .eq('country', country)
        .eq('date', yesterdayDate);

      if (topTenError) throw topTenError;
      if (!topTenData || topTenData.length === 0) return [];

      // 2. 解析 story_ids
      const allStoryIds = [];
      topTenData.forEach(item => {
        const parsedJson = typeof item.top_ten_news_id === 'string' 
          ? JSON.parse(item.top_ten_news_id) 
          : item.top_ten_news_id;
        allStoryIds.push(...parsedJson.top_ten_story_ids);
      });

      console.log('[useYesterdayNews] 找到', allStoryIds.length, '個 story_ids');

      // 3. 批量拉取新聞基本資料 (文字內容)
      const { data: newsData, error: newsError } = await supabase
        .from('single_news')
        .select('story_id, news_title, ultra_short')
        .in('story_id', allStoryIds);

      if (newsError) throw newsError;

      // 4. 先返回文字資料 (不包含圖片和相關來源)
      const basicNews = newsData.map(news => ({
        id: news.story_id,
        title: news.news_title,
        summary: news.ultra_short,
        date: yesterdayDate,
        // 標記為需要載入
        needsImage: true,
        needsSources: true,
      }));

      console.log('[useYesterdayNews] 基本資料載入完成:', basicNews.length, '筆');
      return basicNews;
    },
    
    // 啟用條件: 只有當 country 和 date 都存在時才執行
    enabled: !!country && !!yesterdayDate,
    
    // 快取設定
    staleTime: 10 * 60 * 1000, // 10分鐘內不重新請求
    cacheTime: 60 * 60 * 1000, // 快取1小時
  });
}

/**
 * 自定義 Hook: 拉取新聞圖片
 * 延遲載入,背景執行
 */
export function useNewsImages(storyIds) {
  const supabase = useSupabase();

  return useQuery({
    queryKey: ['news-images', storyIds],
    queryFn: async () => {
      if (!storyIds || storyIds.length === 0) return {};

      console.log('[useNewsImages] 開始載入圖片:', storyIds.length, '張');

      // 批量拉取圖片
      const { data, error } = await supabase
        .from('generated_image')
        .select('story_id, image')
        .in('story_id', storyIds);

      if (error) throw error;

      // 轉換為 Map 格式
      const imagesMap = {};
      data.forEach(item => {
        if (item.image) {
          const cleanBase64 = item.image.replace(/\s/g, '');
          imagesMap[item.story_id] = `data:image/png;base64,${cleanBase64}`;
        }
      });

      console.log('[useNewsImages] 圖片載入完成:', Object.keys(imagesMap).length, '張');
      return imagesMap;
    },
    enabled: !!storyIds && storyIds.length > 0,
    staleTime: 30 * 60 * 1000, // 圖片快取30分鐘
    cacheTime: 2 * 60 * 60 * 1000, // 快取2小時
  });
}

/**
 * 自定義 Hook: 拉取相關來源
 * 延遲載入,背景執行
 */
export function useRelatedSources(storyIds) {
  const supabase = useSupabase();

  return useQuery({
    queryKey: ['related-sources', storyIds],
    queryFn: async () => {
      if (!storyIds || storyIds.length === 0) return {};

      console.log('[useRelatedSources] 開始載入相關來源:', storyIds.length, '個新聞');

      // 批量拉取相關來源
      const { data, error } = await supabase
        .from('cleaned_news')
        .select('story_id, article_title, article_url, media')
        .in('story_id', storyIds);

      if (error) throw error;

      // 按 story_id 分組
      const sourcesMap = {};
      data.forEach(item => {
        if (!sourcesMap[item.story_id]) {
          sourcesMap[item.story_id] = [];
        }
        sourcesMap[item.story_id].push({
          id: sourcesMap[item.story_id].length + 1,
          media: item.media || new URL(item.article_url).hostname.replace('www.', ''),
          name: item.article_title,
          url: item.article_url,
        });
      });

      console.log('[useRelatedSources] 相關來源載入完成');
      return sourcesMap;
    },
    enabled: !!storyIds && storyIds.length > 0,
    staleTime: 10 * 60 * 1000, // 快取10分鐘
    cacheTime: 60 * 60 * 1000, // 快取1小時
  });
}
