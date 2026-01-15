import { useQuery, useInfiniteQuery } from '@tanstack/react-query';
import { useSupabase } from '../components/supabase';
import { useLanguageFields } from '../utils/useLanguageFields';

/**
 * 自定義 Hook: 拉取首頁新聞 (支援無限滾動)
 * 🔧 使用 cursor-based pagination 避免重複新聞
 */
export function useHomeNews(country = 'Taiwan', itemsPerPage = 18, enabled = true) {
  const supabase = useSupabase();
  const { getMultiLanguageSelect, getFieldName, getCurrentLanguage } = useLanguageFields();
  const currentLanguage = getCurrentLanguage();

  return useInfiniteQuery({
    queryKey: ['home-news', country, itemsPerPage, currentLanguage],
    queryFn: async ({ pageParam = { page: 0, cursor: 0 } }) => {
      const { page, cursor } = pageParam;
      console.log('[useHomeNews] 載入頁面:', page, 'cursor:', cursor, '國家:', country);

      // 🔧 為了確保過濾後仍有足夠的資料，多查詢一些 (2倍)
      const fetchMultiplier = 2;
      const fetchSize = itemsPerPage * fetchMultiplier;
      
      // 🔧 使用 cursor 作為實際的資料庫偏移量，避免重複
      const fetchOffset = cursor;

      let newsData = [];

      if (country && country !== 'all') {
        // 國家模式 - 使用巢狀查詢直接在 single_news 中過濾
        const multiLangFields = getMultiLanguageSelect(["news_title", "ultra_short"]);
        
        console.log('[useHomeNews] 使用巢狀查詢,國家:', country);

        // 一次查詢: 從 single_news 查詢,並透過 stories 表過濾國家
        // 只查詢有 generated_image 完整多語言 description 的新聞
        const { data, error: newsError } = await supabase
          .from('single_news')
          .select(`
            story_id,
            generated_date,
            ${multiLangFields},
            stories!inner(country),
            generated_image!inner(
              description_en_lang,
              description_id_lang,
              description_jp_lang
            )
          `)
          .or(`country.eq.${country},country.eq.${country.toLowerCase()}`, { foreignTable: 'stories' })
          .order('generated_date', { ascending: false })
          .range(fetchOffset, fetchOffset + fetchSize - 1);

        if (newsError) {
          console.error('[useHomeNews] 查詢錯誤:', newsError);
          throw newsError;
        }
        
        newsData = data || [];
        console.log('[useHomeNews] 查詢結果總數:', newsData.length, '筆 (過濾前)');
      } else {
        // 全部新聞模式 - 只查詢有 generated_image 完整多語言 description 的新聞
        const multiLangFields = getMultiLanguageSelect(["news_title", "ultra_short"]);
        
        const { data, error: newsError } = await supabase
          .from('single_news')
          .select(`
            story_id, 
            generated_date, 
            ${multiLangFields},
            generated_image!inner(
              description_en_lang,
              description_id_lang,
              description_jp_lang
            )
          `)
          .order('generated_date', { ascending: false })
          .range(fetchOffset, fetchOffset + fetchSize - 1);

        if (newsError) throw newsError;
        
        newsData = data || [];
      }

      // 過濾掉沒有完整多語言 description 的新聞
      const filteredNews = newsData.filter(news => {
        const img = news.generated_image;
        return img && 
               img.description_en_lang && 
               img.description_id_lang && 
               img.description_jp_lang;
      });
      
      // 🔧 只取需要的數量 (itemsPerPage)
      const pageNews = filteredNews.slice(0, itemsPerPage);
      
      console.log('[useHomeNews] 過濾後:', filteredNews.length, '筆，本頁顯示:', pageNews.length, '筆');

      // 轉換格式 (不包含圖片)
      const basicNews = pageNews.map(news => ({
        story_id: news.story_id,
        title: news[getFieldName("news_title")] || news.news_title,
        shortSummary: news[getFieldName("ultra_short")] || news.ultra_short,
        date: news.generated_date,
        needsImage: true,
      }));

      console.log('[useHomeNews] 頁面載入完成:', basicNews.length, '筆');

      // 🔧 計算下一頁的 cursor (實際消耗的資料庫記錄數)
      const nextCursor = cursor + newsData.length;
      
      // 🔧 判斷是否還有下一頁
      const hasMore = filteredNews.length > itemsPerPage || newsData.length === fetchSize;

      return {
        news: basicNews,
        nextPage: hasMore ? { page: page + 1, cursor: nextCursor } : null,
      };
    },
    getNextPageParam: (lastPage) => lastPage.nextPage,
    initialPageParam: { page: 0, cursor: 0 },
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
