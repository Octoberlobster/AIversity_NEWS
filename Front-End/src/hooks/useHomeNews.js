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
        // 國家模式
        const { data: countryStories, error: storiesError } = await supabase
          .from('stories')
          .select('story_id')
          .or(`country.eq.${country},country.eq.${country.toLowerCase()}`)
          .order('story_id', { ascending: false })
          .range(offset, offset + itemsPerPage * 3 - 1);

        if (storiesError) {
          console.error('[useHomeNews] stories 查詢錯誤:', storiesError);
          throw storiesError;
        }
        
        console.log('[useHomeNews] stories 查詢結果:', countryStories?.length || 0, '筆');
        
        if (!countryStories || countryStories.length === 0) return { news: [], nextPage: null };

        const countryStoryIds = countryStories.map(s => s.story_id);
        
        console.log('[useHomeNews] story_ids:', countryStoryIds.slice(0, 5), '...');

        const multiLangFields = getMultiLanguageSelect(["news_title", "ultra_short"]);
        const selectQuery = `story_id, generated_date, ${multiLangFields}`;
        
        console.log('[useHomeNews] select query:', selectQuery);

        const { data: newsData, error: newsError } = await supabase
          .from('single_news')
          .select(selectQuery)
          .in('story_id', countryStoryIds)
          .order('generated_date', { ascending: false })
          .limit(itemsPerPage * 1);

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

      // 檢查哪些 story 有對應的 generated_image，若無圖片則不顯示（needsImage: false）
      const storyIds = fetchedData.map(n => n.story_id).filter(Boolean);
      let imageIdSet = new Set();
      if (storyIds.length > 0) {
        try {
          const { data: imagesData, error: imagesError } = await supabase
            .from('generated_image')
            .select('story_id')
            .in('story_id', storyIds);

          if (imagesError) {
            console.warn('[useHomeNews] generated_image 查詢錯誤，將視為無圖片:', imagesError);
          } else if (imagesData && imagesData.length > 0) {
            imageIdSet = new Set(imagesData.map(i => i.story_id));
          }
        } catch (err) {
          console.warn('[useHomeNews] generated_image 查詢異常，將視為無圖片:', err);
        }
      }

      // 轉換格式 (包含 needsImage 判斷)
      const basicNews = fetchedData
        .map(news => ({
          story_id: news.story_id,
          title: news[getFieldName("news_title")] || news.news_title,
          shortSummary: news[getFieldName("ultra_short")] || news.ultra_short,
          date: news.generated_date,
          needsImage: imageIdSet.has(news.story_id),
        }))
        .filter(news => news.needsImage); // 只保留有圖片的新聞

      // 修改分頁邏輯：如果過濾後的新聞數量為 0，直接載入下一頁
      if (basicNews.length === 0 && fetchedData.length > 0) {
        return {
          news: [],
          nextPage: pageParam + 1, // 強制載入下一頁
        };
      }
      
      // 如果獲取的原始數據量等於查詢限制，表示可能還有更多數據
      const hasMore = fetchedData.length === (country && country !== 'all' 
        ? itemsPerPage 
        : itemsPerPage);

      return {
        news: basicNews,
        nextPage: hasMore ? pageParam + 1 : null,
        // 添加最後一條新聞的日期，用於下一次查詢的參考
        lastDate: fetchedData[fetchedData.length - 1]?.generated_date,
      };
    },
    getNextPageParam: (lastPage) => {
      // 如果沒有更多數據，返回 null 停止分頁
      if (!lastPage.nextPage) return null;
      // 如果當前頁面沒有新聞但還有下一頁，直接返回下一頁參數
      if (lastPage.news.length === 0) return lastPage.nextPage;
      // 如果有新聞，返回下一頁參數
      return lastPage.nextPage;
    },
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
