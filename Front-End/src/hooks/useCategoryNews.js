import { useQuery, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';
import { useSupabase } from '../components/supabase';

/**
 * 自定義 Hook: 拉取分類新聞 (支援無限載入)
 * 使用 React Query 管理快取和狀態
 */
export function useCategoryNews(country, categoryName, itemsPerPage = 18) {
  const supabase = useSupabase();

  return useInfiniteQuery({
    queryKey: ['category-news', country, categoryName, itemsPerPage],
    queryFn: async ({ pageParam = 0 }) => {
      console.log('[useCategoryNews] 載入頁面:', pageParam, '國家:', country, '分類:', categoryName);

      const offset = pageParam * itemsPerPage;

      // 對應資料庫的正確國家名稱
      const countryMap = {
        'Taiwan': 'Taiwan',
        'Japan': 'Japan',
        'Indonesia': 'Indonesia',
        'USA': 'United States of America',
        'United States of America': 'United States of America',
      };
      const dbCountry = countryMap[country] || country;

      // 1. 從 stories 表獲取 story_id (大範圍查詢)
      let storiesQuery = supabase
        .from('stories')
        .select('story_id')
        .eq('country', dbCountry);

      if (categoryName) {
        storiesQuery = storiesQuery.eq('category', categoryName);
      }

      const { data: storiesData, error: storiesError } = await storiesQuery;
      if (storiesError) throw storiesError;
      if (!storiesData || storiesData.length === 0) {
        return { news: [], nextPage: null };
      }

      const storyIds = storiesData.map(story => story.story_id);
      console.log(`[useCategoryNews] 找到 ${storyIds.length} 個 story_ids`);

      // 2. 查詢 single_news 並按時間排序和分頁
      const { data: newsData, error: newsError } = await supabase
        .from('single_news')
        .select('story_id, news_title, ultra_short, generated_date, category')
        .in('story_id', storyIds)
        .order('generated_date', { ascending: false })
        .range(offset, offset + itemsPerPage - 1);
      
      if (newsError) throw newsError;
      
      const allNews = newsData || [];

      // 3. 轉換格式 (不包含圖片)
      const basicNews = allNews.map(news => ({
        story_id: news.story_id,
        title: news.news_title,
        shortSummary: news.ultra_short,
        date: news.generated_date,
        category: news.category,
        needsImage: true,
      }));

      console.log('[useCategoryNews] 頁面載入完成:', basicNews.length, '筆');

      return {
        news: basicNews,
        nextPage: basicNews.length === itemsPerPage ? pageParam + 1 : null,
      };
    },
    getNextPageParam: (lastPage) => lastPage.nextPage,
    enabled: !!country && !!supabase,
    staleTime: 10 * 60 * 1000, // 10分鐘
    cacheTime: 30 * 60 * 1000, // 30分鐘
  });
}

/**
 * 自定義 Hook: 批量拉取新聞圖片
 * 🚀 即時更新模式: 每批載入完立即顯示,不等所有圖片載完
 */
export function useBatchNewsImages(storyIds) {
  const supabase = useSupabase();
  const queryClient = useQueryClient();

  return useQuery({
    queryKey: ['batch-news-images', storyIds],
    queryFn: async () => {
      if (!storyIds || storyIds.length === 0) return {};

      console.log('[useBatchNewsImages] 開始載入圖片:', storyIds.length, '張');

      // 🔧 優化: 減少批次大小避免超時
      const BATCH_SIZE = 3; // 每次載入 3 張圖片
      const imagesMap = {};

      for (let i = 0; i < storyIds.length; i += BATCH_SIZE) {
        const batch = storyIds.slice(i, i + BATCH_SIZE);
        
        try {
          const { data, error } = await supabase
            .from('generated_image')
            .select('story_id, image')
            .in('story_id', batch);

          if (error) {
            console.error('[useBatchNewsImages] 批次載入失敗:', error);
            continue; // 失敗就跳過這批,繼續下一批
          }

          if (data) {
            data.forEach(item => {
              if (item.image) {
                try {
                  const cleanBase64 = item.image.replace(/\s/g, '');
                  imagesMap[item.story_id] = `data:image/png;base64,${cleanBase64}`;
                } catch (e) {
                  console.error('[useBatchNewsImages] 圖片處理失敗:', item.story_id, e);
                }
              }
            });

            // 🚀 立即更新快取,讓 UI 即時顯示已載入的圖片
            queryClient.setQueryData(['batch-news-images', storyIds], { ...imagesMap });
            console.log('[useBatchNewsImages] 批次完成,已顯示:', Object.keys(imagesMap).length, '張');
          }
        } catch (err) {
          console.error('[useBatchNewsImages] 批次異常:', err);
          continue; // 異常就跳過,繼續下一批
        }
        
        // 🔧 批次間添加小延遲,避免資料庫壓力過大
        if (i + BATCH_SIZE < storyIds.length) {
          await new Promise(resolve => setTimeout(resolve, 100));
        }
      }

      console.log('[useBatchNewsImages] 圖片載入完成:', Object.keys(imagesMap).length, '/', storyIds.length, '張');
      return imagesMap;
    },
    enabled: !!storyIds && storyIds.length > 0 && !!supabase,
    staleTime: 30 * 60 * 1000, // 圖片快取 30 分鐘
    cacheTime: 2 * 60 * 60 * 1000, // 快取 2 小時
    retry: 1, // 只重試 1 次
  });
}
