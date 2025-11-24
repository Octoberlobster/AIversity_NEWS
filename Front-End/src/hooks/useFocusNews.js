import { useQuery } from '@tanstack/react-query';
import { useSupabase } from '../components/supabase';
import { useLanguageFields } from '../utils/useLanguageFields';

/**
 * 自定義 Hook: 拉取焦點新聞 (從 top_ten_news 表)
 * @param {string} country - 國家名稱
 */
export function useFocusNews(country = 'taiwan') {
  const supabase = useSupabase();
  const { getFieldName, getCurrentLanguage } = useLanguageFields();
  const currentLanguage = getCurrentLanguage();

  // 國家名稱映射
  const countryMap = {
    'taiwan': 'Taiwan',
    'japan': 'Japan',
    'indonesia': 'Indonesia',
    'usa': 'United States of America'
  };

  const dbCountry = countryMap[country] || 'Taiwan';

  return useQuery({
    queryKey: ['focus-news', dbCountry, currentLanguage],
    queryFn: async () => {
      console.log('[useFocusNews] 開始載入焦點新聞:', dbCountry);

      // 1. 獲取今天的日期 (YYYY-MM-DD 格式)
      const today = new Date();
      const dateString = today.toISOString().split('T')[0];

      console.log('[useFocusNews] 查詢日期:', dateString);

      // 2. 查詢 top_ten_news 表
      const { data: topTenData, error: topTenError } = await supabase
        .from('top_ten_news')
        .select('top_ten_news_id')
        .eq('date', dateString)
        .eq('country', dbCountry);

      if (topTenError) {
        console.error('[useFocusNews] 查詢 top_ten_news 錯誤:', topTenError);
        throw topTenError;
      }

      if (!topTenData || topTenData.length === 0) {
        console.log('[useFocusNews] 沒有找到焦點新聞資料');
        return [];
      }

      // 3. 解析所有結果的 story_ids
      const allStoryIds = [];
      topTenData.forEach(item => {
        const parsedJson = typeof item.top_ten_news_id === 'string' 
          ? JSON.parse(item.top_ten_news_id) 
          : item.top_ten_news_id;
        if (parsedJson.top_ten_story_ids && Array.isArray(parsedJson.top_ten_story_ids)) {
          allStoryIds.push(...parsedJson.top_ten_story_ids);
        }
      });

      console.log('[useFocusNews] 找到', allStoryIds.length, '則焦點新聞');

      if (allStoryIds.length === 0) {
        return [];
      }

      // 4. 平行查詢新聞詳細資料與來源資料 (Parallel Fetching)
      // 使用 Promise.all 同時發出請求，減少等待時間
      const newsMultiLangFields = ['news_title', 'ultra_short'];
      const selectFields = newsMultiLangFields.map(field => 
        `${field}, ${field}_en_lang, ${field}_jp_lang, ${field}_id_lang`
      ).join(', ');

      const [newsResult, sourcesResult] = await Promise.all([
        // 查詢新聞內文
        supabase
          .from('single_news')
          .select(`
            story_id,
            ${selectFields},
            generated_date
          `)
          .in('story_id', allStoryIds)
          .order('generated_date', { ascending: false }),
        
        // 查詢新聞來源
        supabase
          .from('cleaned_news')
          .select('story_id, article_url, article_title, media')
          .in('story_id', allStoryIds)
      ]);

      const { data: newsData, error: newsError } = newsResult;
      const { data: sourcesData, error: sourcesError } = sourcesResult;

      if (newsError) {
        console.error('[useFocusNews] 查詢新聞詳細資料錯誤:', newsError);
        throw newsError;
      }

      if (sourcesError) {
        console.warn('[useFocusNews] 查詢來源資料錯誤:', sourcesError);
      }

      // 5. 處理來源資料映射
      const sourcesMap = {};
      (sourcesData || []).forEach(source => {
        if (!sourcesMap[source.story_id]) {
          sourcesMap[source.story_id] = [];
        }
        sourcesMap[source.story_id].push({
          url: source.article_url,
          title: source.article_title,
          media: source.media
        });
      });

      // 6. 組合最終資料 (已經按 generated_date 排序)
      const newsList = (newsData || []).map(news => ({
        story_id: news.story_id,
        title: news[getFieldName('news_title')] || news.news_title,
        summary: news[getFieldName('ultra_short')] || news.ultra_short,
        date: news.generated_date,
        // imageUrl 由組件層透過 useBatchNewsImages 載入
        sources: (sourcesMap[news.story_id] || []).slice(0, 4) // 最多5個來源
      }));

      // 最多返回10則新聞
      const limitedNewsList = newsList.slice(0, 10);

      console.log('[useFocusNews] 焦點新聞載入完成:', limitedNewsList.length, '則');
      
      return limitedNewsList;
    },
    enabled: !!supabase && !!dbCountry,
    staleTime: 10 * 60 * 1000, // 10分鐘
    cacheTime: 30 * 60 * 1000, // 30分鐘
  });
}
