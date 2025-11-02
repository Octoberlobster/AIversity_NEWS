import { useQuery, useInfiniteQuery } from '@tanstack/react-query';
import { useSupabase } from '../components/supabase';
import { useLanguageFields } from '../utils/useLanguageFields';

/**
 * 自定義 Hook: 拉取首頁新聞 (支援無限滾動)
 */
export function useHomeNews(country = 'Taiwan', itemsPerPage = 18, enabled = true) {
  const supabase = useSupabase();
  const { getMultiLanguageSelect, getFieldName } = useLanguageFields();

  return useInfiniteQuery({
    queryKey: ['home-news', country, itemsPerPage],
    queryFn: async ({ pageParam = 0 }) => {
      console.log('[useHomeNews] 載入頁面:', pageParam, '國家:', country);

      const offset = pageParam * itemsPerPage;

      let fetchedData;

      if (country && country !== 'all') {
        // 國家模式 - 直接在 single_news 中查詢,使用 join 來過濾國家
        const multiLangFields = getMultiLanguageSelect(["news_title", "ultra_short"]);
        const selectQuery = `story_id, generated_date, ${multiLangFields}`;
        
        console.log('[useHomeNews] select query:', selectQuery);

        // 方法1: 先獲取該國家的 story_id 範圍較小的批次
        const { data: countryStories, error: storiesError } = await supabase
          .from('stories')
          .select('story_id')
          .or(`country.eq.${country},country.eq.${country.toLowerCase()}`)
          .order('story_id', { ascending: false })
          .limit(500); // 限制數量避免太大

        if (storiesError) {
          console.error('[useHomeNews] stories 查詢錯誤:', storiesError);
          throw storiesError;
        }
        
        console.log('[useHomeNews] stories 查詢結果:', countryStories?.length || 0, '筆');
        
        if (!countryStories || countryStories.length === 0) return { news: [], nextPage: null };

        const countryStoryIds = countryStories.map(s => s.story_id);
        
        console.log('[useHomeNews] story_ids 範圍:', countryStoryIds.length, '筆');

        // 在 single_news 中按時間排序並分頁
        const { data: newsData, error: newsError } = await supabase
          .from('single_news')
          .select(selectQuery)
          .in('story_id', countryStoryIds)
          .order('generated_date', { ascending: false })
          .range(offset, offset + itemsPerPage - 1);

        if (newsError) {
          console.error('[useHomeNews] single_news 查詢錯誤:', newsError);
          throw newsError;
        }
        
        console.log('[useHomeNews] single_news 查詢結果:', newsData?.length || 0, '筆');
        
        fetchedData = newsData || [];
      } else {
        // 全部新聞模式
        const multiLangFields = getMultiLanguageSelect(["news_title", "ultra_short"]);
        const selectQuery = `story_id, generated_date, ${multiLangFields}`;
        
        const { data: newsData, error: newsError } = await supabase
          .from('single_news')
          .select(selectQuery)
          .order('generated_date', { ascending: false })
          .range(offset, offset + itemsPerPage - 1);

        if (newsError) throw newsError;
        fetchedData = newsData || [];
      }

      // 轉換格式 (不包含圖片)
      const basicNews = fetchedData.map(news => ({
        story_id: news.story_id,
        title: news[getFieldName("news_title")] || news.news_title,
        shortSummary: news[getFieldName("ultra_short")] || news.ultra_short,
        date: news.generated_date,
        needsImage: true,
      }));

      console.log('[useHomeNews] 頁面載入完成:', basicNews.length, '筆');

      return {
        news: basicNews,
        nextPage: basicNews.length === itemsPerPage ? pageParam + 1 : null,
      };
    },
    getNextPageParam: (lastPage) => lastPage.nextPage,
    enabled: enabled && !!supabase, // 加入 enabled 參數
    staleTime: 5 * 60 * 1000, // 5分鐘
    cacheTime: 30 * 60 * 1000, // 30分鐘
  });
}

/**
 * 自定義 Hook: 拉取單張新聞圖片 (用於逐張載入)
 */
export function useSingleNewsImage(storyId) {
  const supabase = useSupabase();

  return useQuery({
    queryKey: ['single-news-image', storyId],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('generated_image')
        .select('story_id, image')
        .eq('story_id', storyId)
        .single();

      if (error) throw error;
      if (!data || !data.image) return null;

      const cleanBase64 = data.image.replace(/\s/g, '');
      return `data:image/png;base64,${cleanBase64}`;
    },
    enabled: !!storyId && !!supabase,
    staleTime: 30 * 60 * 1000, // 30分鐘
    cacheTime: 2 * 60 * 60 * 1000, // 2小時
  });
}
