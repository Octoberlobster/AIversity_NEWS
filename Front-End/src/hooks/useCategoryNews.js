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
        .eq('country', dbCountry)
        .eq('category', categoryName)
        .limit(200);

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
 * 使用全域快取避免重複載入
 */

// 全域快取,在元件外部
const globalImageCache = {};
// 全域物件快取,保持物件參考穩定
let cachedImagesObject = {};

export function useBatchNewsImages(storyIds) {
  const supabase = useSupabase();
  const queryClient = useQueryClient();

  // 使用排序後的字串作為 key,避免陣列順序變化導致重複查詢
  const storyIdsKey = storyIds ? [...storyIds].sort().join(',') : '';

  return useQuery({
    queryKey: ['batch-news-images', storyIdsKey],
    queryFn: async () => {
      if (!storyIds || storyIds.length === 0) {
        // 空陣列時返回空物件但保持參考穩定
        if (Object.keys(cachedImagesObject).length === 0) {
          return cachedImagesObject;
        }
        return {};
      }

      // 先從全域快取中找已有的圖片
      const uncachedStoryIds = storyIds.filter(id => !globalImageCache[id]);
      
      if (uncachedStoryIds.length === 0) {
        console.log('[useBatchNewsImages] 所有圖片已在全域快取中,共', storyIds.length, '張');
        // 檢查是否需要更新物件
        const needsUpdate = storyIds.some(id => !cachedImagesObject[id]);
        if (!needsUpdate) {
          // 回傳相同的物件參考,避免觸發 re-render
          console.log('[useBatchNewsImages] 物件參考保持不變,避免 re-render');
          return cachedImagesObject;
        }
        // 需要更新時才建立新物件
        const result = {};
        storyIds.forEach(id => {
          if (globalImageCache[id]) {
            result[id] = globalImageCache[id];
          }
        });
        cachedImagesObject = result;
        return cachedImagesObject;
      }

      console.log('[useBatchNewsImages] 需要載入:', uncachedStoryIds.length, '張新圖片 (總共', storyIds.length, '張)');

      // 🔧 優化: 減少批次大小避免超時
      const BATCH_SIZE = 3; // 每次載入 3 張圖片
      
      // 從現有的快取物件開始
      const imagesMap = { ...cachedImagesObject };
      
      // 先把已快取的圖片加入結果
      storyIds.forEach(id => {
        if (globalImageCache[id] && !imagesMap[id]) {
          imagesMap[id] = globalImageCache[id];
        }
      });

      for (let i = 0; i < uncachedStoryIds.length; i += BATCH_SIZE) {
        const batch = uncachedStoryIds.slice(i, i + BATCH_SIZE);
        
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
                  const imageUrl = `data:image/png;base64,${cleanBase64}`;
                  imagesMap[item.story_id] = imageUrl;
                  globalImageCache[item.story_id] = imageUrl; // 存入全域快取
                } catch (e) {
                  console.error('[useBatchNewsImages] 圖片處理失敗:', item.story_id, e);
                }
              }
            });

            // 🚀 立即更新快取,讓 UI 即時顯示已載入的圖片
            cachedImagesObject = { ...imagesMap };
            queryClient.setQueryData(['batch-news-images', storyIdsKey], cachedImagesObject);
            console.log('[useBatchNewsImages] 批次完成,已顯示:', Object.keys(imagesMap).length, '/', storyIds.length, '張');
          }
        } catch (err) {
          console.error('[useBatchNewsImages] 批次異常:', err);
          continue; // 異常就跳過,繼續下一批
        }
        
        // 🔧 批次間添加小延遲,避免資料庫壓力過大
        if (i + BATCH_SIZE < uncachedStoryIds.length) {
          await new Promise(resolve => setTimeout(resolve, 100));
        }
      }

      console.log('[useBatchNewsImages] 圖片載入完成:', Object.keys(imagesMap).length, '/', storyIds.length, '張');
      cachedImagesObject = imagesMap;
      return cachedImagesObject;
    },
    enabled: !!storyIds && storyIds.length > 0 && !!supabase,
    staleTime: Infinity, // 圖片永不過期
    gcTime: Infinity, // 永久快取 (React Query v5 使用 gcTime 替代 cacheTime)
    retry: 1, // 只重試 1 次
    refetchOnMount: false, // 不在 mount 時重新載入
    refetchOnWindowFocus: false, // 不在視窗 focus 時重新載入
    refetchOnReconnect: false, // 不在網路重連時重新載入
    structuralSharing: false, // 停用 structural sharing,完全依賴物件參考穩定性
  });
}
