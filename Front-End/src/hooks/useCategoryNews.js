import { useInfiniteQuery, useQueries } from '@tanstack/react-query';
import { useSupabase } from '../components/supabase';
import { useLanguageFields } from '../utils/useLanguageFields';
import { useMemo } from 'react';

/**
 * 自定義 Hook: 拉取分類新聞 (支援無限載入)
 * 使用 React Query 管理快取和狀態
 */
export function useCategoryNews(country, categoryName, itemsPerPage = 18) {
  const supabase = useSupabase();
  const { getMultiLanguageSelect, getFieldName, getCurrentLanguage } = useLanguageFields();
  const currentLanguage = getCurrentLanguage();

  return useInfiniteQuery({
    queryKey: ['category-news', country, categoryName, itemsPerPage, currentLanguage],
    queryFn: async ({ pageParam = { page: 0, cursor: 0 } }) => {
      const { page, cursor } = pageParam;
      console.log('[useCategoryNews] 載入頁面:', page, 'cursor:', cursor, '國家:', country, '分類:', categoryName, '語言:', currentLanguage);

      // 對應資料庫的正確國家名稱
      const countryMap = {
        'Taiwan': 'Taiwan',
        'Japan': 'Japan',
        'Indonesia': 'Indonesia',
        'USA': 'United States of America',
        'United States of America': 'United States of America',
      };
      const dbCountry = countryMap[country] || country;

      // 使用 join 直接從 single_news 查詢,並過濾國家和分類
      const newsMultiLangFields = ['news_title', 'ultra_short'];
      const newsSelectFields = getMultiLanguageSelect(newsMultiLangFields);

      // 🔧 為了確保過濾後仍有足夠的資料，多查詢一些 (2倍)
      const fetchMultiplier = 2;
      const fetchSize = itemsPerPage * fetchMultiplier;
      
      // 🔧 使用 cursor 作為實際的資料庫偏移量，避免重複
      const fetchOffset = cursor;

      const { data: newsData, error: newsError } = await supabase
        .from('single_news')
        .select(`
          story_id, 
          ${newsSelectFields}, 
          generated_date, 
          category,
          generated_image!inner(
            description_en_lang,
            description_id_lang,
            description_jp_lang
          ),
          stories!inner(
            country,
            category
          )
        `)
        .eq('stories.country', dbCountry)
        .eq('stories.category', categoryName)
        .order('generated_date', { ascending: false })
        .range(fetchOffset, fetchOffset + fetchSize - 1);
      
      if (newsError) throw newsError;
      
      if (!newsData || newsData.length === 0) {
        console.log(`[useCategoryNews] 沒有找到 ${dbCountry} - ${categoryName} 的新聞`);
        return { news: [], nextPage: null };
      }
      
      console.log(`[useCategoryNews] 查詢到 ${newsData.length} 筆新聞 (過濾前)`);

      
      // 過濾掉沒有完整多語言 description 的新聞
      const filteredNews = (newsData || []).filter(news => {
        const img = news.generated_image;
        return img && 
               img.description_en_lang && 
               img.description_id_lang && 
               img.description_jp_lang;
      });
      
      // 🔧 只取需要的數量 (itemsPerPage)
      const allNews = filteredNews.slice(0, itemsPerPage);

      // 3. 轉換格式 (不包含圖片)，支援多語言
      const basicNews = allNews.map(news => ({
        story_id: news.story_id,
        title: news[getFieldName('news_title')] || news.news_title,
        shortSummary: news[getFieldName('ultra_short')] || news.ultra_short,
        date: news.generated_date,
        category: news.category,
        needsImage: true,
      }));

      console.log('[useCategoryNews] 頁面載入完成:', basicNews.length, '筆 (過濾後)');

      // 🔧 計算下一頁的 cursor (實際消耗的資料庫記錄數)
      // 下一頁的 cursor = 當前 cursor + 這次查詢的原始資料數量
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
    enabled: !!country && !!supabase,
    staleTime: 10 * 60 * 1000, // 10分鐘
    cacheTime: 30 * 60 * 1000, // 30分鐘
  });
}

/**
 * 自定義 Hook: 批量拉取新聞圖片
 * 🚀 改良版: 使用分批查詢 (Chunked Queries) 避免重新載入
 * 將 ID 列表切分為固定大小的區塊,每個區塊獨立快取
 */

// 全域快取,在元件外部
const globalImageCache = {};

export function useBatchNewsImages(storyIds) {
  const supabase = useSupabase();

  // 將 storyIds 切分成固定大小的 chunks (例如每頁 18 筆)
  // 這樣當新的 ID 加入時,舊的 chunks 保持不變,不會觸發重新查詢
  const chunks = useMemo(() => {
    if (!storyIds || storyIds.length === 0) return [];
    
    const chunkSize = 18;
    const result = [];
    for (let i = 0; i < storyIds.length; i += chunkSize) {
      result.push(storyIds.slice(i, i + chunkSize));
    }
    return result;
  }, [storyIds]);

  const queries = useQueries({
    queries: chunks.map(chunk => {
      // 使用排序後的 ID 作為 key,確保順序不影響 key
      // 注意: 這裡假設 chunk 內容是穩定的 (因為是按順序切分)
      const sortedIds = [...chunk].sort();
      const queryKey = ['news-images-chunk', sortedIds.join(',')];

      return {
        queryKey,
        queryFn: async () => {
          // 1. 先檢查全域快取
          const missingIds = chunk.filter(id => !globalImageCache[id]);
          const result = {};

          // 填入已快取的圖片
          chunk.forEach(id => {
            if (globalImageCache[id]) {
              result[id] = globalImageCache[id];
            }
          });

          if (missingIds.length === 0) {
            return result;
          }

          console.log(`[useBatchNewsImages] 載入區塊圖片: ${missingIds.length} 張`);

          // 2. 載入缺少的圖片
          const { data, error } = await supabase
            .from('generated_image')
            .select('story_id, image')
            .in('story_id', missingIds);

          if (error) {
            console.error('[useBatchNewsImages] 載入失敗:', error);
            return result; // 失敗時回傳已有的
          }

          if (data) {
            data.forEach(item => {
              if (item.image) {
                try {
                  const cleanBase64 = item.image.replace(/\s/g, '');
                  const imageUrl = `data:image/png;base64,${cleanBase64}`;
                  result[item.story_id] = imageUrl;
                  globalImageCache[item.story_id] = imageUrl; // 更新全域快取
                } catch (e) {
                  console.error('[useBatchNewsImages] 圖片處理失敗:', item.story_id, e);
                }
              }
            });
          }
          
          return result;
        },
        staleTime: Infinity,
        gcTime: Infinity,
        refetchOnMount: false,
        refetchOnWindowFocus: false,
        refetchOnReconnect: false,
      };
    })
  });

  // 合併所有查詢結果
  const combinedData = useMemo(() => {
    return queries.reduce((acc, query) => {
      if (query.data) {
        Object.assign(acc, query.data);
      }
      return acc;
    }, {});
  }, [queries]);

  return { data: combinedData };
}
